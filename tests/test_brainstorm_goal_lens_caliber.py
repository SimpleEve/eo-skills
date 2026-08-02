"""Brainstorming Goal Lens 静态口径断言。

只读共享目标契约与 brainstorming 的 skill、工具箱、记录模板，确保七维
按覆盖镜头使用、Proof 阶段边界清晰、Research Gate 有界且连到决策。
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONTRACT = (ROOT / "eo-shared" / "goal-contract.md").read_text(encoding="utf-8")
QUESTIONING = (ROOT / "eo-shared" / "questioning.md").read_text(encoding="utf-8")
SKILL = (ROOT / "eo-brainstorming" / "SKILL.md").read_text(encoding="utf-8")
TOOLKITS = (
    ROOT / "eo-brainstorming" / "references" / "question-toolkits.md"
).read_text(encoding="utf-8")
TEMPLATE = (
    ROOT / "eo-brainstorming" / "references" / "record-template.md"
).read_text(encoding="utf-8")


def section(text, start, end):
    if start not in text:
        raise AssertionError(f"找不到节起点 {start!r}")
    segment = text.split(start, 1)[1]
    return segment.split(end, 1)[0] if end in segment else segment


def line_containing(text, needle):
    return next((line for line in text.splitlines() if needle in line), "")


class TestAC1CoverageLensNotQuestionnaire(unittest.TestCase):
    def test_shared_contract_rejects_forced_seven_questions(self):
        principle = section(CONTRACT, "## 使用原则", "## 七维投影")
        self.assertIn("coverage lens", principle)
        self.assertIn("不是强制七问", principle)
        self.assertIn("无关维度可以不渲染", principle)

    def test_skill_only_surfaces_high_impact_gaps(self):
        lens = section(SKILL, "### Goal Lens", "### Research Gate")
        self.assertIn("不是七问清单", lens)
        self.assertIn("高影响缺口", lens)
        self.assertIn("提问预算", lens)

    def test_record_is_not_fixed_to_seven_sections(self):
        self.assertIn("不要为了凑齐 Goal Lens 固定成七段", TEMPLATE)


class TestAC2ProofStageBoundaries(unittest.TestCase):
    def test_contract_splits_proof_into_three_layers(self):
        proof = section(CONTRACT, "## Proof 的三层边界", "## 阶段权责")
        self.assertIn("决策依据", proof)
        self.assertIn("证明义务", proof)
        self.assertIn("交付证据", proof)

    def test_brainstorming_cannot_claim_delivery_pass(self):
        lens = section(SKILL, "### Goal Lens", "### Research Gate")
        self.assertIn("不得宣告交付 PASS", lens)
        self.assertIn("implement/test/review/manual", lens)


class TestAC3ConditionalResearchGate(unittest.TestCase):
    def setUp(self):
        self.gate = section(SKILL, "### Research Gate", "### 三层追问法")

    def test_research_only_when_fact_can_flip_decision(self):
        self.assertIn("翻转方向选择", self.gate)
        self.assertIn("无法从当前仓库", self.gate)
        self.assertIn("有界回答", self.gate)

    def test_research_is_bounded_and_decision_linked(self):
        self.assertIn("1-3 个会翻转决策的命题", self.gate)
        self.assertIn("影响哪项决策", self.gate)
        self.assertIn("足以区分候选方向即停止", self.gate)
        self.assertIn("逐项区分已验证事实、推断和仍未知内容", self.gate)
        self.assertIn("必须显式列为 Unknown 并给出去向", self.gate)

    def test_durable_research_uses_shared_sot(self):
        self.assertIn("<project_root>/research/", self.gate)
        self.assertIn("../eo-shared/research.md", self.gate)


class TestAC4RemainingDimensionsAreActionable(unittest.TestCase):
    def test_skill_covers_outcome_false_success_bounds_trade_unknown(self):
        lens = section(SKILL, "### Goal Lens", "### Research Gate")
        for term in ("Outcome", "False Success", "Bounds", "Trade", "Unknown"):
            with self.subTest(term=term):
                self.assertIn(term, lens)

    def test_toolkit_keeps_lens_conditional(self):
        hints = section(TOOLKITS, "## Goal Lens 补缺提示", "## 典型 upstream")
        self.assertIn("只在对应信息缺失且会改变结论时使用", hints)
        self.assertIn("执行期 A-B-C 权限分流", hints)

    def test_template_routes_unknowns(self):
        self.assertIn("现在查清 / 调研后再决 / defer / 执行期 A-B-C", TEMPLATE)
        self.assertIn("证据未知不得包装成已钉结论", TEMPLATE)


class TestAC5DecisionFlipQuestionRouting(unittest.TestCase):
    def setUp(self):
        self.selector = section(SKILL, "### 决策翻转排序", "### Research Gate")
        self.workflow = section(
            SKILL, "### 第二步：对话循环", "### 第三步：收敛决策"
        )
        self.gate = section(SKILL, "### Research Gate", "### 三层追问法")

    def test_selector_preserves_contract_mapping_and_outcome_priority(self):
        projection = section(CONTRACT, "## 七维投影", "## Proof 的三层边界")
        self.assertIn("| Done | Outcome |", projection)
        self.assertIn("| Proof | Evidence |", projection)
        self.assertIn("`Done` 仍映射 Outcome", self.selector)
        self.assertIn("`Proof` 仍映射 Evidence", self.selector)
        mode_rule = line_containing(self.selector, "受众、角色或表现偏好")
        self.assertIn("塑形模式", mode_rule)
        self.assertIn("优先钉 Outcome", mode_rule)
        self.assertIn("只有在会改变上述结论时才提前", mode_rule)
        self.assertIn("当前回复不渲染", mode_rule)
        self.assertIn("只有当前推荐确实依赖", mode_rule)
        self.assertIn("不让画像完整度压过核心体验", mode_rule)
        proxy_rule = line_containing(self.selector, "Outcome 尚未钉住时")
        self.assertIn("受众 / 角色不得成为首问", proxy_rule)
        self.assertIn("可观察体验或成功信号之间选择", proxy_rule)
        self.assertIn("无法脱离具体受众定义候选 Outcome", proxy_rule)

    def test_complete_context_allows_zero_questions(self):
        zero_rule = line_containing(self.selector, "信息已覆盖所有")
        self.assertIn("本轮 0 问", zero_rule)
        self.assertIn("不得为走完 Goal Lens", zero_rule)
        self.assertIn("不再补问宽泛的「还有遗漏吗」", self.selector)
        coverage_rule = line_containing(QUESTIONING, "信息充分则用总结确认")
        self.assertIn("不强行追加问题", coverage_rule)
        self.assertIn("信息充分 → 0 问", self.workflow)
        self.assertNotIn("用户抛想法 → 复述确认 + 追问动机层", self.workflow)

    def test_multiple_gaps_only_ask_highest_flip_item(self):
        rank_rule = line_containing(self.selector, "多个高影响缺口")
        self.assertIn("只问翻转力最高的一项", rank_rule)
        self.assertIn("其余保留在未钉池", rank_rule)
        self.assertIn("不打包追问", rank_rule)

    def test_factual_gap_routes_to_research_not_user_question(self):
        route_rule = line_containing(self.gate, "可核查的事实命题")
        self.assertIn("不向用户索要事实判断", route_rule)
        self.assertIn("先按 questioning §1 自查", route_rule)
        self.assertIn("进入 Research Gate", route_rule)
        fallback_rule = line_containing(self.gate, "未进入 Research Gate")
        self.assertIn("Unknown / defer", fallback_rule)
        self.assertIn("不得标为已钉", fallback_rule)

    def test_fatigue_signal_does_not_open_another_menu(self):
        ledger = section(SKILL, "### 决策台账", "### 推荐与建议")
        fatigue_rule = line_containing(ledger, "疲劳信号按 questioning §5")
        self.assertIn("立即停止提问", fatigue_rule)
        self.assertIn("不弹菜单", fatigue_rule)


if __name__ == "__main__":
    unittest.main()
