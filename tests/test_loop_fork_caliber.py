"""eo-loop 分叉上报口径静态断言：worker 不问用户但形态分叉须清单上报。

只读两个口径文件（eo-loop/SKILL.md、references/substrates/_template.md），
断言分叉上报机制的四个落点存在：派发纪律的清单上报条款、③节的总控
汇总转达条款、①节的举例措辞判据、_template 派发节的提示位。
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKILL = (ROOT / "eo-loop" / "SKILL.md").read_text(encoding="utf-8")
TEMPLATE = (
    ROOT / "eo-loop" / "references" / "substrates" / "_template.md"
).read_text(encoding="utf-8")


def section(text, start, end):
    if start not in text:
        raise AssertionError(f"找不到节起点 {start!r}")
    seg = text.split(start, 1)[1]
    return seg.split(end, 1)[0] if end in seg else seg


class TestAC1DispatchPromptForkReporting(unittest.TestCase):
    """派发 prompt 纪律：含形态自由度的节点，worker 分叉+假设清单随交付上报。"""

    def setUp(self):
        self.sec = section(SKILL, "**派发 prompt 纪律", "**worker 复用纪律")

    def test_fork_reporting_clause_present(self):
        self.assertIn("形态自由度", self.sec)
        self.assertIn("本应问用户的分叉", self.sec)

    def test_assumptions_reported_as_list_with_delivery(self):
        self.assertIn("所采假设", self.sec)
        self.assertIn("随交付", self.sec)


class TestAC2CoordinatorBatchesForksToUser(unittest.TestCase):
    """③派发与校验裁决：总控攒分叉清单成一次封闭选择转达用户，裁决回灌。"""

    def setUp(self):
        self.sec = section(SKILL, "**③ 派发与校验裁决**", "**④ 收敛判定**")

    def test_batched_closed_choice_to_user(self):
        self.assertIn("分叉清单", self.sec)
        self.assertIn("封闭选择", self.sec)

    def test_ruling_flows_back_with_revision(self):
        self.assertIn("回灌", self.sec)


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
    """_template.md 派发节：分叉清单提示位。"""

    def test_template_has_fork_hint(self):
        sec = section(TEMPLATE, "## 派发", "## 等待与观测")
        self.assertIn("分叉", sec)


if __name__ == "__main__":
    unittest.main()
