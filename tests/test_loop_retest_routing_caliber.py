"""Review 修复后的条件复验路由静态断言。

锁定非对称回路、Reviewer 免测签署、Tester 定向/完整复验、
Test FAIL 强制回测，以及 Archive 对测试证据新鲜度的最终门禁。
"""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LOOP = (ROOT / "eo-loop" / "SKILL.md").read_text(encoding="utf-8")
CONVENTIONS = (ROOT / "eo-shared" / "conventions.md").read_text(encoding="utf-8")
ACCEPTANCE = (ROOT / "eo-shared" / "acceptance.md").read_text(encoding="utf-8")
IMPLEMENT = (ROOT / "eo-implement" / "SKILL.md").read_text(encoding="utf-8")
REVIEW = (ROOT / "eo-review" / "SKILL.md").read_text(encoding="utf-8")
REVIEW_TEMPLATE = (
    ROOT / "eo-review" / "references" / "review-template.md"
).read_text(encoding="utf-8")
TEST = (ROOT / "eo-test" / "SKILL.md").read_text(encoding="utf-8")
TEST_TEMPLATE = (
    ROOT / "eo-test" / "references" / "test-template.md"
).read_text(encoding="utf-8")
ARCHIVE = (ROOT / "eo-archive" / "SKILL.md").read_text(encoding="utf-8")


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


class TestAC1ReviewFixMayReuseEvidence(unittest.TestCase):
    """Review 修复先增量复审；独立 Reviewer 签署沿用才可免 Test。"""

    def test_loop_uses_short_review_feedback_loop(self):
        convergence = section(LOOP, "**④ 收敛判定**", "## 节点清单")
        self.assertIn("原 reviewer 增量复审", convergence)
        self.assertIn("仍有 P0/P1 就继续这条短回路，不启动 Test", convergence)
        self.assertIn("`沿用` → 跳过 eo-test", convergence)
        self.assertIn("无历史 Test 时仅有待验 heavy AC 才首跑 Test", convergence)
        review_line = line_containing(convergence, "`review` 有 P0/P1")
        self.assertIn("尚未被匹配 Test 轮消费的 `复验`", review_line)
        self.assertIn("基线关系不成立 → 派原 test worker", review_line)

    def test_retest_disposition_cannot_converge_early(self):
        convergence = section(LOOP, "**④ 收敛判定**", "## 节点清单")
        opening = line_containing(convergence, "Review 虽已通过但处置为 `复验`")
        self.assertIn("尚未收敛", opening)
        self.assertIn("最新 Review 未覆盖 `(plan_revision, H)`", opening)
        self.assertIn("测试证据按上方三种方式之一闭合", opening)

    def test_matching_test_round_consumes_retest_without_a_loop(self):
        dispatch = section(LOOP, "**③ 派发与校验裁决**", "**④ 收敛判定**")
        test_delivery = line_containing(dispatch, "Test 交付也按当前基线校验")
        self.assertIn("`触发来源：Review 第 R 轮 @ H`", test_delivery)
        self.assertIn("只有后续通过的 Test 轮明确写", test_delivery)
        self.assertIn("才算消费该路由", test_delivery)
        self.assertIn("不得再次派 Test", test_delivery)
        convergence = section(LOOP, "**④ 收敛判定**", "## 节点清单")
        opening = line_containing(convergence, "Review 虽已通过但处置为 `复验`")
        self.assertIn("尚无匹配该 Review 轮的后续 Test 通过", opening)

    def test_reuse_requires_a_previously_passing_test(self):
        routing = section(
            CONVENTIONS,
            "- **Review 反馈**",
            "- **Test 反馈**",
        )
        for marker in (
            "原 reviewer 增量复审",
            "复审通过后",
            "较旧的通过 Test 基线",
            "`T` 是 `H` 的祖先",
            "既有 Test 无阻塞项",
            "测试证据处置：沿用 / 复验",
        ):
            self.assertIn(marker, routing)

    def test_implement_validates_locally_but_cannot_self_approve(self):
        repair = section(IMPLEMENT, "### 模式二：修复循环", "#### 卡点检查子流程")
        self.assertIn("先复现失败、修后在同层验通过", repair)
        self.assertIn("auto-light AC 就地重验", repair)
        self.assertIn("这是输入，不是免测批准", repair)
        self.assertIn("不得直接让 Loop 跳过 Test", repair)

    def test_reviewer_audits_complete_test_to_head_diff(self):
        self.assertIn("维度 7 · 测试证据失效审计", REVIEW)
        self.assertIn("审计完整 `T..H`", REVIEW)
        self.assertIn("不采信 implement 的“预计无影响”自述", REVIEW)
        self.assertIn("末尾速报每轮都写固定字段", REVIEW)
        self.assertIn("不能压缩掉机器可读路由字段", REVIEW)
        first_record = section(REVIEW_TEMPLATE, "## 第 1 轮记录", "<!-- 复审轮")
        record = section(REVIEW_TEMPLATE, "## 第 N 轮记录", "回炉时由 eo-change")
        speed = section(REVIEW_TEMPLATE, "## 速报", "> 末尾「速报」节")
        for marker in (
            "测试证据处置",
            "既有通过 Test",
            "当前交付基线",
            "受影响 AC / 测试",
            "依据",
        ):
            with self.subTest(area="review_first_round", marker=marker):
                self.assertIn(marker, first_record)
            with self.subTest(area="review_round", marker=marker):
                self.assertIn(marker, record)
            with self.subTest(area="review_speed", marker=marker):
                self.assertIn(marker, speed)

    def test_loop_reuse_targets_latest_passing_test_in_current_revision(self):
        dispatch = section(LOOP, "**③ 派发与校验裁决**", "**④ 收敛判定**")
        reuse = line_containing(dispatch, "Review 修复后的免测判定")
        self.assertIn("当前 `plan_revision`", reuse)
        self.assertIn("精确对应同一 `test.md` 中当前 revision 最新的通过轮", reuse)
        self.assertIn("Test 结构/定向来源链/范围覆盖校验", reuse)
        self.assertIn("台账无阻塞项", reuse)
        self.assertIn("`T` 为 `H` 的祖先", reuse)
        self.assertIn("Test 已在当前 revision 的 `H` 通过且同样通过下文结构校验", reuse)


