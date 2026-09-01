"""修复路径统一的静态口径断言。

循环内 test/review/acceptance 反馈的修复归 /eo-fix 循环内分支（原 impl worker
执行，skill ≠ worker）；eo-implement 模式二退场、全仓无残留；深挖补链路变体
「全链审查」（枚举可死点 + 逐点恢复证明）；eo-loop 打地鼠信号命中即停、交用户裁决。
"""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


FIX = read("eo-fix/SKILL.md")
IMPLEMENT = read("eo-implement/SKILL.md")
LOOP = read("eo-loop/SKILL.md")
CONVENTIONS = read("eo-shared/conventions.md")
INVESTIGATION = read("eo-fix/references/investigation.md")

SKILL_TEXTS = [
    "eo-fix/SKILL.md",
    "eo-implement/SKILL.md",
    "eo-loop/SKILL.md",
    "eo-test/SKILL.md",
    "eo-review/SKILL.md",
    "eo-change/SKILL.md",
    "eo-archive/SKILL.md",
    "eo-shared/conventions.md",
    "eo-shared/acceptance.md",
    "eo-change/references/change-template.md",
    "eo-test/references/test-template.md",
    "eo-review/references/review-template.md",
    "eo-loop/references/substrates/orca-orchestration.md",
    "eo-loop/references/substrates/claude-subagent.md",
    "eo-loop/references/substrates/codex-subagent.md",
]


def section(text, start, end):
    if start not in text:
        raise AssertionError(f"找不到节起点 {start!r}")
    seg = text.split(start, 1)[1]
    if end not in seg:
        raise AssertionError(f"找不到节终点 {end!r}")
    return seg.split(end, 1)[0]


def line_containing(text, marker):
    try:
        return next(line for line in text.splitlines() if marker in line)
    except StopIteration as exc:
        raise AssertionError(f"找不到包含 {marker!r} 的行") from exc


class TestFixAbsorbsInLoopRepair(unittest.TestCase):
    """循环内修复归 eo-fix 循环内分支；impl 模式二退场、全仓无残留。"""

    def test_no_mode2_residue_anywhere(self):
        for rel in SKILL_TEXTS:
            with self.subTest(file=rel):
                self.assertNotIn("模式二", read(rel))

    def test_fix_branch_defines_in_loop_entry(self):
        branch = section(FIX, "## 循环内分支（implement-test-review 反馈修复）", "### 卡点检查子流程")
        for marker in (
            "原 impl worker",
            "免定位",
            "分诊三路由原样生效",
            "全链审查",
            "报告的未决清单",
        ):
            self.assertIn(marker, branch)

    def test_fix_branch_owns_ledger_duties(self):
        branch = section(FIX, "## 循环内分支（implement-test-review 反馈修复）", "### 卡点检查子流程")
        for marker in (
            "凭报告与对话机械可判",
            "报告清单行置 `fixed`",
            "`verified` 由复审方核销",
            "`反馈来源`",
            "`受影响 AC`",
            "`局部验证`",
            "`下一节点`",
            "修复不开新 change",
        ):
            self.assertIn(marker, branch)
        self.assertIn("### 卡点检查子流程（熔断三选一选 b 时执行）", FIX)

    def test_implement_delegates_repair_to_fix(self):
        self.assertNotIn("### 模式二", IMPLEMENT)
        self.assertIn("/eo-fix 循环内分支", IMPLEMENT)
        self.assertIn("NOT FOR: bug 与反馈修复", IMPLEMENT)

    def test_routing_sources_point_to_fix_branch(self):
        test_skill = read("eo-test/SKILL.md")
        self.assertIn("业务代码 bug → **停手**", test_skill)
        self.assertIn("/eo-fix 循环内分支", test_skill)
        review_skill = read("eo-review/SKILL.md")
        self.assertIn("implementation finding → /eo-fix 循环内分支", review_skill)
        self.assertIn(
            "报告有未决阻塞项 → 原 impl worker 走 /eo-fix 循环内分支",
            CONVENTIONS,
        )

    def test_worker_reuse_and_role_isolation_unchanged(self):
        reuse = section(LOOP, "**worker 复用纪律**", "## 可观测性")
        self.assertIn("修复回原 impl worker", reuse)
        self.assertIn("跨角色必须隔离", reuse)
        self.assertIn("review / test 绝不复用 impl worker", reuse)
        branch = section(FIX, "## 循环内分支（implement-test-review 反馈修复）", "### 卡点检查子流程")
        self.assertIn("根因为 `test-asset`", branch)
        self.assertIn("交 `/eo-test`", branch)


class TestFullChainReviewVariant(unittest.TestCase):
    """深挖链路变体：枚举可死点 + 逐点恢复证明，按死点矩阵批量修。"""

    def test_investigation_defines_chain_variant(self):
        variant = section(INVESTIGATION, "## 链路变体：全链审查", "## 调查记录模板")
        for marker in (
            "枚举可死点",
            "恢复证明",
            "UNKNOWN 纪律",
            "死点矩阵",
            "批量落地",
            "不逐 FAIL 驱动",
        ):
            self.assertIn(marker, variant)

    def test_investigation_template_has_death_point_matrix(self):
        self.assertIn("## 死点矩阵", INVESTIGATION)
        self.assertIn("恢复证明（幂等键 / 重试判定 / UNKNOWN 纪律）", INVESTIGATION)

    def test_stuck_check_recognizes_chain_failure_gap(self):
        stuck = section(FIX, "### 卡点检查子流程", "## 关键约束")
        row = line_containing(stuck, "链路失败语义残缺")
        self.assertIn("向前写链", row)
        self.assertIn("全链审查", row)


class TestWhackAMoleSignal(unittest.TestCase):
    """打地鼠信号机械可判；命中即停下逐点回路，交用户裁决。"""

    def test_loop_defines_signal_and_gate(self):
        convergence = section(LOOP, "**④ 收敛判定**", "## 节点清单")
        gate = section(convergence, "**打地鼠信号与裁决门**", "总控不代答")
        self.assertIn("失败触发位置互不相同", gate)
        self.assertIn("凭报告未决清单的位置列机械可判", gate)
        self.assertIn("全链审查", gate)
        self.assertIn("继续逐点修复", gate)
        self.assertIn("卡点检查", gate)
        self.assertIn("回炉", gate)
        self.assertIn("总控不代答", convergence)

    def test_breaker_line_consumes_signal(self):
        breaker = line_containing(LOOP, "| 熔断只消费 |")
        self.assertIn("打地鼠/轮次到限即停", breaker)
        self.assertIn("绝不无限循环", breaker)


if __name__ == "__main__":
    unittest.main()
