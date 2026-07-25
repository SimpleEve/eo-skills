"""eo_lib.config 的 project_root 归一化：相对路径按 repo root 解析并解软链。

覆盖：v1 遗留的软链相对 project_root（形如 "eo-doc/vault"）读取成功并告警、
绝对路径逐字段零变化且零告警、解析不出目录时 fail-closed 报错、既有校验矩阵不动。
外加 eo-project-init 1.5 分支把该形态列为可修项的文档口径断言。
"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_DIR = REPO_ROOT / "cli"

if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))

from eo_lib import ConfigError, load_project_config

INIT_SKILL = (REPO_ROOT / "eo-project-init" / "SKILL.md").read_text(encoding="utf-8")


def line_containing(text, needle):
    return next(l for l in text.splitlines() if needle in l)


class ProjectRootNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / "repo"
        (self.repo / "eo-doc").mkdir(parents=True)
        self.vault = self.root / "vault-side" / "兔村游戏"
        self.vault.mkdir(parents=True)

    def _write_config(self, project_root, **extra):
        cfg = {
            "project_name": "兔村游戏",
            "mode": "vault",
            "project_root": project_root,
            "doc_root": "eo-doc",
            "kanban_path": None,
            "board": {"enabled": True},
            "github": {"issue": False, "pr": "never"},
        }
        cfg.update(extra)
        path = self.repo / ".eo-project.json"
        path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
        return path

    def _load(self, path):
        """返回 (cfg, stderr 文本)；期望成功的路径上把 ConfigError 转成断言失败。"""
        buf = io.StringIO()
        try:
            with redirect_stderr(buf):
                cfg = load_project_config(path)
        except ConfigError as e:
            self.fail(f"配置本应归一化后放行，却被拒绝：{e}")
        return cfg, buf.getvalue()

    def _load_expecting_error(self, path):
        buf = io.StringIO()
        with redirect_stderr(buf):
            return load_project_config(path)

    def test_relative_symlink_project_root_resolves_and_warns(self):
        # Rabbit 的真实形态：project_root 指向 <repo>/eo-doc/vault 软链
        (self.repo / "eo-doc" / "vault").symlink_to(self.vault)
        path = self._write_config("eo-doc/vault")

        cfg, err = self._load(path)

        self.assertEqual(cfg["project_root"], str(self.vault.resolve()))
        self.assertTrue(Path(cfg["project_root"]).is_absolute())
        self.assertIn("project_root", err)
        self.assertIn("eo-doc/vault", err)
        self.assertIn("eo-project-init", err)
        self.assertEqual(len(err.strip().splitlines()), 1, err)

    def test_relative_plain_dir_project_root_resolves(self):
        (self.repo / ".eo-project").mkdir()
        path = self._write_config(".eo-project", mode="local")

        cfg, err = self._load(path)

        self.assertEqual(cfg["project_root"], str((self.repo / ".eo-project").resolve()))
        self.assertIn("project_root", err)

    def test_absolute_project_root_unchanged_and_silent(self):
        path = self._write_config(str(self.vault))

        cfg, err = self._load(path)

        self.assertEqual(cfg["project_root"], str(self.vault))
        self.assertEqual(err, "")

    def test_absolute_symlink_project_root_not_dereferenced(self):
        link = self.root / "link-to-vault"
        link.symlink_to(self.vault)
        path = self._write_config(str(link))

        cfg, err = self._load(path)

        self.assertEqual(cfg["project_root"], str(link))
        self.assertEqual(err, "")

    def test_relative_missing_target_still_fails_closed(self):
        path = self._write_config("eo-doc/vault")
        with self.assertRaises(ConfigError) as ctx:
            self._load_expecting_error(path)
        self.assertIn("project_root", str(ctx.exception))
        self.assertIn("eo-doc/vault", str(ctx.exception))

    def test_relative_dangling_symlink_fails_closed(self):
        (self.repo / "eo-doc" / "vault").symlink_to(self.root / "gone")
        path = self._write_config("eo-doc/vault")
        with self.assertRaises(ConfigError):
            self._load_expecting_error(path)

    def test_relative_symlink_loop_fails_closed(self):
        # 成环软链在 CPython 的 resolve() 抛 RuntimeError，不得穿透成裸 traceback
        loop = self.repo / "eo-doc" / "vault"
        loop.symlink_to(loop)
        path = self._write_config("eo-doc/vault")
        with self.assertRaises(ConfigError):
            self._load_expecting_error(path)

    def test_target_vanishing_after_validation_fails_closed(self):
        # 校验通过与取值之间目标消失：绝不把 None 当路径传给下游
        (self.repo / "eo-doc" / "vault").symlink_to(self.vault)
        path = self._write_config("eo-doc/vault")
        import eo_lib.config as config_mod

        real = config_mod._normalize_project_root
        calls = []

        def flaky(project_root, cfg_path):
            calls.append(project_root)
            return real(project_root, cfg_path) if len(calls) == 1 else None

        with mock.patch.object(config_mod, "_normalize_project_root", flaky):
            with self.assertRaises(ConfigError):
                self._load_expecting_error(path)

    def test_relative_pointing_to_file_fails_closed(self):
        (self.repo / "eo-doc" / "vault").write_text("not a dir", encoding="utf-8")
        path = self._write_config("eo-doc/vault")
        with self.assertRaises(ConfigError):
            self._load_expecting_error(path)

    def test_local_override_relative_root_also_normalized(self):
        (self.repo / "eo-doc" / "vault").symlink_to(self.vault)
        path = self._write_config(str(self.root / "shared-side"))
        (self.repo / ".eo-project.local.json").write_text(
            json.dumps({"project_root": "eo-doc/vault"}), encoding="utf-8"
        )

        cfg, err = self._load(path)

        self.assertEqual(cfg["project_root"], str(self.vault.resolve()))
        self.assertIn("project_root", err)


class ExistingValidationMatrixTests(unittest.TestCase):
    """AC-5 characterization：除 project_root 相对分支外的校验行为逐条不变。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir(parents=True)
        self.pm = self.root / "pm"
        self.pm.mkdir()

    def _load_raw(self, cfg):
        path = self.repo / ".eo-project.json"
        path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
        buf = io.StringIO()
        with redirect_stderr(buf):
            return load_project_config(path)

    def _base(self, **over):
        cfg = {"project_name": "p", "mode": "local", "project_root": str(self.pm), "doc_root": "eo-doc"}
        cfg.update(over)
        return cfg

    def test_missing_required_field_rejected(self):
        for field in ("project_name", "mode", "project_root", "doc_root"):
            cfg = self._base()
            del cfg[field]
            with self.assertRaises(ConfigError, msg=field):
                self._load_raw(cfg)

    def test_blank_required_field_rejected(self):
        with self.assertRaises(ConfigError):
            self._load_raw(self._base(project_name="   "))

    def test_bad_mode_rejected(self):
        with self.assertRaises(ConfigError):
            self._load_raw(self._base(mode="hybrid"))

    def test_absolute_doc_root_rejected(self):
        with self.assertRaises(ConfigError):
            self._load_raw(self._base(doc_root="/abs/eo-doc"))

    def test_non_object_sync_rejected(self):
        with self.assertRaises(ConfigError):
            self._load_raw(self._base(sync=3))

    def test_sync_key_presence_semantics_preserved(self):
        self.assertNotIn("sync", self._load_raw(self._base()))
        self.assertIsNone(self._load_raw(self._base(sync=None))["sync"])
        self.assertEqual(self._load_raw(self._base(sync={}))["sync"], {})


class InitRepairBranchCaliberTests(unittest.TestCase):
    def test_repair_branch_lists_project_root_as_fixable(self):
        step1 = line_containing(INIT_SKILL, "**配置校验**")
        self.assertIn("project_root", step1)
        self.assertIn("绝对路径", step1)
        self.assertIn("回写", step1)

    def test_repair_branch_keeps_local_first_writeback_rule(self):
        step1 = line_containing(INIT_SKILL, "**配置校验**")
        fixable = step1.split("project_root", 1)[1]
        self.assertIn(".eo-project.local.json", fixable)
        self.assertIn("写 local", fixable)
        self.assertIn(".eo-project.json", fixable)


if __name__ == "__main__":
    unittest.main()
