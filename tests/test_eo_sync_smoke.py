"""eo-sync Batch 1 smoke：夹具适配器跑通 run / dry-run / 锁互斥 / 兼容映射。

隔离：EO_HOME 指向临时目录，绝不碰真实 ~/.eo；每个用例独立 temp git 仓库。
"""

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_DIR = REPO_ROOT / "cli"
EO_SYNC = CLI_DIR / "eo-sync"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))


def load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


eo_sync = load_module("eo_sync_mod", EO_SYNC)


CHANGE_TEMPLATE = """---
id: {cid}
seq: {seq}
title: {title}
summary: {summary}
status: {status}
tier: full
type: feature
base_commit: ~
created: 2026-07-24
issue: ~
pr: ~
---

# {title}

## 1. 意图

{summary}

## 2. 验收清单

- [ ] AC-1 演示
- [x] AC-2 已过

## 3. TODO

### Batch 1

- [x] TODO-1 做了
- [ ] TODO-2 没做
"""


def make_change(repo, cid, seq, status="confirmed", title="演示", summary="一句话意图"):
    p = repo / "eo-doc" / "changes" / f"{seq:02d}-{cid}" / "change.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        CHANGE_TEMPLATE.format(cid=cid, seq=seq, status=status, title=title, summary=summary),
        encoding="utf-8",
    )
    return p


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def init_repo(root, config):
    repo = root / "repo"
    repo.mkdir()
    (repo / ".eo-project.json").write_text(json.dumps(config), encoding="utf-8")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return repo


def run_sync(repo, eo_home, *args, extra_env=None):
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([str(CLI_DIR), str(FIXTURES_DIR), env.get("PATH", "")])
    env["EO_HOME"] = str(eo_home)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(EO_SYNC), *args],
        cwd=repo, env=env, capture_output=True, text=True,
    )


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.eo_home = self.root / "eo_home"
        cfg = {
            "project_name": "smoke",
            "mode": "local",
            "project_root": str(self.root / "pm"),
            "doc_root": "eo-doc",
            "sync": {"fixture": {"enabled": True}},
        }
        self.repo = init_repo(self.root, cfg)
        self.change = make_change(self.repo, "demo", 1)
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "change")

    def tearDown(self):
        self.tmp.cleanup()

    def test_adapters_lists_fixture(self):
        r = run_sync(self.repo, self.eo_home, "adapters")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("fixture", r.stdout)
        self.assertIn("启用", r.stdout)

    def test_dry_run_zero_write(self):
        r = run_sync(self.repo, self.eo_home, "run", "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("→ create", r.stdout)
        # dry-run 零写入：无簿记文件、frontmatter 未变
        self.assertFalse((self.eo_home / "sync-state").exists())
        self.assertIn("issue: ~", self.change.read_text(encoding="utf-8"))
        self.assertNotIn("fixture_ref", self.change.read_text(encoding="utf-8"))

    def test_run_then_skip(self):
        r1 = run_sync(self.repo, self.eo_home, "run")
        self.assertEqual(r1.returncode, 0, r1.stderr)
        # 簿记落盘
        state_files = list((self.eo_home / "sync-state").glob("*.json"))
        self.assertEqual(len(state_files), 1)
        # 身份字段回写（保序：替换已存在的 fixture_ref? 不在模板 → 追加）
        text = self.change.read_text(encoding="utf-8")
        self.assertIn("fixture_ref: ref-demo", text)
        # 第二次 run 全 skip
        r2 = run_sync(self.repo, self.eo_home, "run")
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertIn("→ skip", r2.stdout)
        self.assertNotIn("→ create", r2.stdout)

    def test_lock_contention_exit_2(self):
        # 手动持锁后再 run → 退出码 2
        import fcntl
        state_dir = self.eo_home / "sync-state"
        state_dir.mkdir(parents=True, exist_ok=True)
        # 先跑一次拿到确定的锁文件名
        run_sync(self.repo, self.eo_home, "run")
        lock_files = list(state_dir.glob("*.lock"))
        self.assertEqual(len(lock_files), 1)
        lp = lock_files[0]
        fd = os.open(str(lp), os.O_RDWR | os.O_CREAT)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            os.write(fd, json.dumps({"pid": os.getpid(), "at": 9999999999}).encode())
            r = run_sync(self.repo, self.eo_home, "run")
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("持锁", r.stderr)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    def test_compat_mapping_board_github(self):
        # 兼容映射：无 sync 段时由存量 board/github 派生启用集
        cfg = {"board": {"enabled": True, "stub_dir": "cards"},
               "github": {"issue": True, "pr": "auto"}}
        enabled = eo_sync.resolve_enabled(cfg)
        self.assertEqual(set(enabled), {"obsidian", "github"})
        self.assertEqual(enabled["obsidian"]["stub_dir"], "cards")
        self.assertEqual(enabled["github"], {"issue": True, "pr": "auto"})
        # sync 段存在则完全以其为准，不看 board/github
        cfg2 = {"board": {"enabled": True}, "sync": {"fixture": {"enabled": True}}}
        self.assertEqual(set(eo_sync.resolve_enabled(cfg2)), {"fixture"})
        # 全空 → 无启用目标
        self.assertEqual(eo_sync.resolve_enabled({}), {})


if __name__ == "__main__":
    unittest.main()
