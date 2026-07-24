"""eo-sync 完整测试矩阵（复用 Batch 1 夹具 tests/fixtures/eo-sync-fixture）。

覆盖：协议往返、发现与启用制、兼容映射、dry-run 零写入、双进程锁竞态、身份回写校验
（冲突/未知字段/非空不覆盖/保留键/非法键名）、保序插入、同状态分叉 fail-closed、部分失败总退出码、
簿记幂等与陈锁清理。

隔离：EO_HOME 一律指向临时目录，绝不触碰真实 ~/.eo；每个用例独立 temp git 仓库。
"""

import fcntl
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_DIR = REPO_ROOT / "cli"
EO_SYNC = CLI_DIR / "eo-sync"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))

from eo_lib import (
    resolve_writeback_path,
    status_rank,
    upsert_frontmatter_fields,
)


def load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


eo_sync = load_module("eo_sync_matrix_mod", EO_SYNC)


CHANGE_TMPL = """---
id: {cid}
seq: {seq}
title: {title}
summary: {summary}
status: {status}
tier: full
type: feature
base_commit: ~
created: 2026-07-24
issue: {issue}
pr: ~
---

# {title}

## 2. 验收清单
- [ ] AC-1 一
- [x] AC-2 二

## 3. TODO
### Batch 1
- [x] TODO-1 甲
- [ ] TODO-2 乙
"""


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def make_change(repo, cid, seq, status="confirmed", issue="~", title="标题", summary="意图"):
    p = repo / "eo-doc" / "changes" / f"{seq:02d}-{cid}" / "change.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(CHANGE_TMPL.format(cid=cid, seq=seq, status=status, issue=issue, title=title, summary=summary), encoding="utf-8")
    return p


def init_repo(root, config, changes=None):
    repo = root / "repo"
    repo.mkdir()
    (repo / ".eo-project.json").write_text(json.dumps(config), encoding="utf-8")
    for c in changes or []:
        make_change(repo, **c)
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return repo


def run_sync(repo, eo_home, *args, extra_env=None, on_path=(CLI_DIR, FIXTURES_DIR)):
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([str(p) for p in on_path] + [env.get("PATH", "")])
    env["EO_HOME"] = str(eo_home)
    env["EO_SYNC_TODAY"] = "2026-07-25"
    if extra_env:
        env.update(extra_env)
    return subprocess.run([sys.executable, str(EO_SYNC), *args], cwd=repo, env=env, capture_output=True, text=True)


def invoke_fixture(verb, request, extra_env=None):
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(FIXTURES_DIR / "eo-sync-fixture"), verb],
        input=json.dumps(request), capture_output=True, text=True, env=env,
    )


class ProtocolTests(unittest.TestCase):
    def test_capabilities_roundtrip(self):
        r = invoke_fixture("capabilities", {"protocol_version": 1, "verb": "capabilities"})
        self.assertEqual(r.returncode, 0, r.stderr)
        resp = json.loads(r.stdout)
        self.assertEqual(resp["protocol_version"], 1)
        self.assertEqual(resp["entities"], ["change"])
        self.assertEqual(resp["identity_fields"], ["fixture_ref"])

    def test_plan_apply_roundtrip(self):
        changes = [{"id": "c1", "status": "confirmed"}]
        plan_req = {"protocol_version": 1, "verb": "plan", "changes": changes, "bookkeeping": {}, "params": {}}
        plan = json.loads(invoke_fixture("plan", plan_req).stdout)
        self.assertEqual(plan["actions"][0]["op"], "create")
        apply_req = {"protocol_version": 1, "verb": "apply", "actions": plan["actions"], "bookkeeping": {}, "params": {}}
        result = json.loads(invoke_fixture("apply", apply_req).stdout)
        self.assertIn("c1", result["writeback"])
        self.assertIn("c1", result["bookkeeping"])


