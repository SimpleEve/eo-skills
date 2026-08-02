"""eo-loop 条件式 Execution Guard 的静态口径断言。

只读共享目标契约、eo-loop/SKILL.md 与基底模板，锁定条件触发、
无第二真相源、Unknown/Trade 单一来源及回收反作弊边界。
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = (ROOT / "eo-shared" / "goal-contract.md").read_text(encoding="utf-8")
SHARED_README = (ROOT / "eo-shared" / "README.md").read_text(encoding="utf-8")
SKILL = (ROOT / "eo-loop" / "SKILL.md").read_text(encoding="utf-8")
TEMPLATE = (
    ROOT / "eo-loop" / "references" / "substrates" / "_template.md"
).read_text(encoding="utf-8")


def section(text, start, end):
    if start not in text:
        raise AssertionError(f"找不到节起点 {start!r}")
    seg = text.split(start, 1)[1]
    return seg.split(end, 1)[0] if end in seg else seg


class TestConditionalExecutionGuard(unittest.TestCase):
    def setUp(self):
        self.guard = section(SKILL, "**条件式 Execution Guard**", "**② 选基底**")

    def test_only_triggered_by_risky_or_open_execution(self):
        for marker in ("长程", "并行", "无人值守", "高风险", "开放未知"):
            self.assertIn(marker, self.guard)
        self.assertIn("未命中条件", self.guard)

    def test_compiled_from_existing_sot_without_persisting(self):
        for marker in ("change.md", "review/test 台账", "Git 基线", "用户本轮授权"):
            self.assertIn(marker, self.guard)
        self.assertIn("每个节点派发前", self.guard)
        self.assertIn("不写 `PROGRESS.md`", self.guard)
        self.assertIn("不新增任何第二真相源", self.guard)

    def test_unconfirmed_goal_cannot_dispatch_delivery_nodes(self):
        self.assertIn("标明「未冻结」", self.guard)
        self.assertIn(
            "不得据此派发 eo-implement / eo-test / eo-review / eo-archive",
            self.guard,
        )
        self.assertIn("confirmed change", self.guard)

    def test_runtime_authorization_cannot_move_frozen_goalposts(self):
        self.assertIn("只能收紧运行边界", self.guard)
        self.assertIn("不得直接覆盖", self.guard)
        self.assertIn("change revision", self.guard)


class TestUnknownAuthorityAndTrade(unittest.TestCase):
    def setUp(self):
        self.guard = section(SKILL, "**条件式 Execution Guard**", "**② 选基底**")
        self.unknown = section(CONTRACT, "## Unknown 分流", "\x00")
        self.a_rule = next(
            line for line in self.unknown.splitlines() if "**A 类（可自治）**" in line
        )
        self.c_rule = next(
            line for line in self.unknown.splitlines() if "**C 类（硬决策门）**" in line
        )
        self.trade = section(
            CONTRACT, "## Trade 的默认裁决顺序", "## Unknown 分流"
        )

    def test_only_a_may_act_then_report(self):
        for marker in ("Why", "范围", "架构", "预算", "人工门"):
            self.assertIn(marker, self.a_rule)
        self.assertIn("只有 A 类允许先做后报", self.unknown)
        self.assertIn("goal-contract 为唯一来源", self.guard)
        self.assertIn("A 类", self.guard)
        self.assertIn("允许 worker 先做后报", self.guard)
        self.assertIn("B 类", self.guard)
        self.assertIn("变更前发求裁决信号", self.guard)
        self.assertIn("C 类", self.guard)
        self.assertIn("变更前立即发求裁决信号", self.guard)

    def test_c_hard_gate_covers_every_frozen_or_hard_boundary(self):
        for marker in (
            "Why",
            "范围",
            "AC",
            "架构",
            "外部契约",
            "数据",
            "权限",
            "预算",
            "人工门",
            "硬约束",
            "不可逆动作",
        ):
            self.assertIn(marker, self.c_rule)

    def test_unknown_evidence_is_bounded_and_fail_closed(self):
        self.assertIn("只允许一次有界探测", self.guard)
        self.assertIn("时间 / 调用预算", self.guard)
        self.assertIn("fail-closed", self.guard)
        self.assertIn("不得写 PASS", self.guard)

    def test_trade_order_is_frozen(self):
        for marker in (
            "1. 安全、权限、人工门、熔断等硬约束",
            "2. 已冻结的 Why、Bounds 与 AC",
            "3. 判定和证据完整性",
            "4. 最小改动与可逆性",
            "5. 速度、成本与并行效率",
        ):
            self.assertIn(marker, self.trade)
        self.assertIn("Trade 的默认裁决顺序", self.guard)
        self.assertNotIn("硬约束 > 冻结的 Why", self.guard)

    def test_shared_contract_is_indexed_and_referenced(self):
        self.assertIn("[goal-contract.md](goal-contract.md)", SHARED_README)
        self.assertIn("../eo-shared/goal-contract.md", self.guard)


class TestCollectionIntegrity(unittest.TestCase):
    def setUp(self):
        self.dispatch = section(
            SKILL, "**③ 派发与校验裁决**", "**④ 收敛判定**"
        )

    def test_integrity_checks_cover_common_gaming(self):
        for marker in (
            "自检不得冒充",
            "弱化测试 / judge",
            "样例硬编码",
            "吞错",
            "包装成 PASS",
        ):
            self.assertIn(marker, self.dispatch)

    def test_rejection_does_not_expand_coordinator_role(self):
        self.assertIn("总控不得", self.dispatch)
        for role in ("亲自实施", "执行 eo-test", "兼任 eo-review"):
            self.assertIn(role, self.dispatch)
        self.assertIn("默认派独立 eo-review 审判据与 diff", self.dispatch)
        self.assertIn("执行证据时派 eo-test", self.dispatch)
        self.assertIn("两类同时存在可在同一基线上并行", self.dispatch)

    def test_substrate_template_carries_but_does_not_store_guard(self):
        dispatch = section(TEMPLATE, "## 派发", "## 等待与观测")
        self.assertIn("Execution Guard", dispatch)
        self.assertIn("不另行落盘", dispatch)


if __name__ == "__main__":
    unittest.main()