class TestAC2TargetedRetest(unittest.TestCase):
    """影响可圈定时由 Tester 定向复验，并显式组合新旧证据。"""

    def test_tester_selects_targeted_scope(self):
        phase = section(TEST, "### 阶段一：单元测试", "### 阶段二：")
        self.assertIn("定向复验", phase)
        self.assertIn("有限 AC、用例及依赖闭包", phase)
        self.assertIn("重跑范围", phase)
        self.assertIn("沿用范围", phase)
        targeted_line = line_containing(phase, "**定向复验**")
        self.assertIn("只重跑", targeted_line)
        self.assertIn("不含 auto-heavy", targeted_line)
        self.assertIn("触发影响集记为 `I`", targeted_line)
        self.assertIn("必须证明 `I ⊆ R`", targeted_line)
        self.assertIn("无遗漏、无重叠地分区", targeted_line)
        self.assertIn("无法机械证明就升级完整复验", targeted_line)
        self.assertNotIn("执行全量", targeted_line)
        loop_line = line_containing(
            section(LOOP, "**④ 收敛判定**", "## 节点清单"),
            "进入 `test` 后",
        )
        self.assertIn("原 tester", loop_line)
        self.assertIn("定向复验", loop_line)

    def test_targeted_report_is_anchored_to_current_baseline(self):
        for marker in (
            "验证方式：首轮完整 / 定向复验 / 完整复验",
            "触发来源",
            "来源 Test",
            "当前交付基线",
            "测试资产提交",
            "重跑范围",
            "沿用范围",
            "范围校验",
        ):
            self.assertIn(marker, TEST_TEMPLATE)
        self.assertIn("组合后统一锚定 `B`", TEST)
        first_record = section(TEST_TEMPLATE, "## 第 1 轮记录", "<!-- 复验轮")
        record = section(TEST_TEMPLATE, "## 第 N 轮记录", "回炉时由 eo-change")
        speed = section(TEST_TEMPLATE, "## 速报", "> 末尾「速报」节")
        for marker in (
            "验证方式",
            "触发来源",
            "来源 Test",
            "当前交付基线",
            "测试资产提交",
            "重跑范围",
            "沿用范围",
            "范围校验",
        ):
            with self.subTest(area="first_round", marker=marker):
                self.assertIn(marker, first_record)
            with self.subTest(area="round", marker=marker):
                self.assertIn(marker, record)
            with self.subTest(area="speed", marker=marker):
                self.assertIn(marker, speed)

    def test_targeted_retest_has_a_verifiable_passing_source_round(self):
        evidence = section(TEST, "2. **确定证据范围并盘点覆盖**", "3. **提取缺口验证点**")
        review_retest_line = line_containing(evidence, "Review 修复后")
        self.assertIn("第 N 轮 @ S", review_retest_line)
        self.assertIn("来源轮及其定向来源链均属于当前 `plan_revision`", review_retest_line)
        self.assertIn("结构完整、结论通过", review_retest_line)
        self.assertIn("`S` 是 `H` 的祖先", review_retest_line)
        self.assertIn("不得省略触发轮次或来源轮次只写裸 commit", TEST)