class EnablementCompatTests(unittest.TestCase):
    def test_compat_mapping(self):
        self.assertEqual(eo_sync.resolve_enabled({}), {})
        e = eo_sync.resolve_enabled({"board": {"enabled": True, "stub_dir": "b"}, "github": {"issue": True, "pr": "auto"}})
        self.assertEqual(set(e), {"obsidian", "github"})
        self.assertEqual(e["obsidian"]["stub_dir"], "b")
        # pr != never 也启用 github（即便 issue=false）
        self.assertIn("github", eo_sync.resolve_enabled({"github": {"issue": False, "pr": "always"}}))
        # sync 段存在则完全以其为准
        self.assertEqual(set(eo_sync.resolve_enabled({"board": {"enabled": True}, "sync": {"fixture": {"enabled": True}}})), {"fixture"})
        # enabled=false 不算
        self.assertEqual(eo_sync.resolve_enabled({"sync": {"x": {"enabled": False}}}), {})

    def test_discovery_lists_and_enable_gate(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                    "doc_root": "eo-doc", "sync": {"fixture": {"enabled": True}}},
                             changes=[{"cid": "c1", "seq": 1}])
            r = run_sync(repo, root / "home", "adapters")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("fixture", r.stdout)
            self.assertIn("启用", r.stdout)

    def test_no_targets_exit_zero(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                    "doc_root": "eo-doc"}, changes=[{"cid": "c1", "seq": 1}])
            r = run_sync(repo, root / "home", "run")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("未启用任何同步目标", r.stdout)


class DryRunLockTests(unittest.TestCase):
    def _repo(self, root):
        return init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                "doc_root": "eo-doc", "sync": {"fixture": {"enabled": True}}},
                         changes=[{"cid": "c1", "seq": 1}])

    def test_dry_run_zero_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = self._repo(root)
            change = repo / "eo-doc" / "changes" / "01-c1" / "change.md"
            before = change.read_text(encoding="utf-8")
            r = run_sync(repo, root / "home", "run", "--dry-run")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("提示性计划", r.stdout)
            self.assertFalse((root / "home" / "sync-state").exists())
            self.assertEqual(change.read_text(encoding="utf-8"), before)

    def test_serial_second_run_all_skip(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = self._repo(root)
            self.assertEqual(run_sync(repo, root / "home", "run").returncode, 0)
            r2 = run_sync(repo, root / "home", "run")
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertIn("→ skip", r2.stdout)
            self.assertNotIn("→ create", r2.stdout)

    def test_lock_contention_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = self._repo(root)
            run_sync(repo, root / "home", "run")  # 造出 .lock
            lock = next((root / "home" / "sync-state").glob("*.lock"))
            fd = os.open(str(lock), os.O_RDWR | os.O_CREAT)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                os.write(fd, json.dumps({"pid": os.getpid(), "at": time.time()}).encode())
                r = run_sync(repo, root / "home", "run")
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                self.assertIn("持锁", r.stderr)
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)

    def test_stale_lock_content_does_not_block(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = self._repo(root)
            run_sync(repo, root / "home", "run")
            lock = next((root / "home" / "sync-state").glob("*.lock"))
            # 死 pid + 老时间戳的陈锁内容：无 live flock 持有者 → 下次 run 正常取锁通过
            lock.write_text(json.dumps({"pid": 2 ** 31 - 1, "at": time.time() - 3600}), encoding="utf-8")
            r = run_sync(repo, root / "home", "run")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class StaleLockPredicateTests(unittest.TestCase):
    def test_predicate(self):
        self.assertTrue(eo_sync._lock_is_stale({"pid": 2 ** 31 - 1, "at": time.time() - 3600}))
        self.assertFalse(eo_sync._lock_is_stale({"pid": os.getpid(), "at": time.time() - 3600}))  # pid 存活
        self.assertFalse(eo_sync._lock_is_stale({"pid": 2 ** 31 - 1, "at": time.time()}))  # 时间新
        self.assertFalse(eo_sync._lock_is_stale({}))


class WritebackValidationTests(unittest.TestCase):
    def _run(self, extra_env, issue="~"):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        root = Path(d.name)
        repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                "doc_root": "eo-doc", "sync": {"fixture": {"enabled": True}}},
                         changes=[{"cid": "c1", "seq": 1, "issue": issue}])
        change = repo / "eo-doc" / "changes" / "01-c1" / "change.md"
        r = run_sync(repo, root / "home", "run", extra_env=extra_env)
        return r, change

    def test_valid_identity_writeback_appends(self):
        r, change = self._run({"EO_FIXTURE_IDENTITY": "page_id", "EO_FIXTURE_WB_FIELD": "page_id", "EO_FIXTURE_WB_VALUE": "abc123"})
        self.assertEqual(r.returncode, 0, r.stderr)
        text = change.read_text(encoding="utf-8")
        self.assertIn("page_id: abc123", text)  # 追加在 --- 前
        self.assertLess(text.index("page_id: abc123"), text.index("\n---\n\n#"))

    def test_unknown_field_rejected(self):
        # 声明 identity=[issue] 但回写 bogus 字段 → 核拒绝该回写
        r, change = self._run({"EO_FIXTURE_IDENTITY": "issue", "EO_FIXTURE_WB_FIELD": "bogus", "EO_FIXTURE_WB_VALUE": "x"})
        self.assertNotIn("bogus", change.read_text(encoding="utf-8"))
        self.assertIn("未在适配器 identity_fields 声明", r.stderr)

    def test_reserved_key_declaration_rejected(self):
        r, change = self._run({"EO_FIXTURE_RESERVED": "1"})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)  # 适配器被拒 → 失败退出码
        self.assertIn("保留键", r.stderr)

    def test_invalid_field_name_rejected(self):
        r, _ = self._run({"EO_FIXTURE_IDENTITY": "Bad-Key"})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("非法身份字段名", r.stderr)

    def test_non_empty_not_overwritten(self):
        # change 已有 issue: 5，夹具回写 issue: 99 → 不覆盖、告警
        r, change = self._run({"EO_FIXTURE_IDENTITY": "issue", "EO_FIXTURE_WB_FIELD": "issue", "EO_FIXTURE_WB_VALUE": "99"}, issue="5")
        self.assertIn("issue: 5", change.read_text(encoding="utf-8"))
        self.assertNotIn("issue: 99", change.read_text(encoding="utf-8"))
        self.assertIn("已有不同非空值", r.stderr)


