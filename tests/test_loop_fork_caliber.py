"""eo-loop Unknown 上报口径静态断言：仅 A 类可先做后报。

只读两个口径文件（eo-loop/SKILL.md、references/substrates/_template.md），
断言 A 类交付留痕、B/C 变更前决策门、总控汇总 B 类、举例措辞判据
和基底求裁决信号提示位。
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


class TestAC1DispatchPromptUnknownAuthority(unittest.TestCase):
    """派发 prompt 纪律：仅 A 随交付，B/C 必须在变更前求裁决。"""

    def setUp(self):
        self.sec = section(SKILL, "**派发 prompt 纪律", "**worker 复用纪律")

    def test_only_a_is_reported_with_delivery(self):
        self.assertIn("仅 A 类", self.sec)
        self.assertIn("随交付记录", self.sec)
        self.assertNotIn("本应问用户的分叉 + 各自所采假设", self.sec)

    def test_b_and_c_gate_before_mutation(self):
        self.assertIn("B / C 类", self.sec)
        self.assertIn("须变更前求裁决", self.sec)
        self.assertNotIn("先采假设、交付后再问", self.sec)


class TestAC2CoordinatorRoutesUnknowns(unittest.TestCase):
    """③派发、路由与风险升级：A 留痕、B 合并选择、C 立即上交。"""

    def setUp(self):
        self.sec = section(SKILL, "**条件式 Execution Guard**", "**② 选基底**")

    def test_batched_closed_choice_to_user(self):
        self.assertIn("A 类", self.sec)
        self.assertIn("允许 worker 先做后报", self.sec)
        self.assertIn("B 类", self.sec)
        self.assertIn("合并成一次封闭选择", self.sec)
        self.assertIn("C 类", self.sec)
        self.assertIn("立即上交用户", self.sec)

    def test_affected_branch_pauses_before_ruling(self):
        self.assertIn("变更前发求裁决信号并暂停受影响分支", self.sec)
        self.assertIn("总控把同窗 B 类合并成一次封闭选择交用户", self.sec)


class TestAC3ExampleWordingIsNotFinal(unittest.TestCase):
    """①圈线段：「比如/之类」等举例措辞 = 形态未定稿，先探针再派。"""

    def setUp(self):
        self.sec = section(SKILL, "**① 圈线段**", "**② 选基底**")

    def test_example_wording_judged_undecided(self):
        self.assertIn("举例措辞", self.sec)
        self.assertIn("比如", self.sec)

    def test_probe_before_dispatch(self):
        self.assertIn("探针", self.sec)


class TestAC4TemplateDispatchSlot(unittest.TestCase):
    """_template.md 派发节：基底必须提供 B/C 求裁决信号。"""

    def test_template_has_fork_hint(self):
        sec = section(TEMPLATE, "## 派发", "## 等待与观测")
        self.assertIn("仅 A 类可随交付记录", sec)
        self.assertIn("B / C 类必须在变更前", sec)
        self.assertIn("求裁决", sec)

    def test_every_runtime_substrate_exposes_decision_gate(self):
        self.assertGreaterEqual(len(SUBSTRATES), 3)
        for name, text in SUBSTRATES.items():
            dispatch = section(text, "## 派发", "## 等待与观测")
            with self.subTest(substrate=name):
                self.assertIn("A 类", dispatch)
                self.assertIn("B / C 类", dispatch)
                self.assertTrue(
                    "求裁决" in dispatch or "decision_gate" in dispatch,
                    f"{name} 未提供 B/C 求裁决信号",
                )


if __name__ == "__main__":
    unittest.main()