class TestAC3FullRetestAndFailClosed(unittest.TestCase):
    """跨共享面或证据不完整时完整复验，不按改动行数拍脑袋。"""

    def test_full_retest_triggers_cover_material_risk(self):
        for marker in (
            "共享路径",
            "状态机",
            "schema",
            "并发",
            "权限安全",
            "测试基础设施",
            "无法可靠圈定",
        ):
            self.assertIn(marker, TEST)
        self.assertIn("执行全量", TEST)
        scope = section(TEST, "7. **选择并执行最终范围**", "8. **失败分析**")
        full_line = line_containing(scope, "**完整复验**")
        self.assertIn("auto-heavy AC 被弄脏", full_line)
        self.assertIn("执行全量", full_line)
        convergence = section(LOOP, "**④ 收敛判定**", "## 节点清单")
        self.assertIn("任一 auto-heavy AC 被弄脏", convergence)

    def test_invalid_baseline_escalates_directly_to_full_retest(self):
        evidence = section(TEST, "2. **确定证据范围并盘点覆盖**", "3. **提取缺口验证点**")
        review_retest_line = line_containing(evidence, "Review 修复后")
        self.assertIn("基线不成立", review_retest_line)
        self.assertIn("直接升级完整复验", review_retest_line)

    def test_missing_or_ambiguous_review_disposition_retests(self):
        dispatch = section(LOOP, "**③ 派发与校验裁决**", "**④ 收敛判定**")
        self.assertIn("字段缺失/含糊都不能放行", dispatch)
        self.assertIn("后一律按 `复验` 路由", dispatch)
        self.assertIn("影响不清即签复验", REVIEW)


class TestAC4TestFailureAlwaysReturnsToTester(unittest.TestCase):
    """Test FAIL 的核销权留在原 Tester，不能套用 Review 免测。"""

    def test_loop_routes_test_fail_back_to_original_tester(self):
        convergence = section(LOOP, "**④ 收敛判定**", "## 节点清单")
        test_line = next(
            line for line in convergence.splitlines() if "`test` 有未核销 FAIL" in line
        )
        self.assertIn("原 test worker 复验", test_line)
        self.assertIn("不得套用 `沿用`", test_line)
        self.assertIn("再派原 reviewer 增量审查", test_line)

    def test_implement_prioritizes_open_test_fail(self):
        repair = section(IMPLEMENT, "### 模式二：修复循环", "#### 卡点检查子流程")
        self.assertIn("当前存在未核销 Test FAIL", repair)
        self.assertIn("回**原 tester**复验", repair)
        self.assertIn("再回**原 reviewer**增量审查", repair)

    def test_test_report_preserves_retest_next_step(self):
        self.assertIn("修复后由原 tester 复验", TEST_TEMPLATE)
        acceptance_route = line_containing(ACCEPTANCE, "若同时存在未核销 Test FAIL")
        self.assertIn("先回原 tester 复验", acceptance_route)
        self.assertIn("修复提交必须重新 Review", ACCEPTANCE)

    def test_fail_then_pass_restores_reviewed_through_reviewer_even_if_h_is_unchanged(self):
        status_rule = line_containing(TEST, "2. **status 回退与恢复边界**")
        self.assertIn("Test 通过不自行改回 `reviewed`", status_rule)
        self.assertIn("即使 `H` 未变化", status_rule)
        self.assertIn("回原 reviewer", status_rule)
        convergence = section(LOOP, "**④ 收敛判定**", "## 节点清单")
        pass_line = line_containing(convergence, "`test` 通过")
        self.assertIn("status` 因先前 Test FAIL 仍为 `implementing`", pass_line)
        self.assertIn("先派原 reviewer 增量审查", pass_line)
        self.assertIn("只有 `status: reviewed`", pass_line)