class OrderedInsertionTests(unittest.TestCase):
    SRC = "---\nid: x\nissue: ~   # 注释\ntitle: T\npr: ~\n---\n\n正文 issue: 保持\n"

    def test_replace_preserves_comment(self):
        out = upsert_frontmatter_fields(self.SRC, {"issue": 42})
        self.assertIn("issue: 42   # 注释", out)
        self.assertIn("正文 issue: 保持", out)

    def test_append_before_close(self):
        out = upsert_frontmatter_fields(self.SRC, {"page_id": "p9"})
        self.assertIn("page_id: p9\n---\n", out)

    def test_idempotent(self):
        once = upsert_frontmatter_fields(self.SRC, {"issue": 42})
        self.assertEqual(upsert_frontmatter_fields(once, {"issue": 42}), once)

    def test_no_frontmatter_untouched(self):
        self.assertEqual(upsert_frontmatter_fields("no fm here", {"issue": 1}), "no fm here")


class WritebackResolveTests(unittest.TestCase):
    def _rec(self, path, status, worktree):
        return {"id": "c1", "status": status, "path": str(path), "worktree": str(worktree)}

    def test_single_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.md"
            p.write_text("x", encoding="utf-8")
            path, cands = resolve_writeback_path([self._rec(p, "confirmed", d)], d)
            self.assertEqual(path, str(p))
            self.assertIsNone(cands)

    def test_highest_status_wins(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.md", Path(d) / "b.md"
            a.write_text("1", encoding="utf-8")
            b.write_text("2", encoding="utf-8")
            recs = [self._rec(a, "confirmed", d + "/w1"), self._rec(b, "reviewed", d + "/w2")]
            path, cands = resolve_writeback_path(recs, None)
            self.assertEqual(path, str(b))  # reviewed > confirmed

    def test_same_status_fork_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "wa" / "c.md", Path(d) / "wb" / "c.md"
            a.parent.mkdir(); b.parent.mkdir()
            a.write_text("内容甲", encoding="utf-8")
            b.write_text("内容乙", encoding="utf-8")  # 分叉
            recs = [self._rec(a, "confirmed", a.parent), self._rec(b, "confirmed", b.parent)]
            path, cands = resolve_writeback_path(recs, None)  # 发起处不在任一候选
            self.assertIsNone(path)
            self.assertEqual(len(cands), 2)

    def test_same_status_identical_content_ok(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "wa" / "c.md", Path(d) / "wb" / "c.md"
            a.parent.mkdir(); b.parent.mkdir()
            a.write_text("同", encoding="utf-8")
            b.write_text("同", encoding="utf-8")
            recs = [self._rec(a, "confirmed", a.parent), self._rec(b, "confirmed", b.parent)]
            path, cands = resolve_writeback_path(recs, None)
            self.assertIsNone(cands)
            self.assertIn(path, {str(a), str(b)})

    def test_origin_worktree_preferred(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "wa" / "c.md", Path(d) / "wb" / "c.md"
            a.parent.mkdir(); b.parent.mkdir()
            a.write_text("甲", encoding="utf-8")
            b.write_text("乙", encoding="utf-8")
            recs = [self._rec(a, "confirmed", a.parent), self._rec(b, "confirmed", b.parent)]
            path, cands = resolve_writeback_path(recs, str(b.parent))  # 发起处 = wb
            self.assertEqual(path, str(b))


class PartialFailureTests(unittest.TestCase):
    def test_one_adapter_fails_others_complete_exit_1(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = init_repo(root, {"project_name": "p", "mode": "vault", "project_root": str(root / "pm"),
                                    "doc_root": "eo-doc",
                                    "sync": {"fixture": {"enabled": True}, "obsidian": {"enabled": True}}},
                             changes=[{"cid": "c1", "seq": 1}])
            (root / "pm").mkdir(exist_ok=True)
            # 夹具非零退出 → 失败；obsidian 仍完成
            r = run_sync(repo, root / "home", "run", extra_env={"EO_FIXTURE_EXIT": "1"})
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertTrue((root / "pm" / "board" / "c1.md").is_file())

    def test_protocol_version_mismatch_skips_and_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                    "doc_root": "eo-doc", "sync": {"fixture": {"enabled": True}}},
                             changes=[{"cid": "c1", "seq": 1}])
            r = run_sync(repo, root / "home", "run", extra_env={"EO_FIXTURE_PROTOCOL": "99"})
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("协议主版本不匹配", r.stderr)

    def test_invalid_json_skips_and_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                    "doc_root": "eo-doc", "sync": {"fixture": {"enabled": True}}},
                             changes=[{"cid": "c1", "seq": 1}])
            r = run_sync(repo, root / "home", "run", extra_env={"EO_FIXTURE_BAD_JSON": "1"})
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)


