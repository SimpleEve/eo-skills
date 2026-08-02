"""eo-loop 风险触发式核查口径静态断言。

锁定正常交付只消费路由事实、无抽查或信任分层、仅客观风险信号升级、
升级范围不外溢，以及三种执行基底遵循同一回收边界。
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = (ROOT / "eo-loop" / "SKILL.md").read_text(encoding="utf-8")
TEMPLATE = (
    ROOT / "eo-loop" / "references" / "substrates" / "_template.md"
).read_text(encoding="utf-8")
SUBSTRATES = {
    path.name: path.read_text(encoding="utf-8")
    for path in (ROOT / "eo-loop" / "references" / "substrates").glob("*.md")
    if path.name != "_template.md"
}


def section(text, start, end):
    if start not in text:
        raise AssertionError(f"找不到节起点 {start!r}")
    seg = text.split(start, 1)[1]
    return seg.split(end, 1)[0] if end in seg else seg


class TestNormalRouteHasNoAudit(unittest.TestCase):
    def setUp(self):
        self.dispatch = section(
            SKILL, "**③ 派发、路由与风险升级**", "**④ 收敛判定**"
        )

    def test_normal_delivery_only_consumes_route_facts(self):
        for marker in (
            "默认只读取",
            "frontmatter 当前状态",
            "预期工件指针",
            "当前交付基线",
            "最新结构化处置",
            "无风险即推进",
        ):
            self.assertIn(marker, self.dispatch)
        for marker in ("不打开完整 diff", "不重跑节点命令", "不重新判断"):
            self.assertIn(marker, self.dispatch)

    def test_first_or_cross_agent_delivery_does_not_trigger_sampling(self):
        for marker in (
            "交付来自其他 agent",
            "worker 首次参与",
            "新的可用基底",
            "不是风险信号",
            "首次抽查",
            "随机抽查",
            "按比例抽查",
            "worker 信任分层",
        ):
            self.assertIn(marker, self.dispatch)

    def test_old_blanket_verification_contract_is_absent(self):
        for marker in (
            "**③ 派发与校验裁决**",
            "先校验、再裁决",
            "四项基本检查",
            "绝不直接采信",
        ):
            self.assertNotIn(marker, SKILL)


class TestObjectiveRiskSignals(unittest.TestCase):
    def setUp(self):
        self.dispatch = section(
            SKILL, "**③ 派发、路由与风险升级**", "**④ 收敛判定**"
        )

    def test_signals_are_observable_and_explicit(self):
        for marker in (
            "可指认的风险信号",
            "互相冲突",
            "工件或字段缺失",
            "基线过期",
            "越过角色权限",
            "计划外变化",
            "Unknown B / C",
            "阻塞或决策门",
        ):
            self.assertIn(marker, self.dispatch)
        self.assertIn("主观不信任或“以防万一”不构成信号", self.dispatch)

    def test_escalation_is_targeted_and_role_owned(self):
        for marker in (
            "只处理触发信号对应的范围",
            "不扩张为全面核查",
            "派对应有权节点",
            "停下上交用户",
            "风险消除后回到正常路由",
        ):
            self.assertIn(marker, self.dispatch)


class TestSubstrateConsistency(unittest.TestCase):
    def test_template_requires_route_first_collection(self):
        collect = section(TEMPLATE, "## 回收", "## 已知陷阱")
        for marker in (
            "路由事实",
            "不抽查",
            "不复做节点内容",
            "客观风险信号",
            "对应异常",
        ):
            self.assertIn(marker, collect)

    def test_every_runtime_substrate_uses_the_same_boundary(self):
        self.assertGreaterEqual(len(SUBSTRATES), 3)
        for name, text in SUBSTRATES.items():
            collect = section(text, "## 回收", "## 已知陷阱")
            with self.subTest(substrate=name):
                for marker in (
                    "正常路径",
                    "直接路由",
                    "不抽查或复做节点内容",
                    "客观风险信号",
                    "对应异常升级",
                ):
                    self.assertIn(marker, collect)
                self.assertNotIn("不采信", collect)


if __name__ == "__main__":
    unittest.main()