class TestAC5ArchiveEvidenceFreshness(unittest.TestCase):
    """Archive 只接受当前 Test，或当前 Review 对旧 Test 的可核验证据沿用。"""

    def test_archive_accepts_exactly_current_or_signed_reuse(self):
        full_gate = section(ARCHIVE, "**全档（tier 缺省/full）**", "**轻档（tier: light）**")
        review_line = line_containing(full_gate, "`review.md` 存在且末尾速报结论为通过")
        self.assertIn("最新轮 revision == 当前 `plan_revision`、基线 commit == H", review_line)
        self.assertIn("任何后续业务代码/测试资产提交", review_line)
        gate = section(full_gate, "**Test 证据门", "3. **验收清单全勾")
        self.assertIn("末尾速报为通过", gate)
        self.assertIn("无 `open`/`fixed` 的阻塞项", gate)
        self.assertIn("Test 结论基线 `B`", gate)
        freshness = line_containing(gate, "**新鲜度二选一**")
        self.assertIn("`B == H`；或 `B != H` 且", freshness)
        self.assertIn("最新 Review 锚定 `H`", gate)
        self.assertIn("测试证据处置：沿用", gate)
        self.assertIn("`B` 是 `H` 的祖先", gate)
        self.assertIn("Review 沿用的必须是这份最新通过 Test", gate)
        self.assertIn("`触发来源：Review 第 R 轮 @ H`", gate)
        self.assertIn("证明复验路由已被后续 Test 消费", gate)
        self.assertIn("任一步缺失/含糊", gate)
        self.assertIn("回原 tester 做定向/完整复验", gate)
        fallback = line_containing(gate, "任一步缺失/含糊")
        self.assertIn("Review 写 `复验` 且未由第 3 项的匹配后续 Test 消费", fallback)

    def test_archive_rejects_incomplete_targeted_provenance(self):
        full_gate = section(ARCHIVE, "**全档（tier 缺省/full）**", "**轻档（tier: light）**")
        gate = section(full_gate, "**Test 证据门", "3. **验收清单全勾")
        targeted = line_containing(gate, "**定向来源与覆盖完整**")
        for marker in (
            "`来源 Test` 必须精确写成 `第 N 轮 @ S`",
            "历史轮须在同一报告中属于当前 revision、结论为通过",
            "`S` 是 `B` 的祖先",
            "递归回溯到当前 revision 的首轮完整/完整复验",
            "成环或基线不单调都失败",
            "重跑范围与沿用范围必须是非空、非占位",
            "从 `触发来源` 指向的历史轮解析影响集 `I`",
            "再机械证明 `I ⊆ R`",
            "无遗漏、无重叠地覆盖",
            "无法证明就必须完整复验",
            "即使 `B == H`",
        ):
            self.assertIn(marker, targeted)

    def test_archive_requires_current_revision_test_evidence(self):
        full_gate = section(ARCHIVE, "**全档（tier 缺省/full）**", "**轻档（tier: light）**")
        gate = section(full_gate, "**Test 证据门", "3. **验收清单全勾")
        complete = line_containing(gate, "**结论完整**")
        self.assertIn("最新 Test 轮 revision == 当前 `plan_revision`", complete)
        key_rule = line_containing(ARCHIVE, "| Test 证据新鲜度 |")
        self.assertIn("新鲜度键为 `(plan_revision, commit)`", key_rule)

    def test_archive_does_not_force_first_test_without_heavy_ac(self):
        full_gate = section(ARCHIVE, "**全档（tier 缺省/full）**", "**轻档（tier: light）**")
        gate = section(full_gate, "**Test 证据门", "3. **验收清单全勾")
        self.assertIn("`test.md` 不存在时保持既有语义", gate)
        self.assertIn("未勾 auto-heavy AC 门", gate)
        dispatch = section(LOOP, "**③ 派发与校验裁决**", "**④ 收敛判定**")
        self.assertIn("从未运行 Test 且没有待验 heavy AC", dispatch)


