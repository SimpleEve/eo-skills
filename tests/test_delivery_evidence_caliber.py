"""交付证据面与回复契约硬步骤的静态口径断言。

锁定 eo-shared/evidence.md 与 eo-shared/reply-contract.md 两个单一来源，
以及其在 eo-implement / eo-archive / eo-loop / eo-fix / eo-project-init
五个消费方正文中的硬性引用（防漂移）。
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = (ROOT / "eo-shared" / "evidence.md").read_text(encoding="utf-8")
REPLY = (ROOT / "eo-shared" / "reply-contract.md").read_text(encoding="utf-8")
README = (ROOT / "eo-shared" / "README.md").read_text(encoding="utf-8")
IMPLEMENT = (ROOT / "eo-implement" / "SKILL.md").read_text(encoding="utf-8")
ARCHIVE = (ROOT / "eo-archive" / "SKILL.md").read_text(encoding="utf-8")
LOOP = (ROOT / "eo-loop" / "SKILL.md").read_text(encoding="utf-8")
FIX = (ROOT / "eo-fix" / "SKILL.md").read_text(encoding="utf-8")
INIT = (ROOT / "eo-project-init" / "SKILL.md").read_text(encoding="utf-8")

CONTRACT_LINES = [
    "1. **做了什么**——行为变化，不是 diff 清单",
    "2. **为什么这么做**——关键决策与理由，被否掉的方案一并点名",
    "3. **主要产出**——文件 / 功能 / 命令，用户去哪看、怎么验",
    "4. **遇到的问题与解法**——没有就明说「无」",
    "受众分两层：对开发者讲接口与路径，对需求方讲行为与结果。一句一事，不铺陈过程。",
]


class TestEvidenceSpec(unittest.TestCase):
    def test_three_mandatory_sections(self):
        for marker in ("入口与环境", "过程证据", "怎么验"):
            self.assertIn(marker, EVIDENCE)

    def test_every_change_produces_no_manual_prerequisite(self):
        self.assertIn("每个 change 必产", EVIDENCE)
        self.assertIn("不以人工 AC 为前提", EVIDENCE)
        self.assertIn("最薄形态", EVIDENCE)

    def test_four_builtin_presets_and_project_override(self):
        for preset in ("web", "cli", "service", "library"):
            self.assertIn(preset, EVIDENCE)
        self.assertIn("eo-doc/templates/", EVIDENCE)
        self.assertIn("evidence-<type>.md", EVIDENCE)
        self.assertIn("命中优先于出厂预设", EVIDENCE)

    def test_screenshot_discipline(self):
        self.assertIn("shots/", EVIDENCE)
        self.assertIn("随归档冻结进 git", EVIDENCE)
        self.assertIn("UI 变化的批末自验必留截图", EVIDENCE)

    def test_refresh_and_lifecycle(self):
        self.assertIn("刷新与失效", EVIDENCE)
        self.assertIn("acceptance.md](acceptance.md)「失效与重置」", EVIDENCE)
        for marker in ("eo-implement 全部完成", "eo-archive（硬门）", "eo-loop"):
            self.assertIn(marker, EVIDENCE)
        self.assertIn("不静默放行", EVIDENCE)


class TestReplyContractSpec(unittest.TestCase):
    def test_contract_body(self):
        for line in CONTRACT_LINES:
            self.assertIn(line, REPLY)

    def test_dual_channels(self):
        self.assertIn("生效通道", REPLY)
        self.assertIn("eo-reply-contract", REPLY)
        self.assertIn("被动上下文", REPLY)
        self.assertIn("硬步骤", REPLY)

    def test_readme_registers_both(self):
        self.assertIn("[evidence.md](evidence.md)", README)
        self.assertIn("[reply-contract.md](reply-contract.md)", README)


class TestImplementIntegration(unittest.TestCase):
    def test_evidence_generated_regardless_of_manual_ac(self):
        self.assertIn("无论有无人工项", IMPLEMENT)
        self.assertIn("../eo-shared/evidence.md", IMPLEMENT)
        self.assertIn("eo-doc/templates/evidence-*.md", IMPLEMENT)

    def test_batch_checkpoint_screenshots(self):
        self.assertIn("UI 变化留截图", IMPLEMENT)
        self.assertIn("shots/", IMPLEMENT)

    def test_report_carries_evidence_path(self):
        self.assertIn("交付证据面：<evidence.md 路径>", IMPLEMENT)


class TestArchiveIntegration(unittest.TestCase):
    def test_evidence_hard_gate(self):
        self.assertIn("交付证据面核对", ARCHIVE)
        self.assertIn("三段非空", ARCHIVE)
        for marker in ("补齐", "显式豁免", "终止归档"):
            self.assertIn(marker, ARCHIVE)

    def test_delivery_report_before_confirmation(self):
        self.assertIn("归档前先发交付汇报", ARCHIVE)
        self.assertIn("回复契约四条", ARCHIVE)
        self.assertIn("证据面渲染", ARCHIVE)
        self.assertIn("同条消息", ARCHIVE)
        self.assertIn("../eo-shared/reply-contract.md", ARCHIVE)

    def test_constraint_rows(self):
        self.assertIn("证据面硬门", ARCHIVE)
        self.assertIn("交付汇报硬步骤", ARCHIVE)


class TestLoopIntegration(unittest.TestCase):
    def test_convergence_is_delivery_report(self):
        self.assertIn("收敛即交付汇报", LOOP)
        self.assertIn("../eo-shared/reply-contract.md", LOOP)
        self.assertIn("evidence.md", LOOP)
        self.assertIn("不得只有三行归档速报", LOOP)

    def test_constraint_row(self):
        self.assertIn("收尾必发交付汇报", LOOP)


class TestFixIntegration(unittest.TestCase):
    def test_evidence_refresh_on_fix(self):
        # 落点记账与循环内分支各引用一次；每次引用 = 链接文本 + 链接目标两处字符串
        self.assertEqual(FIX.count("../eo-shared/evidence.md"), 4)
        self.assertIn("刷新与失效", FIX)


class TestInitInjectionSameSource(unittest.TestCase):
    def test_init_declares_single_source(self):
        self.assertIn("../eo-shared/reply-contract.md", INIT)
        self.assertIn("单一来源", INIT)

    def test_injection_body_matches_contract_verbatim(self):
        for line in CONTRACT_LINES:
            self.assertIn(line, INIT)


if __name__ == "__main__":
    unittest.main()
