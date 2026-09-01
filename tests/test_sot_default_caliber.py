"""SoT 口径静态断言：init 一律 local（无模式询问）且管理侧随仓库提交。

只读四个口径文件（eo-project-init/SKILL.md、references/config.md、
docs/GUIDE.md、README.md），断言现行口径锚点存在、vault 残留清零。
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKILL = (ROOT / "eo-project-init" / "SKILL.md").read_text(encoding="utf-8")
CONFIG = (ROOT / "eo-project-init" / "references" / "config.md").read_text(encoding="utf-8")
GUIDE = (ROOT / "docs" / "GUIDE.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def section(text, start, end):
    if start not in text:
        raise AssertionError(f"找不到节起点 {start!r}")
    seg = text.split(start, 1)[1]
    return seg.split(end, 1)[0] if end in seg else seg


def line_containing(text, needle):
    return next(l for l in text.splitlines() if needle in l)


class TestAlwaysLocalOnly(unittest.TestCase):
    def test_no_mode_question(self):
        self.assertNotIn("询问运行模式", SKILL)
        self.assertNotIn("运行模式偏好", SKILL)

    def test_project_root_is_repo_local(self):
        self.assertIn("`<repo>/.eo-project/`", SKILL)

    def test_config_example_writes_local_mode(self):
        # cli 校验 mode 必填，init 照写 "local"，但不再构成选择
        self.assertIn('"mode": "local"', SKILL)
        self.assertIn('"mode": "local"', CONFIG)

    def test_no_user_level_mode_config(self):
        # init 不读用户级配置推断模式
        self.assertNotIn("default_mode", SKILL)
        self.assertNotIn("default_mode", CONFIG)


class TestManagementSideCommitted(unittest.TestCase):
    def setUp(self):
        self.sec = section(SKILL, "### 8. 处理 `.eo-project/`", "### 9.")

    def test_section_defaults_to_committed(self):
        self.assertNotIn("默认追加到 `.gitignore`", self.sec)
        self.assertIn("缺省随仓库提交", self.sec)

    def test_optout_preserved(self):
        # 用户明确不想提交时仍可当场选择追加 ignore
        self.assertIn("明确", self.sec)
        self.assertIn(".eo-project/", self.sec)

    def test_constraints_committed(self):
        constraints = section(SKILL, "## 约束", "\x00")
        self.assertNotIn("`.eo-project/` 默认进 `.gitignore`", constraints)
        self.assertIn("缺省随仓库提交", constraints)


class TestRepairBranchZeroTouch(unittest.TestCase):
    def setUp(self):
        self.step4 = line_containing(SKILL, ".gitignore 核对")

    def test_repair_branch_does_not_backfill_ignore(self):
        self.assertNotIn("（local 模式）`.eo-project/`", self.step4)

    def test_repair_branch_states_zero_touch(self):
        # 双向零改动：已 ignore 不删行、未 ignore 不补写
        self.assertIn("保持现状", self.step4)


class TestNoVaultResidue(unittest.TestCase):
    FILES = [
        ("eo-project-init/SKILL.md", SKILL),
        ("eo-project-init/references/config.md", CONFIG),
        ("docs/GUIDE.md", GUIDE),
        ("README.md", README),
    ]

    def test_no_vault_mention(self):
        for name, text in self.FILES:
            self.assertNotIn("vault", text.lower(), name)

    def test_no_default_ignore_wording_near_eo_project_dir(self):
        for name, text in self.FILES:
            for i, line in enumerate(text.splitlines(), 1):
                if ".eo-project/" in line and ".eo-project.local" not in line:
                    self.assertNotIn("默认进", line, f"{name}:{i} 旧口径残留: {line}")
                    self.assertNotIn("默认追加", line, f"{name}:{i} 旧口径残留: {line}")

    def test_config_states_committed(self):
        self.assertIn("缺省随仓库提交", CONFIG)

    def test_guide_states_committed(self):
        self.assertIn("缺省随仓库提交", GUIDE)
        self.assertNotIn("（默认进 `.gitignore`）", GUIDE)

    def test_readme_collab_committed(self):
        self.assertIn("随仓库提交", README)

    def test_local_override_always_ignored(self):
        self.assertIn("`.eo-project.local.json` **始终**进 `.gitignore`", SKILL)


if __name__ == "__main__":
    unittest.main()