class TestUnifiedDeliveryBaseline(unittest.TestCase):
    """测试资产与业务代码共享 H；Test、Review、Archive 都不能漏掉它。"""

    def test_test_assets_are_committed_before_final_evidence(self):
        lock = line_containing(TEST, "6. **提交测试资产并锁定交付基线**")
        self.assertIn("先把这些测试资产提交", lock)
        self.assertIn("`[<change-id>]` 前缀", lock)
        self.assertIn("最终执行开始时不得残留本 change 的未提交交付改动", lock)
        self.assertIn("未提交业务代码则停下退回 eo-implement", lock)
        self.assertIn("再次提交、刷新 `H`", lock)
        self.assertIn("`B` = 最终执行基线", lock)
        self.assertIn("`测试资产提交` 必须列全 `A..B`", ARCHIVE)

    def test_delivery_baseline_includes_business_and_test_assets_only(self):
        routing = section(CONVENTIONS, "- **Review 反馈**", "- **权限边界**")
        self.assertIn("业务代码或测试资产提交", routing)
        self.assertIn("纯流程工件提交不推进 `H`", routing)
        self.assertIn("先以 `[<change-id>]` 提交", routing)
        review_dimension = line_containing(REVIEW, "**维度 7 · 测试证据失效审计")
        self.assertIn("业务代码/测试资产提交", review_dimension)
        report_rule = line_containing(TEST, "每轮记录与末尾速报固定写")
        self.assertIn("`B` 是本轮最终执行锁定的 `H`", report_rule)

    def test_test_asset_commit_forces_fresh_review(self):
        dispatch = section(LOOP, "**③ 派发与校验裁决**", "**④ 收敛判定**")
        test_delivery = line_containing(dispatch, "Test 交付也按当前基线校验")
        self.assertIn("测试资产", test_delivery)
        self.assertIn("先以 `[<change-id>]` 提交", test_delivery)
        self.assertIn("最新 Review 未覆盖当前 `(plan_revision, H)`", test_delivery)
        self.assertIn("先回原 reviewer", test_delivery)
        full_gate = section(ARCHIVE, "**全档（tier 缺省/full）**", "**轻档（tier: light）**")
        dirty_line = line_containing(full_gate, "**工作区无本 change 的未提交交付改动**")
        self.assertIn("未提交测试资产", dirty_line)
        self.assertIn("回 /eo-test", dirty_line)

    def test_later_delivery_commit_expires_review_and_reuse_signature(self):
        full_gate = section(ARCHIVE, "**全档（tier 缺省/full）**", "**轻档（tier: light）**")
        review_line = line_containing(full_gate, "`review.md` 存在且末尾速报结论为通过")
        self.assertIn("任何后续业务代码/测试资产提交", review_line)
        self.assertIn("都会同时使 Review 结论与沿用签署过期", review_line)

    def test_revision_change_expires_test_and_review_even_without_new_h(self):
        routing = section(CONVENTIONS, "- **Review 反馈**", "- **权限边界**")
        self.assertIn("完整新鲜度键是 `(plan_revision, commit)`", routing)
        self.assertIn("回炉提升 `plan_revision` 即使 `H` 不变也会使旧证据过期", routing)
        dimension = line_containing(REVIEW, "**维度 7 · 测试证据失效审计")
        self.assertIn("revision 不等于当前 `plan_revision`", dimension)
        self.assertIn("直接签 `复验`", dimension)
        self.assertIn("不得仅凭 `T == H` 沿用", dimension)
        dispatch = section(LOOP, "**③ 派发与校验裁决**", "**④ 收敛判定**")
        test_delivery = line_containing(dispatch, "Test 交付也按当前基线校验")
        self.assertIn("当前 `plan_revision` 的结构化 Test 轮次", test_delivery)
        for marker in (
            "`验证方式`",
            "`触发来源`",
            "`测试资产提交`",
            "`重跑范围`",
            "`沿用范围`",
            "`范围校验`",
        ):
            self.assertIn(marker, test_delivery)
        convergence = section(LOOP, "**④ 收敛判定**", "## 节点清单")
        self.assertIn("任一证据 revision 过期", convergence)


if __name__ == "__main__":
    unittest.main()