class BookkeepingIsolationTests(unittest.TestCase):
    def test_bookkeeping_in_eo_home_not_repo_and_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                    "doc_root": "eo-doc", "sync": {"fixture": {"enabled": True}}},
                             changes=[{"cid": "c1", "seq": 1}])
            run_sync(repo, root / "home", "run")
            state = list((root / "home" / "sync-state").glob("*.json"))
            self.assertEqual(len(state), 1)
            data = json.loads(state[0].read_text(encoding="utf-8"))
            self.assertEqual(data["version"], 1)
            self.assertIn("fixture", data["adapters"])
            # 仓库内零新增未跟踪文件（除已跟踪的 change 与回写）
            status = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True).stdout
            self.assertNotIn("sync-state", status)

    def test_never_touches_real_eo_home(self):
        # 显式断言：所有 run 都带 EO_HOME 指向 temp；这里核对 bookkeeping_path 用 EO_HOME
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                    "doc_root": "eo-doc", "sync": {"fixture": {"enabled": True}}},
                             changes=[{"cid": "c1", "seq": 1}])
            os.environ_backup = os.environ.get("EO_HOME")
            try:
                os.environ["EO_HOME"] = str(root / "home")
                from eo_lib import load_project_config, find_project_config
                cfg = load_project_config(find_project_config(repo))
                bk = eo_sync.bookkeeping_path(cfg)
                self.assertTrue(str(bk).startswith(str(root / "home")))
            finally:
                if os.environ_backup is None:
                    os.environ.pop("EO_HOME", None)
                else:
                    os.environ["EO_HOME"] = os.environ_backup


if __name__ == "__main__":
    unittest.main()
