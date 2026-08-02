"""轻档锁定：看板 card 进度与卡点（journal / 五 tab / 阶段徽标 / ≥3 轮警告）。"""

import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_DIR = REPO_ROOT / "cli"
BOARD_PATH = CLI_DIR / "eo-board"
NODE = shutil.which("node")


def load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


def run_git(repo, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


# 在最小 DOM 垫片上调用 renderChange / changeCard，断言真实 HTML 产出。
NODE_DETAIL_RUNNER = r"""
const fs = require('fs');
const projectJs = fs.readFileSync(process.argv[2], 'utf8');
const payload = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
// 抽出 IIFE 内的函数到全局：跑 mount 用不到，只 eval 整段后从 EO_PROJECT 取不到内部函数。
// 直接用 Function 包装 PROJECT_JS 里声明的函数体不可行；改为挂载后走 openDetail 路径。
function stub(name) {
  return {
    name, innerHTML: '', textContent: '', style: {}, disabled: false, _q: {},
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c); },
      remove(c) { this._s.delete(c); },
      toggle(c, on) { if (on === undefined) { this._s.has(c) ? this._s.delete(c) : this._s.add(c); }
        else if (on) this._s.add(c); else this._s.delete(c); },
      contains(c) { return this._s.has(c); },
    },
    querySelector(sel) { return this._q[sel] || (this._q[sel] = stub(sel)); },
    querySelectorAll(sel) {
      if (sel === '.detail-tab') return this._tabs || [];
      if (sel === '.detail-pane') return this._panes || [];
      if (sel && sel.startsWith('.card')) return this._cards || [];
      return [];
    },
    addEventListener(type, fn) { (this._listeners = this._listeners || {})[type] = fn; },
    setAttribute(k, v) { this[k] = v; this['data-' + k] = v; },
    getAttribute(k) { return this[k] || this['data-' + k] || null; },
    focus() {},
  };
}
const els = {};
const el = (id) => els[id] || (els[id] = stub(id));
el('eo-project-markup').textContent = fs.readFileSync(process.argv[4], 'utf8');
el('eo-project-css').textContent = '';
const root = stub('root');
// mount 会把 markup 写进 root.innerHTML，再 querySelector 找 drawer 等——垫片需支持。
const drawer = stub('p-drawer');
const backdrop = stub('p-backdrop');
const pBody = stub('p-body');
const pChips = stub('p-chips');
const pTitle = stub('p-title');
const pClose = stub('p-close');
const pBoard = stub('p-board');
const pTopbar = stub('p-topbar');
const pStrip = stub('p-strip');
const pWarn = stub('p-warn');
root.querySelector = (sel) => {
  const map = {
    '#p-drawer': drawer, '#p-backdrop': backdrop, '#p-body': pBody,
    '#p-chips': pChips, '#p-title': pTitle, '#p-close': pClose,
    '#p-board': pBoard, '#p-topbar': pTopbar, '#p-strip': pStrip, '#p-warn': pWarn,
    '#p-src-toggle': stub('p-src-toggle'),
  };
  return map[sel] || stub(sel);
};
root.querySelectorAll = (sel) => {
  if (sel === '.card[data-detail]') return root._cards || [];
  return [];
};

globalThis.document = {
  getElementById: el,
  createElement: () => stub('created'),
  head: { appendChild() {} },
  documentElement: { classList: { add() {}, remove() {}, toggle() {} } },
  addEventListener() {}, removeEventListener() {},
  activeElement: null,
};
globalThis.window = { EO_PROJECT: null };
globalThis.setInterval = () => 0;
globalThis.clearInterval = () => {};
(0, eval)(projectJs);
const api = window.EO_PROJECT;
api.mount({ root, data: payload.data, dataUrl: '/data.json', homeUrl: '' });
// 打开第一张 change 卡详情
const firstKey = Object.keys(api /* no export */).length;
// CARD_INDEX 不暴露；直接从 board HTML 解析 data-detail 不可靠。
// 改：在 buildBoard 后 board HTML 在 pBoard.innerHTML，用正则取 data-detail。
const m = /data-detail="(ch:[^"]+)"/.exec(pBoard.innerHTML || '');
const key = m ? m[1].replace(/&quot;/g, '"') : null;
if (!key) {
  process.stdout.write(JSON.stringify({ error: 'no change card', board: pBoard.innerHTML.slice(0, 500) }));
  process.exit(0);
}
// 触发 openDetail：通过卡片 click 监听；bindCardEvents 把监听挂在 stub 上
const cardStub = stub('card');
cardStub.dataset = { detail: key };
// re-bind: 直接调用会失败；用 innerHTML 触发后手动模拟 openDetail 路径
// 最稳：再次 mount 后从 pBoard 的 click 监听拿不到 CARD_INDEX。
// 暴露测试钩子：若 EO_PROJECT.__test 存在则用之。
if (api.__test && api.__test.openDetail) {
  api.__test.openDetail(key);
} else if (api.__test && api.__test.renderChange) {
  const rec = payload.data.changes.find((c) => ('ch:' + (c.id || c.path)) === key
    || ('ch:' + c.id) === key);
  pBody.innerHTML = api.__test.renderChange(rec || payload.data.changes[0]);
  pBoard.innerHTML = api.__test.changeCard(rec || payload.data.changes[0]);
} else {
  process.stdout.write(JSON.stringify({ error: 'no test hooks', board: (pBoard.innerHTML || '').slice(0, 300) }));
  process.exit(0);
}
process.stdout.write(JSON.stringify({
  detail: pBody.innerHTML,
  card: pBoard.innerHTML,
  tabs: (pBody.innerHTML.match(/detail-tab/g) || []).length,
}));
"""


class BoardCardProgressFixture(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.repo = self.root / "repo"
        self.vault = self.root / "vault"
        self.repo.mkdir()
        self.vault.mkdir()
        (self.vault / "backlog").mkdir()
        (self.vault / "roadmap.md").write_text(
            "---\nstatus: active\nphase: initial\nupdated: 2026-08-02\n---\n",
            encoding="utf-8",
        )
        self.change_dir = self.repo / "eo-doc" / "changes" / "11-demo-progress"
        self.change_dir.mkdir(parents=True)
        self.change_body = (
            "---\n"
            "id: demo-progress\n"
            "seq: 11\n"
            "title: Demo Progress\n"
            "status: implementing\n"
            "tier: light\n"
            "type: feature\n"
            "created: 2026-08-02\n"
            "---\n\n"
            "# Demo Progress\n\n"
            "意图：fixture for card progress.\n\n"
            "## 2. 验收清单\n"
            "- [x] AC-1 一\n"
            "- [ ] AC-2 二\n"
        )
        (self.change_dir / "change.md").write_text(self.change_body, encoding="utf-8")
        (self.repo / ".eo-project.json").write_text(
            json.dumps(
                {
                    "project_name": "card-progress",
                    "mode": "vault",
                    "project_root": str(self.vault),
                    "doc_root": "eo-doc",
                    "board": {"enabled": True},
                    "github": {"issue": False, "pr": "never"},
                }
            ),
            encoding="utf-8",
        )
        run_git(self.repo, "init", "-b", "main")
        run_git(self.repo, "config", "user.name", "EO Test")
        run_git(self.repo, "config", "user.email", "eo-test@example.invalid")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-m", "fixture")
        self.board = load_module(f"eo_board_card_progress_{id(self)}", BOARD_PATH)
        self.cfg = self.board.load_project_config(self.repo / ".eo-project.json")

    def tearDown(self):
        self.tempdir.cleanup()

    def build(self):
        return self.board.build_data(self.cfg)

    def rec(self):
        data = self.build()
        self.assertEqual(len(data["changes"]), 1)
        return data["changes"][0]

    def write_journal(self, body, slug="demo-progress"):
        jdir = self.repo / "tmp" / "eo" / "loop" / slug
        jdir.mkdir(parents=True, exist_ok=True)
        (jdir / "journal.md").write_text(body, encoding="utf-8")
        return jdir / "journal.md"

    def write_test_gate(self, rounds_hint=2, fail=True):
        # rounds_approx 来自 git log + frontmatter；用 created/updated 拉到 ≥2
        created = "2026-08-01"
        updated = "2026-08-02" if rounds_hint >= 2 else "2026-08-01"
        verdict = "不通过" if fail else "通过"
        (self.change_dir / "test.md").write_text(
            f"---\ncreated: {created}\nupdated: {updated}\n---\n\n"
            f"# test\n\n### [FAIL-1] 假失败\n\n## 速报\n结论：{verdict}\n下一步：修\n",
            encoding="utf-8",
        )

    def write_review_gate(self, p0=1, rounds_hint=1):
        created = "2026-08-01"
        updated = "2026-08-02" if rounds_hint >= 2 else "2026-08-01"
        headings = "".join(f"### [P0-{i}] 问题{i}\n\n" for i in range(1, p0 + 1))
        (self.change_dir / "review.md").write_text(
            f"---\ncreated: {created}\nupdated: {updated}\n---\n\n"
            f"# review\n\n{headings}"
            "## 速报\n结论：不通过\n下一步：修 P0\n",
            encoding="utf-8",
        )

    def write_change_review_gate(self, extra_rounds=0):
        # rounds = 1 + 复审记录节数量；标题格式对齐 CHANGE_REVIEW_ROUND_RE
        body = "---\ncreated: 2026-08-01\n---\n\n# change-review\n\n## Finding 台账\n\n"
        body += "| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |\n"
        body += "|----|------|------|------|------|------|-------------|------------------|\n"
        body += "| P0-1 | P0 | x | a | open | implementation | 1/1 | `abc` |\n\n"
        for i in range(extra_rounds):
            body += f"## 复审记录（第 {i + 2} 轮 · 增量 · 2026-08-0{i + 2}）\n\n内容\n\n"
        body += "## 速报\n结论：不通过\n下一步：修\n"
        (self.change_dir / "change-review.md").write_text(body, encoding="utf-8")


class JournalAndFullTextTests(BoardCardProgressFixture):
    """journal 投影与 change 全文字段。"""

    def test_journal_entries_loaded_when_present(self):
        self.write_journal(
            "# eo-loop journal · demo-progress\n\n"
            "• 09:00 「第一窗」\n\n"
            "一句定性：没有需要你裁决的事项。\n\n"
            "下一次固定进度报告约 09:30。\n\n"
            "• 09:30 「第二窗」\n\n"
            "一句定性：是否需要你裁决：有，范围分叉。\n\n"
            "- 派发：task_x\n\n"
            "下一次固定进度报告约 10:00。\n"
        )
        rec = self.rec()
        self.assertTrue(rec.get("has_journal"))
        entries = rec.get("journal_entries")
        self.assertIsInstance(entries, list)
        self.assertGreaterEqual(len(entries), 1)
        joined = "\n".join(e.get("raw") or e.get("body") or "" for e in entries)
        self.assertIn("是否需要你裁决", joined)
        self.assertTrue(
            any("第二窗" in (e.get("title") or "") or "第二窗" in (e.get("raw") or "") for e in entries),
            entries,
        )

    def test_journal_absent_empty_state_without_poisoning_other_fields(self):
        rec = self.rec()
        self.assertFalse(rec.get("has_journal"))
        self.assertIn(rec.get("journal_entries"), (None, []))
        self.assertEqual(rec["id"], "demo-progress")
        self.assertEqual(rec["status"], "implementing")
        self.assertIn("ac", rec)
        self.assertTrue(rec.get("full_text") is not None and "Demo Progress" in rec["full_text"])

    def test_full_text_matches_change_md_on_disk(self):
        rec = self.rec()
        on_disk = (self.change_dir / "change.md").read_text(encoding="utf-8")
        self.assertEqual(rec.get("full_text"), on_disk)

    def test_parse_journal_entries_keeps_recent_window_reports(self):
        text = "\n\n".join(
            f"• {10 + i}:00 「窗{i}」\n\n一句定性：没有需要你裁决的事项。\n"
            for i in range(7)
        )
        entries = self.board.parse_journal_entries(text, limit=5)
        self.assertEqual(len(entries), 5)
        self.assertIn("窗2", entries[0]["title"] + entries[0].get("raw", ""))
        self.assertIn("窗6", entries[-1]["title"] + entries[-1].get("raw", ""))


class StageProgressTests(BoardCardProgressFixture):
    """质量门阶段徽标与轮次警告。"""

    def test_stage_progress_from_test_gate(self):
        self.write_test_gate(rounds_hint=2, fail=True)
        rec = self.rec()
        sp = rec.get("stage_progress")
        self.assertIsInstance(sp, dict)
        self.assertEqual(sp.get("stage"), "test")
        self.assertIn("test", sp.get("label", ""))
        self.assertGreaterEqual(sp.get("rounds") or 0, 2)
        self.assertFalse(sp.get("warn"))

    def test_stage_progress_from_review_gate(self):
        self.write_review_gate(p0=1, rounds_hint=1)
        rec = self.rec()
        sp = rec.get("stage_progress")
        self.assertEqual(sp.get("stage"), "review")
        self.assertRegex(sp.get("label") or "", r"review")
        self.assertIn("P0", sp.get("label") or "")

    def test_stage_warn_when_any_gate_rounds_ge_3(self):
        # change-review：首轮 + 2 条复审记录 = 3 轮
        self.write_change_review_gate(extra_rounds=2)
        rec = self.rec()
        sp = rec.get("stage_progress")
        self.assertIsInstance(sp, dict)
        self.assertTrue(sp.get("warn"), sp)
        self.assertGreaterEqual(sp.get("rounds") or 0, 3)

    def test_stage_progress_none_without_gates(self):
        """无质量门时卡面不贴阶段徽标（warn 也不应出现）。"""
        rec = self.rec()
        self.assertIsNone(rec.get("stage_progress"))


class ProjectJsSurfaceTests(BoardCardProgressFixture):
    """前端模板锁：五 tab + 卡面徽标/警告类（静态 + 可选 node）。"""

    def test_project_js_declares_five_tabs_and_stage_warn_hooks(self):
        src = BOARD_PATH.read_text(encoding="utf-8")
        for label in ("概览", "清单", "质量门", "动态", "全文"):
            self.assertIn(label, src)
        self.assertIn("detail-tab", src)
        self.assertIn("detail-pane", src)
        self.assertIn("has_journal", src)
        self.assertIn("journal_entries", src)
        self.assertIn("full_text", src)
        self.assertIn("stage_progress", src)
        self.assertIn("card-warn", src)

    def test_terminal_renderer_ignores_new_progress_fields(self):
        self.write_journal("• 10:00 「x」\n\n一句定性：没有需要你裁决的事项。\n")
        self.write_test_gate(rounds_hint=2)
        data = self.build()
        out = self.board.render_terminal(data)
        # 终端形态不变：不出现 tab / journal 专有呈现
        self.assertNotIn("detail-tab", out)
        self.assertNotIn("是否需要你裁决", out)
        self.assertIn("demo-progress", out)


@unittest.skipUnless(NODE, "node 不可用：跳过 DOM 级渲染断言")
class ProjectJsRenderTests(BoardCardProgressFixture):
    def test_render_change_and_card_via_test_hooks(self):
        self.write_journal(
            "• 11:00 「实窗」\n\n一句定性：是否需要你裁决：否。\n\n- 派发：task_1\n"
        )
        self.write_change_review_gate(extra_rounds=2)
        data = self.build()
        rec = data["changes"][0]
        # 直接调 Python 侧无法跑 JS；用 __test hooks
        html = self.board.render_html(data)
        # 抽出 PROJECT_JS
        marker = "window.EO_PROJECT"
        self.assertIn(marker, html)
        # 从 HTML 模板拆 PROJECT_JS 与 markup
        m_js = re.search(
            r'<script>\s*(window\.EO_PROJECT[\s\S]*?)</script>',
            html,
        )
        self.assertIsNotNone(m_js)
        project_js = m_js.group(1)
        m_markup = re.search(
            r'id="eo-project-markup">([\s\S]*?)</script>',
            html,
        )
        self.assertIsNotNone(m_markup)
        markup = m_markup.group(1)
        payload = {"data": data}
        runner = self.root / "detail-runner.js"
        runner.write_text(NODE_DETAIL_RUNNER, encoding="utf-8")
        js_file = self.root / "project.js"
        js_file.write_text(project_js, encoding="utf-8")
        data_file = self.root / "payload.json"
        data_file.write_text(json.dumps(payload), encoding="utf-8")
        markup_file = self.root / "markup.html"
        markup_file.write_text(markup, encoding="utf-8")
        proc = subprocess.run(
            [NODE, str(runner), str(js_file), str(data_file), str(markup_file)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertNotIn("error", result, result)
        detail = result["detail"]
        for label in ("概览", "清单", "质量门", "动态", "全文"):
            self.assertIn(label, detail)
        self.assertIn("detail-tab", detail)
        self.assertIn("实窗", detail)
        self.assertIn("是否需要你裁决", detail)
        # 全文 tab 含 change 正文片段
        self.assertIn("Demo Progress", detail)
        card = result["card"]
        self.assertIn("card-warn", card)
        self.assertTrue(
            "stage" in card or "change-review" in card or "第" in card,
            card,
        )

    def test_journal_absent_renders_empty_hint_in_detail(self):
        """AC-3：无 journal 时动态 pane 出空态提示，且五 tab 仍在。"""
        data = self.build()
        html = self.board.render_html(data)
        m_js = re.search(
            r'<script>\s*(window\.EO_PROJECT[\s\S]*?)</script>',
            html,
        )
        self.assertIsNotNone(m_js)
        project_js = m_js.group(1)
        m_markup = re.search(
            r'id="eo-project-markup">([\s\S]*?)</script>',
            html,
        )
        self.assertIsNotNone(m_markup)
        markup = m_markup.group(1)
        runner = self.root / "detail-runner-empty.js"
        runner.write_text(NODE_DETAIL_RUNNER, encoding="utf-8")
        js_file = self.root / "project-empty.js"
        js_file.write_text(project_js, encoding="utf-8")
        data_file = self.root / "payload-empty.json"
        data_file.write_text(json.dumps({"data": data}), encoding="utf-8")
        markup_file = self.root / "markup-empty.html"
        markup_file.write_text(markup, encoding="utf-8")
        proc = subprocess.run(
            [NODE, str(runner), str(js_file), str(data_file), str(markup_file)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertNotIn("error", result, result)
        detail = result["detail"]
        for label in ("概览", "清单", "质量门", "动态", "全文"):
            self.assertIn(label, detail)
        self.assertIn("empty-hint", detail)
        self.assertIn("暂无 loop 窗口报告", detail)
        self.assertIn("Demo Progress", detail)
        self.assertNotIn("journal-entry", detail)


if __name__ == "__main__":
    unittest.main()
