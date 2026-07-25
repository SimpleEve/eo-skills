"""sync 段收编口径静态断言：init 停写 board/github 旧段、改写 sync 段。

读四个口径文件（eo-project-init/SKILL.md、references/config.md、
eo-shared/board-github.md、docs/GUIDE.md）断言新口径锚点存在、旧口径残留清零；
另断言本仓 .eo-project.json 狗粮迁移等价、cli/ 在本 change 区间零 diff。
兼容映射的行为语义基线由 tests/test_eo_sync.py::test_compat_mapping 既有覆盖
（characterization，基线即绿）。
"""

import importlib.machinery
import importlib.util
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKILL = (ROOT / "eo-project-init" / "SKILL.md").read_text(encoding="utf-8")
CONFIG = (ROOT / "eo-project-init" / "references" / "config.md").read_text(encoding="utf-8")
BG = (ROOT / "eo-shared" / "board-github.md").read_text(encoding="utf-8")
GUIDE = (ROOT / "docs" / "GUIDE.md").read_text(encoding="utf-8")
CHANGE = (ROOT / "eo-doc" / "changes" / "05-sync-config-consolidation" / "change.md").read_text(encoding="utf-8")


def section(text, start, end):
    if start not in text:
        raise AssertionError(f"找不到节起点 {start!r}")
    seg = text.split(start, 1)[1]
    return seg.split(end, 1)[0] if end in seg else seg


def line_containing(text, needle):
    return next(l for l in text.splitlines() if needle in l)


def load_eo_sync():
    loader = importlib.machinery.SourceFileLoader("eo_sync_caliber", str(ROOT / "cli" / "eo-sync"))
    spec = importlib.util.spec_from_loader("eo_sync_caliber", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class TestAC1InitWritesSyncSection(unittest.TestCase):
    def setUp(self):
        self.sec = section(SKILL, "**sync 段**", "用户跳过")

    def test_answers_land_in_sync_adapters(self):
        self.assertIn("sync.obsidian", self.sec)
        self.assertIn("sync.github", self.sec)
        self.assertIn("stub_dir", self.sec)

    def test_old_sections_no_longer_written(self):
        self.assertIn("不再写 `board` / `github` 段", SKILL)
        self.assertNotIn("OQ-1 前 init 仍写这两段", SKILL)

    def test_skip_writes_explicit_disabled_entry(self):
        skip = line_containing(SKILL, "用户跳过")
        self.assertIn("显式关闭条目", skip)
        self.assertIn('"enabled": false', skip)

    def test_trigger_is_missing_adapter_key(self):
        self.assertIn("缺对应适配器键", SKILL)
        self.assertNotIn("仅对应段缺失时", SKILL)


class TestAC2RepairBranchMigration(unittest.TestCase):
    def setUp(self):
        self.branch = section(SKILL, "### 1.5 更新/修复分支", "### 2.")

    def test_migration_offered_when_legacy_only(self):
        self.assertIn("代写等价 `sync` 段", self.branch)
        self.assertIn("旧段保留不删", self.branch)

    def test_existing_sync_key_means_zero_action(self):
        self.assertIn("零动作", self.branch)

    def test_validation_step_no_legacy_backfill_wording(self):
        step1 = line_containing(SKILL, "**配置校验**")
        self.assertNotIn("`board` / `github` 段缺失时不在本步补写", step1)
        self.assertIn("sync", step1)


class TestAC3CliZeroDiff(unittest.TestCase):
    def test_cli_untouched_in_change_range(self):
        fm = section(CHANGE, "---", "\n---")
        base = re.search(r"base_commit:\s*([0-9a-f]{7,40})", fm).group(1)
        commits = re.search(r"commits:\s*\[([^\]]*)\]", fm).group(1)
        tail = [c.strip().strip('"') for c in commits.split(",") if c.strip()]
        end = tail[-1] if tail else "HEAD"
        out = subprocess.run(
            ["git", "diff", "--name-only", f"{base}..{end}", "--", "cli/"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(out, "", f"cli/ 在本 change 区间出现 diff: {out}")

    def test_existence_semantics_docstring_intact(self):
        src = (ROOT / "cli" / "eo-sync").read_text(encoding="utf-8")
        self.assertIn("完全以其为准、绝不回落", src)
        self.assertIn("等价映射", src)


class TestAC4DocsCaliber(unittest.TestCase):
    def test_config_marks_legacy_rows(self):
        for needle in ("| `board.enabled`", "| `board.stub_dir`", "| `github.issue`", "| `github.pr`"):
            self.assertIn("legacy", line_containing(CONFIG, needle), needle)

    def test_config_sync_is_first_choice(self):
        self.assertIn("legacy", line_containing(CONFIG, "| `sync`"))
        self.assertIn("首选", CONFIG)

    def test_config_consolidation_done_not_pending(self):
        self.assertNotIn("时机见 change `sync-plugin-layer` 的 OQ-1", CONFIG)
        self.assertIn("sync-config-consolidation", CONFIG)

    def test_board_github_doc_prefers_sync(self):
        self.assertIn("legacy", BG)
        self.assertIn("sync.obsidian", line_containing(BG, "## 一、Obsidian stub 适配器"))
        self.assertIn("sync.github", line_containing(BG, "## 二、GitHub issue"))
        self.assertIn("缺对应适配器键", BG)

    def test_guide_prefers_sync(self):
        self.assertIn("sync.obsidian", line_containing(GUIDE, "├── board/"))
        self.assertNotIn("board.enabled 时自动维护", GUIDE)
        self.assertIn("legacy", section(GUIDE, "## 看板与 GitHub 联动", "## 多项目总览"))

    def test_no_init_still_writes_legacy_residue(self):
        for name, text in (("SKILL", SKILL), ("CONFIG", CONFIG), ("BG", BG), ("GUIDE", GUIDE)):
            self.assertNotIn("仍写这两段", text, name)


class TestAC5DogfoodMigration(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((ROOT / ".eo-project.json").read_text(encoding="utf-8"))

    def test_sync_section_present_and_explicit(self):
        sync = self.cfg.get("sync")
        self.assertIsInstance(sync, dict)
        self.assertEqual(sync["obsidian"]["enabled"], True)
        self.assertEqual(sync["obsidian"]["stub_dir"], "board")
        self.assertEqual(sync["github"]["enabled"], False)

    def test_legacy_sections_retained(self):
        self.assertIn("board", self.cfg)
        self.assertIn("github", self.cfg)

    def test_enabled_set_equivalent_to_legacy_derivation(self):
        eo_sync = load_eo_sync()
        legacy_cfg = {k: v for k, v in self.cfg.items() if k != "sync"}
        current = eo_sync.resolve_enabled(self.cfg)
        derived = eo_sync.resolve_enabled(legacy_cfg)
        self.assertEqual(set(current), set(derived))
        self.assertEqual(current.get("obsidian"), derived.get("obsidian"))


if __name__ == "__main__":
    unittest.main()
