"""SoT 默认口径静态断言：新项目默认 local 且管理侧随仓库提交。

只读四个口径文件（eo-project-init/SKILL.md、references/config.md、
docs/GUIDE.md、README.md），断言新口径锚点存在、旧口径残留清零。
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


class TestAC1LocalIsDefaultRecommendation(unittest.TestCase):
    def setUp(self):
        self.sec2 = section(SKILL, "询问运行模式", "### 3.")

    def test_no_anti_local_directive(self):
        self.assertNotIn("不要直接默认到 local", SKILL)

    def test_local_recommended_by_default(self):
        self.assertIn("缺省推荐 local", self.sec2)
        # 用户级显式配置仍作推荐项尊重
        self.assertIn("default_mode", self.sec2)

    def test_local_option_says_committed(self):
        self.assertIn("缺省随仓库提交", self.sec2)

    def test_vault_still_optional(self):
        self.assertIn("vault 模式", self.sec2)
        self.assertIn("local 模式", self.sec2)

    def test_default_mode_not_inferred_from_vault_root_alone(self):
        # config.md：default_mode 缺省 local，不再仅凭 vault_root 存在推断 vault
        row = line_containing(CONFIG, "| `default_mode`")
        self.assertNotIn("推断", row)
        self.assertIn("local", row)


class TestAC2NoDefaultGitignore(unittest.TestCase):
    def setUp(self):
        self.sec10 = section(SKILL, "### 10. 处理 `.eo-project/`", "### 11.")

    def test_section10_defaults_to_committed(self):
        self.assertNotIn("默认追加到 `.gitignore`", self.sec10)
        self.assertIn("缺省随仓库提交", self.sec10)

    def test_section10_optout_preserved(self):
        # 用户明确不想提交时仍可当场选择追加 ignore
        self.assertIn("明确", self.sec10)
        self.assertIn(".eo-project/", self.sec10)

    def test_constraints_flipped(self):
        constraints = section(SKILL, "## 约束", "\x00")
        self.assertNotIn("`.eo-project/` 默认进 `.gitignore`", constraints)
        self.assertIn("缺省随仓库提交", constraints)


class TestAC3ExistingProjectsUntouched(unittest.TestCase):
    def setUp(self):
        self.step4 = line_containing(SKILL, ".gitignore 与软链核对")

    def test_repair_branch_does_not_backfill_ignore(self):
        self.assertNotIn("（local 模式）`.eo-project/`", self.step4)

    def test_repair_branch_states_zero_touch(self):
        # 双向零改动：已 ignore 不删行、未 ignore 不补写
        self.assertIn("保持现状", self.step4)


class TestAC4NoOldCaliberResidue(unittest.TestCase):
    FILES = [
        ("eo-project-init/SKILL.md", SKILL),
        ("eo-project-init/references/config.md", CONFIG),
        ("docs/GUIDE.md", GUIDE),
        ("README.md", README),
    ]

    def test_no_default_ignore_wording_near_eo_project_dir(self):
        for name, text in self.FILES:
            for i, line in enumerate(text.splitlines(), 1):
                if ".eo-project/" in line and ".eo-project.local" not in line:
                    self.assertNotIn("默认进", line, f"{name}:{i} 旧口径残留: {line}")
                    self.assertNotIn("默认追加", line, f"{name}:{i} 旧口径残留: {line}")

    def test_config_table_new_caliber(self):
        self.assertIn("缺省随仓库提交", CONFIG)

    def test_guide_table_new_caliber(self):
        self.assertIn("缺省随仓库提交", GUIDE)
        self.assertNotIn("（默认进 `.gitignore`）", GUIDE)

    def test_readme_collab_new_caliber(self):
        self.assertIn("随仓库提交", README)

    def test_vault_mode_untouched(self):
        # vault 侧口径不动：软链 gitignore 与 local 覆盖文件不提交约定保持
        self.assertIn("# eo-project vault link", SKILL)
        self.assertIn("`.eo-project.local.json` **始终**进 `.gitignore`", SKILL)
        self.assertIn("<vault_root>/<projects_subdir>/<project_name>/", SKILL)


if __name__ == "__main__":
    unittest.main()
