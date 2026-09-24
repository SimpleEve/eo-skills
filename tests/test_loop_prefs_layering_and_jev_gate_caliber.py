"""锁定本次优化的三条新口径：基底无倾向、经验沉淀按属性分层（traps/ 拓扑）、jev 判定门 fail-open。

只读口径文件（eo-loop/SKILL.md、references/preferences-format.md、substrates/*、
eo-shared/jev-gate.md 与三个挂钩 skill），断言新口径锚点存在、被推翻的旧口径清零。
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LOOP = (ROOT / "eo-loop" / "SKILL.md").read_text(encoding="utf-8")
FORMAT = (ROOT / "eo-loop" / "references" / "preferences-format.md").read_text(encoding="utf-8")
TEMPLATE = (ROOT / "eo-loop" / "references" / "substrates" / "_template.md").read_text(encoding="utf-8")
SUBSTRATES = {
    name: (ROOT / "eo-loop" / "references" / "substrates" / f"{name}.md").read_text(encoding="utf-8")
    for name in ("orca-orchestration", "claude-subagent", "codex-subagent")
}
JEV_GATE = (ROOT / "eo-shared" / "jev-gate.md").read_text(encoding="utf-8")
CHANGE = (ROOT / "eo-change" / "SKILL.md").read_text(encoding="utf-8")
CHANGE_REVIEW = (ROOT / "eo-change-review" / "SKILL.md").read_text(encoding="utf-8")
FIX = (ROOT / "eo-fix" / "SKILL.md").read_text(encoding="utf-8")


def section(text, start, end):
    if start not in text:
        raise AssertionError(f"找不到节起点 {start!r}")
    body = text.split(start, 1)[1]
    if end == "\x00":
        return body
    if end not in body:
        raise AssertionError(f"找不到节终点 {end!r}")
    return body.split(end, 1)[0]


class TestSubstrateHasNoBias(unittest.TestCase):
    """基底选择无内置倾向：可用性只由探测节决定。"""

    def test_bias_table_removed(self):
        for marker in ("倾向基底", "初始三基底与优先倾向", "| 调用形态 |"):
            self.assertNotIn(marker, LOOP)

    def test_no_bias_is_declared(self):
        self.assertIn("基底无内置倾向", LOOP)
        self.assertIn("基底之间无优先倾向", LOOP)

    def test_probe_decides_availability(self):
        substrate = section(LOOP, "## 执行基底（可插拔）", "**交互式硬约束")
        self.assertIn("可用性只由各文件「探测」节决定", substrate)

    def test_three_level_priority_kept(self):
        pick = section(LOOP, "**② 选基底**", "**③ 派发")
        for marker in ("本次用户显式指定 > 偏好文件 > 探测选定", "不静默生效", "封闭选择"):
            self.assertIn(marker, pick)


class TestExperienceLayeredByOwnership(unittest.TestCase):
    """经验沉淀按「这是谁的属性」分层：陷阱跟基底走，流水进 history。"""

    def test_loop_declares_four_locations(self):
        sed = section(LOOP, "## 经验沉淀", "## 事实说明")
        for marker in ("preferences/<项目短名>.md", "traps/<基底名>.md", "traps/_general.md",
                       "history/<项目短名>.md"):
            self.assertIn(marker, sed)

    def test_traps_follow_substrate(self):
        sed = section(LOOP, "## 经验沉淀", "## 事实说明")
        self.assertIn("陷阱跟基底走", sed)
        self.assertIn("A 项目踩的坑", sed)

    def test_old_preference_trap_pointer_gone(self):
        """旧口径（运行时陷阱写 preferences/ 并带 [基底名] 前缀）不得残留。"""
        sed = section(LOOP, "## 经验沉淀", "## 事实说明")
        self.assertNotIn("记进偏好文件的「已知陷阱」节", sed)
        for name, text in SUBSTRATES.items():
            traps = section(text, "## 已知陷阱", "\x00")
            self.assertNotIn("loop/preferences/", traps, name)
            self.assertIn(f"loop/traps/{name}.md", traps, name)
        self.assertIn("loop/traps/<基底名>.md", section(TEMPLATE, "## 已知陷阱", "\x00"))

    def test_short_name_consistency_and_size_discipline(self):
        sed = section(LOOP, "## 经验沉淀", "## 事实说明")
        self.assertIn("短名一致性", sed)
        self.assertIn("编辑距离 ≤2", sed)
        self.assertIn("≤4KB", sed)

    def test_format_spec_defines_topology_and_routing(self):
        for marker in ("traps/", "history/", "项目纪律", "写入路由", "append-only",
                       "同根因不同变体的陷阱", "合并为一条"):
            self.assertIn(marker, FORMAT)
        self.assertIn("不再需要 `[基底名]` 前缀", FORMAT)

    def test_history_is_aggregation_source_not_preference(self):
        self.assertIn("连续 ≥2 次", FORMAT)
        self.assertIn("唯一消费场景", FORMAT)


class TestJevGateDiscipline(unittest.TestCase):
    """jev 是决策辅助不是基底：只判不写、fail-open、阈值集中。"""

    def test_positioning_is_not_substrate(self):
        self.assertIn("决策辅助，不是基底", JEV_GATE)
        self.assertIn("不能生成文本", JEV_GATE)

    def test_fail_open_is_hard_rule(self):
        self.assertIn("fail-open", JEV_GATE)
        self.assertIn("主路永不因 jev 阻塞", JEV_GATE)
        self.assertIn("command -v jev-cli && jev-cli doctor --offline", JEV_GATE)

    def test_only_judges_never_writes(self):
        self.assertIn("只判不写", JEV_GATE)
        self.assertIn("不生成叙述性文本", JEV_GATE)
        self.assertIn("带出处标注的分支结论行", JEV_GATE)

    def test_two_hooks_defined_with_thresholds(self):
        self.assertIn("挂钩点 1 · 风险信号独立复判", JEV_GATE)
        self.assertIn("挂钩点 2 · 卡点根因预判", JEV_GATE)
        # 阈值必须锚定语境（防别处出现数字导致空转）
        self.assertIn("**P(true) ≥ 0.7**", JEV_GATE)
        self.assertIn("**0.4 ≤ P(true) < 0.7**", JEV_GATE)
        self.assertIn("top-1 P ≥ **0.7** 且 top-1 与 top-2 差 ≥ **0.2**", JEV_GATE)

    def test_non_hooks_named_to_prevent_gilding(self):
        self.assertIn("明确不挂的判定点", JEV_GATE)
        for marker in ("trivial 判定", "打地鼠信号", "review finding 定级"):
            self.assertIn(marker, JEV_GATE)

    def test_fail_open_timeout_bounded_and_statefile(self):
        """fail-open 必须闭合：探测与调用都有界、state 走文件不内联。"""
        self.assertIn("≤5s", JEV_GATE)
        self.assertIn("--state-file", JEV_GATE)
        self.assertIn("禁止 `-s \"<state>\"` 内联插值", JEV_GATE)

    def test_state_strips_prior_judgments_and_secrets(self):
        """state 剥离前序判定与敏感串，保 jev 独立性。"""
        self.assertIn("剥离一切前序判定记录", JEV_GATE)
        self.assertIn("不含 §6 风险与开放问题节", JEV_GATE)
        self.assertIn("剥离密钥、token、凭证等敏感串", JEV_GATE)

    def test_low_confidence_band_aligns_hit_when_unsure(self):
        """0.4~0.7 低置信按命中处理，与「判不准按命中」同向。"""
        self.assertIn("低置信，**按命中处理**", JEV_GATE)
        self.assertIn("判不准按命中", JEV_GATE)


class TestConsumptionSafetyGates(unittest.TestCase):
    """偏好消费的安全闸：必确认、显式覆盖、global 可达、模板排除。"""

    def test_consume_requires_confirmation_and_explicit_override(self):
        self.assertIn("消费必确认", FORMAT)
        self.assertIn("用户本次显式指定永远覆盖偏好", FORMAT)

    def test_global_preferences_readable(self):
        sed = section(LOOP, "## 经验沉淀", "## 事实说明")
        self.assertIn("preferences/_global.md", sed)
        self.assertIn("项目文件同名条目优先", sed)

    def test_template_excluded_from_candidates(self):
        substrate = section(LOOP, "## 执行基底（可插拔）", "**交互式硬约束")
        self.assertIn("排除 `_template.md`", substrate)

    def test_short_name_requires_identity_check(self):
        sed = section(LOOP, "## 经验沉淀", "## 事实说明")
        self.assertIn("先核项目身份", sed)
        self.assertIn("禁止静默并入", sed)
        self.assertIn("foo/food", FORMAT)

    def test_signal_source_stays_granularity(self):
        """信号清单唯一来源仍是 granularity §5，jev 不另立清单。"""
        self.assertIn("granularity.md", JEV_GATE)
        self.assertIn("§5", JEV_GATE)


class TestJevHooksWired(unittest.TestCase):
    """三处挂钩引用 jev-gate 且降级路径明确。"""

    def test_change_step4_union_and_source_disclosed(self):
        step4 = section(CHANGE, "### 第四步：风险信号扫描与播报", "### 第五步")
        self.assertIn("../eo-shared/jev-gate.md", step4)
        self.assertIn("取并集", step4)
        self.assertIn("仅 jev 命中", step4)
        self.assertIn("照常播报一句「jev 复判未执行」", step4)
        self.assertNotIn("静默降级为纯自判", step4)
    def test_change_review_dimension6_does_not_degrade(self):
        dim6 = next(ln for ln in CHANGE_REVIEW.splitlines() if "维度 6 · 条件节合规" in ln)
        self.assertIn("../eo-shared/jev-gate.md", dim6)
        self.assertIn("不降级维度 6 其余检查", dim6)

    def test_fix_stuck_check_prefers_jev_then_subagent(self):
        stuck = section(FIX, "### 卡点检查子流程", "## 关键约束")
        self.assertIn("jev 预判优先", stuck)
        self.assertIn("../eo-shared/jev-gate.md", stuck)
        # 阈值不满足或不可用仍回退原 subagent 路径，失败关闭原则未被削弱
        self.assertIn("新鲜上下文 subagent", stuck)
        self.assertIn("失败关闭", stuck)
        self.assertIn("jev 预判证伪", stuck)

    def test_shared_index_lists_jev_gate(self):
        readme = (ROOT / "eo-shared" / "README.md").read_text(encoding="utf-8")
        self.assertIn("[jev-gate.md](jev-gate.md)", readme)


if __name__ == "__main__":
    unittest.main()
