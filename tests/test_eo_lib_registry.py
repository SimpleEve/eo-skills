"""eo_lib.registry 项目注册表测试。

覆盖：幂等注册、主/linked worktree 去重与簿记 hash8 交叉一致、原子写失败不破坏旧文件、
EO_HOME 隔离、未知字段两级 round-trip、损坏 JSON 容错、同名项目共存、
eo-board --register/--unregister 往返复原。

隔离：EO_HOME 一律指向临时目录，绝不触碰真实 ~/.eo。
"""

import hashlib
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_DIR = REPO_ROOT / "cli"
BOARD_PATH = CLI_DIR / "eo-board"
EO_SYNC_PATH = CLI_DIR / "eo-sync"

if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))

from eo_lib import (
    ConfigError,
    load_registry,
    register_project,
    registry_path,
    repo_identity,
    save_registry,
    unregister_project,
)


def load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def make_git_repo(root, name="repo"):
    repo = root / name
    repo.mkdir(parents=True)
    (repo / "f.txt").write_text("x", encoding="utf-8")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return repo


class RegistryTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.eo_home = self.root / "eo-home"
        patcher = mock.patch.dict(os.environ, {"EO_HOME": str(self.eo_home)})
        patcher.start()
        self.addCleanup(patcher.stop)


class RegistryCoreTests(RegistryTestBase):
    def test_eo_home_isolation(self):
        self.assertEqual(registry_path(), self.eo_home / "projects.json")
        repo = make_git_repo(self.root)
        register_project(repo, "p1")
        self.assertTrue((self.eo_home / "projects.json").is_file())
        # 缺失文件视为空表
        with mock.patch.dict(os.environ, {"EO_HOME": str(self.root / "empty")}):
            self.assertEqual(load_registry()["projects"], [])

    def test_register_idempotent(self):
        repo = make_git_repo(self.root)
        r1 = register_project(repo, "p1")
        r2 = register_project(repo, "p1-renamed")
        self.assertEqual(r1["action"], "created")
        self.assertEqual(r2["action"], "updated")
        data = load_registry()
        self.assertEqual(len(data["projects"]), 1)
        self.assertEqual(data["projects"][0]["name"], "p1-renamed")

    def test_worktree_dedup_and_bookkeeping_hash8_cross(self):
        repo = make_git_repo(self.root)
        wt = self.root / "linked-wt"
        git(repo, "worktree", "add", "-q", str(wt), "-b", "side")
        register_project(repo, "p1")
        result = register_project(wt, "p1")
        self.assertEqual(result["action"], "updated")
        data = load_registry()
        self.assertEqual(len(data["projects"]), 1)
        # path 保持首次注册值（主 worktree）
        self.assertEqual(data["projects"][0]["path"], str(repo.resolve()))
        # 交叉判据：registry 去重身份与 eo-sync 簿记 hash8 同源——任一 worktree 算出同一 hash8
        self.assertEqual(repo_identity(repo), repo_identity(wt))
        eo_sync = load_module("eo_sync_registry_cross", EO_SYNC_PATH)
        h_main = eo_sync.bookkeeping_path({"repo_root": repo, "project_name": "p1"}).name
        h_wt = eo_sync.bookkeeping_path({"repo_root": wt, "project_name": "p1"}).name
        self.assertEqual(h_main, h_wt)
        expected = hashlib.sha256(repo_identity(repo).encode("utf-8")).hexdigest()[:8]
        self.assertEqual(h_main, f"p1-{expected}.json")

    def test_atomic_write_failure_keeps_old_file(self):
        repo = make_git_repo(self.root)
        register_project(repo, "p1")
        before = (self.eo_home / "projects.json").read_text(encoding="utf-8")
        other = make_git_repo(self.root, "repo2")
        with mock.patch("eo_lib.registry.os.replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                register_project(other, "p2")
        self.assertEqual((self.eo_home / "projects.json").read_text(encoding="utf-8"), before)

    def test_unknown_fields_two_level_roundtrip(self):
        plain = self.root / "plain-dir"
        plain.mkdir()
        self.eo_home.mkdir(parents=True)
        (self.eo_home / "projects.json").write_text(
            json.dumps({
                "version": 1,
                "future_top": {"keep": True},
                "projects": [{
                    "name": "old", "path": str(plain), "registered_at": "2026-01-01",
                    "future_entry": "keep-me",
                }],
            }),
            encoding="utf-8",
        )
        register_project(plain, "old-renamed")
        raw = json.loads((self.eo_home / "projects.json").read_text(encoding="utf-8"))
        self.assertEqual(raw["future_top"], {"keep": True})
        self.assertEqual(len(raw["projects"]), 1)
        self.assertEqual(raw["projects"][0]["future_entry"], "keep-me")
        self.assertEqual(raw["projects"][0]["name"], "old-renamed")

    def test_corrupt_json_raises_not_silently_cleared(self):
        self.eo_home.mkdir(parents=True)
        (self.eo_home / "projects.json").write_text("{oops", encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_registry()
        repo = make_git_repo(self.root)
        with self.assertRaises(ConfigError):
            register_project(repo, "p1")
        # 损坏文件原样保留，未被清空重建
        self.assertEqual((self.eo_home / "projects.json").read_text(encoding="utf-8"), "{oops")
        with self.assertRaises(ConfigError):
            load_registry(self.eo_home / "projects.json")
        (self.eo_home / "projects.json").write_text("[1,2]", encoding="utf-8")
        with self.assertRaises(ConfigError):
            load_registry()

    def test_same_name_projects_coexist(self):
        a = make_git_repo(self.root, "a")
        b = make_git_repo(self.root, "b")
        register_project(a, "dup")
        result = register_project(b, "dup")
        self.assertEqual(result["action"], "created")
        data = load_registry()
        self.assertEqual(len(data["projects"]), 2)
        self.assertEqual([e.get("path") for e in result["same_name"]], [str(a.resolve())])

    def test_non_git_dir_realpath_dedup(self):
        plain = self.root / "plain"
        plain.mkdir()
        link = self.root / "plain-link"
        link.symlink_to(plain)
        register_project(plain, "p")
        result = register_project(link, "p")
        self.assertEqual(result["action"], "updated")
        self.assertEqual(len(load_registry()["projects"]), 1)

    def test_save_registry_atomic_no_tmp_leftover(self):
        save_registry({"version": 1, "projects": []})
        self.assertTrue((self.eo_home / "projects.json").is_file())
        self.assertFalse((self.eo_home / "projects.json.tmp").exists())


class BoardRegisterCliTests(RegistryTestBase):
    def _make_project(self, name="proj"):
        repo = make_git_repo(self.root, name)
        pm = self.root / f"{name}-pm"
        pm.mkdir()
        (repo / ".eo-project.json").write_text(json.dumps({
            "project_name": name,
            "mode": "vault",
            "project_root": str(pm),
            "doc_root": "eo-doc",
        }), encoding="utf-8")
        return repo

    def _run_board(self, *args, cwd=None):
        env = dict(os.environ)
        env["EO_HOME"] = str(self.eo_home)
        return subprocess.run(
            [sys.executable, str(BOARD_PATH), *args],
            cwd=cwd or self.root, env=env, capture_output=True, text=True,
        )

    def test_register_unregister_roundtrip_restores_registry(self):
        repo = self._make_project()
        r = self._run_board("--register", str(repo))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("已注册", r.stdout)
        data = json.loads((self.eo_home / "projects.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["projects"]), 1)

        r = self._run_board("--unregister", str(repo))
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads((self.eo_home / "projects.json").read_text(encoding="utf-8"))
        self.assertEqual(data["projects"], [])

    def test_register_defaults_to_cwd_and_searches_upward(self):
        repo = self._make_project()
        sub = repo / "src"
        sub.mkdir()
        r = self._run_board("--register", cwd=sub)
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads((self.eo_home / "projects.json").read_text(encoding="utf-8"))
        self.assertEqual(data["projects"][0]["path"], str(repo.resolve()))

    def test_unregister_miss_gives_clear_hint(self):
        r = self._run_board("--unregister", str(self.root / "nowhere"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("未命中", r.stderr)

    def test_register_same_name_warns_coexist(self):
        a = self._make_project("dupname")
        b = make_git_repo(self.root, "other-repo")
        pm = self.root / "other-pm"
        pm.mkdir()
        (b / ".eo-project.json").write_text(json.dumps({
            "project_name": "dupname", "mode": "vault",
            "project_root": str(pm), "doc_root": "eo-doc",
        }), encoding="utf-8")
        self.assertEqual(self._run_board("--register", str(a)).returncode, 0)
        r = self._run_board("--register", str(b))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("同名共存", r.stdout)
        data = json.loads((self.eo_home / "projects.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["projects"]), 2)

    def test_register_fails_clearly_when_home_unwritable(self):
        repo = self._make_project()
        self.eo_home.mkdir(parents=True)
        os.chmod(self.eo_home, 0o555)
        self.addCleanup(os.chmod, self.eo_home, 0o755)
        r = self._run_board("--register", str(repo))
        self.assertNotEqual(r.returncode, 0)
        self.assertTrue(r.stderr.strip())


if __name__ == "__main__":
    unittest.main()
