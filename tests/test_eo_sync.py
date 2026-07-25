"""eo-sync 完整测试矩阵（复用 tests/fixtures/eo-sync-fixture 夹具）。

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
        # change 已有 issue: 5，夹具强制回写 issue: 99 → 核不覆盖、告警
        r, change = self._run({"EO_FIXTURE_IDENTITY": "issue", "EO_FIXTURE_WB_FIELD": "issue",
                               "EO_FIXTURE_WB_VALUE": "99", "EO_FIXTURE_FORCE_WB": "1"}, issue="5")
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


class SelectiveRunTests(unittest.TestCase):
    """选择性 run（--change）不得把范围外投影当孤儿删除。"""

    def _setup(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        root = Path(d.name)
        repo = init_repo(root, {"project_name": "p", "mode": "vault", "project_root": str(root / "pm"),
                                "doc_root": "eo-doc", "sync": {"obsidian": {"enabled": True}}},
                         changes=[{"cid": "c1", "seq": 1}, {"cid": "c2", "seq": 2}])
        (root / "pm").mkdir(exist_ok=True)
        return root, repo

    def test_change_filter_does_not_delete_out_of_scope(self):
        root, repo = self._setup()
        self.assertEqual(run_sync(repo, root / "home", "run").returncode, 0)
        board = root / "pm" / "board"
        self.assertTrue((board / "c1.md").is_file() and (board / "c2.md").is_file())
        r = run_sync(repo, root / "home", "run", "--change", "c1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((board / "c2.md").is_file(), "范围外 c2 stub 被误删")
        self.assertNotIn("delete", r.stdout)

    def test_nonexistent_change_deletes_nothing(self):
        root, repo = self._setup()
        run_sync(repo, root / "home", "run")
        board = root / "pm" / "board"
        run_sync(repo, root / "home", "run", "--change", "nope")
        self.assertTrue((board / "c1.md").is_file() and (board / "c2.md").is_file())

    def test_full_run_still_deletes_orphan(self):
        import shutil
        root, repo = self._setup()
        run_sync(repo, root / "home", "run")
        board = root / "pm" / "board"
        shutil.rmtree(repo / "eo-doc" / "changes" / "02-c2")
        git(repo, "add", "-A")
        git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "drop c2")
        r = run_sync(repo, root / "home", "run")
        self.assertEqual(r.returncode, 0)
        self.assertFalse((board / "c2.md").is_file(), "全量 run 未清理孤儿 stub")
        self.assertTrue((board / "c1.md").is_file())

    def test_scan_degradation_suppresses_delete(self):
        # c2 的 change.md 损坏（无 frontmatter）→ 扫描告警 → 快照不可证完整 → 本轮禁删，c2 stub 保留
        root, repo = self._setup()
        run_sync(repo, root / "home", "run")
        board = root / "pm" / "board"
        (repo / "eo-doc" / "changes" / "02-c2" / "change.md").write_text("无 frontmatter", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "corrupt c2")
        r = run_sync(repo, root / "home", "run")
        self.assertTrue((board / "c2.md").is_file(), "扫描降级下 c2 stub 被误删")
        self.assertIn("跳过孤儿投影清理", r.stderr)


class IdentityReadPathTests(unittest.TestCase):
    """写回的身份字段下次扫描应交还适配器（旁车丢失后仍能定位原对象）。"""

    def test_read_identity_after_sidecar_loss(self):
        import shutil
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        root = Path(d.name)
        repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                "doc_root": "eo-doc", "sync": {"fixture": {"enabled": True}}},
                         changes=[{"cid": "c1", "seq": 1}])
        change = repo / "eo-doc" / "changes" / "01-c1" / "change.md"
        env = {"EO_FIXTURE_IDENTITY": "page_id", "EO_FIXTURE_WB_FIELD": "page_id", "EO_FIXTURE_WB_VALUE": "pg-1"}
        run_sync(repo, root / "home", "run", extra_env=env)
        self.assertIn("page_id: pg-1", change.read_text(encoding="utf-8"))
        shutil.rmtree(root / "home" / "sync-state")  # 旁车丢失
        r = run_sync(repo, root / "home", "run", extra_env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("→ skip", r.stdout)
        self.assertNotIn("→ create", r.stdout)  # 从 SoT 读回身份，不当作新对象重建


class ResolveChangeUnifiedTests(unittest.TestCase):
    """计划来源与回写落点共用同一 resolve_change 结果。"""

    def _rec(self, path, status, wt):
        return {"id": "c1", "status": status, "path": str(path), "worktree": str(wt)}

    def test_resolve_change_and_writeback_path_agree(self):
        from eo_lib import resolve_change
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "wa" / "c.md", Path(d) / "wb" / "c.md"
            a.parent.mkdir(); b.parent.mkdir()
            a.write_text("甲", encoding="utf-8")
            b.write_text("乙", encoding="utf-8")
            recs = [self._rec(a, "confirmed", a.parent), self._rec(b, "confirmed", b.parent)]
            rec, cands = resolve_change(recs, str(b.parent))  # 发起处 = wb
            self.assertEqual(rec["path"], str(b))
            path, _ = resolve_writeback_path(recs, str(b.parent))
            self.assertEqual(path, rec["path"])  # 同一份，不会 plan/writeback 错位

    def test_fork_fail_closed(self):
        from eo_lib import resolve_change
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "wa" / "c.md", Path(d) / "wb" / "c.md"
            a.parent.mkdir(); b.parent.mkdir()
            a.write_text("甲", encoding="utf-8")
            b.write_text("乙", encoding="utf-8")
            recs = [self._rec(a, "confirmed", a.parent), self._rec(b, "confirmed", b.parent)]
            rec, cands = resolve_change(recs, None)
            self.assertIsNone(rec)
            self.assertEqual(len(cands), 2)


class ResponseSchemaTests(unittest.TestCase):
    """结构合法 JSON 但 schema 非法/缺必填字段的响应仅隔离该适配器，不中断全局。"""

    def _run(self, bad_shape):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        root = Path(d.name)
        repo = init_repo(root, {"project_name": "p", "mode": "vault", "project_root": str(root / "pm"),
                                "doc_root": "eo-doc",
                                "sync": {"fixture": {"enabled": True}, "obsidian": {"enabled": True}}},
                         changes=[{"cid": "c1", "seq": 1}])
        (root / "pm").mkdir(exist_ok=True)
        return run_sync(repo, root / "home", "run", extra_env={"EO_FIXTURE_BAD_SHAPE": bad_shape}), root

    def test_bad_plan_shape_isolated(self):
        r, root = self._run("plan")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("结构非法", r.stderr)
        self.assertTrue((root / "pm" / "board" / "c1.md").is_file())  # obsidian 仍完成

    def test_bad_apply_shape_isolated(self):
        r, root = self._run("apply")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("结构非法", r.stderr)

    def test_missing_plan_field_isolated(self):
        r, root = self._run("plan_missing")  # 响应缺必填 actions
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("缺少必填", r.stderr)
        self.assertTrue((root / "pm" / "board" / "c1.md").is_file())

    def test_missing_apply_field_isolated(self):
        r, root = self._run("apply_missing")  # 响应缺必填 bookkeeping
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("缺少必填", r.stderr)

    def test_missing_writeback_field_isolated(self):
        r, root = self._run("apply_no_wb")  # 响应缺必填 writeback
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("缺少必填", r.stderr)


class SyncSegmentSemanticsTests(unittest.TestCase):
    """显式 sync 段（含空 {} / null）关闭存量兼容映射；非法类型为配置错误。"""

    def test_empty_sync_disables_compat(self):
        self.assertEqual(eo_sync.resolve_enabled({"sync": {}, "board": {"enabled": True}}), {})

    def test_absent_sync_uses_compat(self):
        self.assertIn("obsidian", eo_sync.resolve_enabled({"board": {"enabled": True}}))

    def test_invalid_sync_type_is_config_error(self):
        from eo_lib import load_project_config, find_project_config, ConfigError
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = root / "repo"
            repo.mkdir()
            (repo / ".eo-project.json").write_text(json.dumps(
                {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                 "doc_root": "eo-doc", "sync": "foo"}), encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_project_config(find_project_config(repo))

    def test_empty_sync_run_exit_zero(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                    "doc_root": "eo-doc", "sync": {}, "board": {"enabled": True}},
                             changes=[{"cid": "c1", "seq": 1}])
            r = run_sync(repo, root / "home", "run")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("未启用任何同步目标", r.stdout)

    def test_null_sync_disables_compat(self):
        # 显式 sync: null 是「段存在」，视为零目标，绝不回落 board/github
        self.assertEqual(eo_sync.resolve_enabled({"sync": None, "board": {"enabled": True}}), {})

    def test_null_sync_config_run_exit_zero(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                    "doc_root": "eo-doc", "sync": None, "board": {"enabled": True}},
                             changes=[{"cid": "c1", "seq": 1}])
            r = run_sync(repo, root / "home", "run")  # sync:null 经真实 config 加载
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("未启用任何同步目标", r.stdout)

    def test_sync_null_contract_documented(self):
        # 代码-文档一致化：sync:null 的合法性须写进公开契约（对表格管道转义鲁棒）
        cfg_md = (REPO_ROOT / "eo-project-init" / "references" / "config.md").read_text(encoding="utf-8")
        proto = (REPO_ROOT / "docs" / "sync-adapter-protocol.md").read_text(encoding="utf-8")
        self.assertIn("显式 `null`", cfg_md)
        self.assertIn("零目标", cfg_md)
        self.assertIn("null", proto)


class GithubFixTests(unittest.TestCase):
    """gh 结果如实进簿记与输出；archived issue 关闭幂等。"""

    def test_github_dry_run_plans_without_remote_or_writes(self):
        """GitHub 目标 dry-run 只给出计划，不触发 gh 或写入任一介质。"""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                    "doc_root": "eo-doc",
                                    "sync": {"github": {"enabled": True, "issue": True, "pr": "always"}}},
                             changes=[
                                 {"cid": "draft", "seq": 1, "status": "draft"},
                                 {"cid": "confirmed", "seq": 2, "status": "confirmed"},
                                 {"cid": "archived", "seq": 3, "status": "archived"},
                             ])
            changes = sorted(repo.glob("eo-doc/changes/*/change.md"))
            before = {path: path.read_text(encoding="utf-8") for path in changes}

            r = run_sync(repo, root / "home", "run", "--dry-run")

            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("draft × github/issue → skip", r.stdout)
            self.assertIn("confirmed × github/issue → create", r.stdout)
            self.assertIn("archived × github/issue → create", r.stdout)
            self.assertIn("archived × github/pr → create", r.stdout)
            self.assertIn("提示性计划", r.stdout)
            self.assertFalse((root / "home" / "sync-state").exists())
            self.assertEqual({path: path.read_text(encoding="utf-8") for path in changes}, before)
            self.assertEqual(
                subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True).stdout,
                "",
            )

    def test_gh_unavailable_surfaced_and_bookkeeping_clean(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                    "doc_root": "eo-doc",
                                    "sync": {"github": {"enabled": True, "issue": True, "pr": "never"}}},
                             changes=[{"cid": "c1", "seq": 1, "status": "confirmed"}])
            r = run_sync(repo, root / "home", "run")  # 临时仓库无 remote
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)  # 跳过不阻塞
            self.assertIn("skip", r.stdout)
            self.assertIn("gh 不可用或无 remote", r.stdout)  # 原因如实呈现，不显示计划的 create
            state = json.loads(next((root / "home" / "sync-state").glob("*.json")).read_text(encoding="utf-8"))
            self.assertNotIn("issue_body_hash", state["adapters"].get("github", {}).get("c1", {}))

    def test_archived_issue_close_idempotent_via_bookkeeping(self):
        gh = load_module("gh_plan_probe", CLI_DIR / "eo-sync-github")
        change = {"id": "c", "status": "archived", "issue": 42, "title": "T", "summary": "S",
                  "tier": "full", "ac": [], "todo": [], "commits": []}
        a1 = gh._plan_issue(change, {"issue": True}, {})
        self.assertEqual((a1["op"], a1["payload"]["mode"]), ("update", "close"))
        a2 = gh._plan_issue(change, {"issue": True}, {"c": {"issue_closed": True}})
        self.assertEqual(a2["op"], "skip")


class RetirementDisciplineTests(unittest.TestCase):
    """语义退役无残留 + 新代码/测试注释无流程溯源。"""

    def test_no_immediate_projection_in_skills(self):
        eo_change = (REPO_ROOT / "eo-change" / "SKILL.md").read_text(encoding="utf-8")
        eo_impl = (REPO_ROOT / "eo-implement" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("再刷新一次投影", eo_change)
        self.assertNotIn("GitHub 联动 → stub 终态", eo_impl)
        self.assertNotIn("GitHub 联动 → stub", eo_impl)

    def test_no_process_traceability(self):
        import re as _re
        # finding 号与 change 节号是纯流程溯源，任何文件（含 test docstring）都不该出现；
        # pattern 由片段拼接构造，避免匹配本函数自身。
        finding = _re.compile("P" + r"[01]-\d")
        section = _re.compile(chr(0xa7) + r"5\.\d")
        # 章节/批次/AC 号在真实 change 内容里合法，只查非测试文件（代码/夹具）的注释
        soft = _re.compile(r"AC-\d|" + r"Batch\s*\d|" + r"TODO-\d")
        code_files = ["cli/eo-sync", "cli/eo-sync-obsidian", "cli/eo-sync-github",
                      "tests/fixtures/eo-sync-fixture", "cli/eo_lib/changes.py",
                      "cli/eo_lib/config.py", "cli/eo_lib/frontmatter.py"]
        test_files = ["tests/test_eo_sync.py", "tests/test_eo_sync_smoke.py"]
        offenders = []
        for f in code_files + test_files:
            for i, line in enumerate((REPO_ROOT / f).read_text(encoding="utf-8").splitlines(), 1):
                if finding.search(line) or section.search(line):
                    offenders.append(f"{f}:{i}")
                elif f in code_files and "#" in line and soft.search(line.split("#", 1)[1]):
                    offenders.append(f"{f}:{i}")
        self.assertEqual(offenders, [], f"含流程溯源标记：{offenders}")


class IdentitiesScalarTests(unittest.TestCase):
    """快照 identities 只暴露标量身份，列表/对象 frontmatter 被排除（协议 v1 标量契约）。"""

    def test_identities_excludes_non_scalar(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        p = Path(d.name) / "change.md"
        p.write_text(
            "---\nid: c1\nissue: 7\npr: https://x/pull/2\npage_id: pg-9\n"
            "commits: [a, b]\nfix_consumed: [rev1]\n---\n\n# T\n",
            encoding="utf-8")
        ids = eo_sync._read_identities({"path": str(p)})
        self.assertEqual(ids.get("issue"), 7)
        self.assertEqual(ids.get("page_id"), "pg-9")
        self.assertNotIn("commits", ids)
        self.assertNotIn("fix_consumed", ids)
        for v in ids.values():
            self.assertNotIsInstance(v, (list, dict))


class AtomicScanTests(unittest.TestCase):
    """快照与其完整性同源同时刻：build_scan 单一原子结构，worktree 枚举降级即判不完整。"""

    def _cfg_repo(self, root):
        from eo_lib import load_project_config, find_project_config
        repo = init_repo(root, {"project_name": "p", "mode": "local", "project_root": str(root / "pm"),
                                "doc_root": "eo-doc", "sync": {"obsidian": {"enabled": True}}},
                         changes=[{"cid": "c1", "seq": 1}])
        return load_project_config(find_project_config(repo)), repo

    def test_list_worktrees_status_ok_signal(self):
        from eo_lib import list_worktrees_status
        with tempfile.TemporaryDirectory() as d:
            wts, ok = list_worktrees_status(d)  # 非 git 目录：单目录、完整
            self.assertTrue(ok)
            self.assertEqual(len(wts), 1)
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d) / "r"
            repo.mkdir()
            (repo / "x").write_text("x", encoding="utf-8")
            git(repo, "init", "-q")
            git(repo, "add", "-A")
            git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "i")
            wts, ok = list_worktrees_status(repo)  # git 仓库正常枚举
            self.assertTrue(ok)

    def test_build_scan_complete_clean_full(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg, repo = self._cfg_repo(root)
            scan = eo_sync.build_scan(cfg, str(repo), None, str(repo), [])
            self.assertTrue(scan["complete"])
            self.assertIn("c1", scan["resolved"])

    def test_build_scan_incomplete_on_filter(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg, repo = self._cfg_repo(root)
            scan = eo_sync.build_scan(cfg, str(repo), "c1", str(repo), [])
            self.assertFalse(scan["complete"])
            self.assertIn("选择性过滤", scan["reasons"])

    def test_build_scan_incomplete_on_worktree_degradation(self):
        # 降级信号与快照来自同一次 build_scan：枚举降级 → complete=False（同源同时刻，杜绝旧判定配新快照）
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cfg, repo = self._cfg_repo(root)
            orig = eo_sync.list_worktrees_status
            eo_sync.list_worktrees_status = lambda anchor: ([{"path": str(repo), "branch": None}], False)
            try:
                scan = eo_sync.build_scan(cfg, str(repo), None, str(repo), [])
            finally:
                eo_sync.list_worktrees_status = orig
            self.assertFalse(scan["complete"])
            self.assertIn("worktree 枚举降级", scan["reasons"])


if __name__ == "__main__":
    unittest.main()
