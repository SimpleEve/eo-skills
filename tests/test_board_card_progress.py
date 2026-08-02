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

# 刷新保留活动 tab：用可追踪 classList 的轻量 DOM，覆盖 openDetail(isRefresh) 路径。
NODE_TAB_RESTORE_RUNNER = r"""
const fs = require('fs');
const projectJs = fs.readFileSync(process.argv[2], 'utf8');
const payload = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const markup = fs.readFileSync(process.argv[4], 'utf8');

function classList(init) {
  const s = new Set(init || []);
  return {
    add(c) { s.add(c); },
    remove(c) { s.delete(c); },
    toggle(c, on) {
      if (on === undefined) { s.has(c) ? s.delete(c) : s.add(c); }
      else if (on) s.add(c); else s.delete(c);
    },
    contains(c) { return s.has(c); },
  };
}
function el(name, attrs) {
  return {
    name, attrs: Object.assign({}, attrs || {}), style: {}, disabled: false,
    textContent: '', _html: '', _listeners: {},
    classList: classList(),
    children: [],
    querySelector(sel) {
      if (sel === '.detail-tab.active') {
        const tabs = this.querySelectorAll('.detail-tab');
        return tabs.find(t => t.classList.contains('active')) || null;
      }
      if (sel && sel.startsWith('#')) return this._ids && this._ids[sel.slice(1)] || null;
      return null;
    },
    querySelectorAll(sel) {
      if (sel === '.detail-tab') return this._tabs || [];
      if (sel === '.detail-pane') return this._panes || [];
      if (sel === '.card[data-detail]') return this._cards || [];
      return [];
    },
    addEventListener(type, fn) { this._listeners[type] = fn; },
    setAttribute(k, v) { this.attrs[k] = v; },
    getAttribute(k) { return this.attrs[k] != null ? this.attrs[k] : null; },
    focus() {},
    get innerHTML() { return this._html; },
    set innerHTML(v) {
      this._html = String(v || '');
      // 重建 tab/pane 节点以模拟真实 DOM 替换
      const tabIds = [...this._html.matchAll(/data-tab="([^"]+)"/g)].map(m => m[1]);
      const paneIds = [...this._html.matchAll(/data-pane="([^"]+)"/g)].map(m => m[1]);
      this._tabs = tabIds.map((id, i) => {
        const t = el('button', { 'data-tab': id, 'aria-selected': i === 0 ? 'true' : 'false' });
        t.classList = classList(i === 0 ? ['detail-tab', 'active'] : ['detail-tab']);
        return t;
      });
      this._panes = paneIds.map((id, i) => {
        const p = el('div', { 'data-pane': id });
        p.classList = classList(i === 0 ? ['detail-pane', 'active'] : ['detail-pane']);
        return p;
      });
    },
  };
}

const els = {};
const byId = (id) => els[id] || (els[id] = el(id));
byId('eo-project-markup').textContent = markup;
byId('eo-project-css').textContent = '';

const root = el('root');
const pBody = el('p-body');
const pBoard = el('p-board');
const pChips = el('p-chips');
const pTitle = el('p-title');
const pClose = el('p-close');
const pDrawer = el('p-drawer');
const pBackdrop = el('p-backdrop');
const pTopbar = el('p-topbar');
const pStrip = el('p-strip');
const pWarn = el('p-warn');
const pSrc = el('p-src-toggle');
root.querySelector = (sel) => ({
  '#p-drawer': pDrawer, '#p-backdrop': pBackdrop, '#p-body': pBody,
  '#p-chips': pChips, '#p-title': pTitle, '#p-close': pClose,
  '#p-board': pBoard, '#p-topbar': pTopbar, '#p-strip': pStrip, '#p-warn': pWarn,
  '#p-src-toggle': pSrc,
}[sel] || el(sel));
root.querySelectorAll = (sel) => sel === '.card[data-detail]' ? (root._cards || []) : [];

globalThis.document = {
  getElementById: byId,
  createElement: () => el('created'),
  head: { appendChild() {} },
  documentElement: { classList: classList() },
  addEventListener() {}, removeEventListener() {},
  activeElement: null,
};
globalThis.window = {};
globalThis.setInterval = () => 0;
globalThis.clearInterval = () => {};
(0, eval)(projectJs);
const api = window.EO_PROJECT;
api.mount({ root, data: payload.data, dataUrl: '/data.json', homeUrl: '' });
const m = /data-detail="(ch:[^"]+)"/.exec(pBoard.innerHTML || '');
const key = m && m[1];
if (!key || !api.__test) {
  process.stdout.write(JSON.stringify({ error: 'no key/hooks', board: (pBoard.innerHTML || '').slice(0, 200) }));
  process.exit(0);
}
api.__test.openDetail(key, false);
// 用户点「动态」
const journalTab = (pBody._tabs || []).find(t => t.getAttribute('data-tab') === 'journal');
if (!journalTab) {
  process.stdout.write(JSON.stringify({ error: 'no journal tab', detail: pBody.innerHTML.slice(0, 200) }));
  process.exit(0);
}
journalTab._listeners.click && journalTab._listeners.click();
const before = (pBody._tabs || []).find(t => t.classList.contains('active'));
const beforeId = before && before.getAttribute('data-tab');
// 模拟 serve 热刷新
api.__test.openDetail(key, true);
const after = (pBody._tabs || []).find(t => t.classList.contains('active'));
const afterId = after && after.getAttribute('data-tab');
const afterPane = (pBody._panes || []).find(p => p.classList.contains('active'));
process.stdout.write(JSON.stringify({
  beforeTab: beforeId,
  afterTab: afterId,
  afterPane: afterPane && afterPane.getAttribute('data-pane'),
  ok: beforeId === 'journal' && afterId === 'journal',
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

    def write_review_gate(
        self,
        p0=1,
        p1=0,
        rounds_hint=1,
        verdict="不通过",
        open_p0=None,
        open_p1=None,
        p1_status="open",
    ):
        """p0/p1 为标题与台账总行数；open_p0/open_p1 为未决条数（open/fixed）。

        p1_status：未决 P1 行的状态（open 或 fixed）；超出未决的为 verified。
        """
        created = "2026-08-01"
        updated = "2026-08-02" if rounds_hint >= 2 else "2026-08-01"
        headings = "".join(f"### [P0-{i}] 问题{i}\n\n" for i in range(1, p0 + 1))
        headings += "".join(f"### [P1-{i}] P1问题{i}\n\n" for i in range(1, p1 + 1))
        if open_p0 is None:
            open_p0 = p0 if ("不通过" in verdict or "有保留" in verdict) else 0
        if open_p1 is None:
            open_p1 = p1 if ("不通过" in verdict or "有保留" in verdict) else 0
        rows = ""
        for i in range(1, p0 + 1):
            st = "open" if i <= open_p0 else "verified"
            rows += f"| P0-{i} | P0 | 问题{i} | a | {st} | implementation | 1/1 | `abc` |\n"
        for i in range(1, p1 + 1):
            st = p1_status if i <= open_p1 else "verified"
            rows += f"| P1-{i} | P1 | P1问题{i} | a | {st} | implementation | 1/1 | `abc` |\n"
        (self.change_dir / "review.md").write_text(
            f"---\ncreated: {created}\nupdated: {updated}\n---\n\n"
            f"# review\n\n## Finding 台账\n\n"
            "| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |\n"
            "|----|------|------|------|------|------|-------------|------------------|\n"
            f"{rows}\n"
            f"{headings}"
            f"## 速报\n结论：{verdict}\n下一步：修\n",
            encoding="utf-8",
        )

    def write_acceptance(self, unchecked=2):
        lines = "".join("- [ ] 通过：项\n" for _ in range(unchecked))
        (self.change_dir / "acceptance.md").write_text(
            f"# 人工验收单\n\n{lines}",
            encoding="utf-8",
        )

    def write_change_review_gate(self, extra_rounds=0, verdict="不通过", open_p0=True):
        # rounds = 1 + 复审记录节数量；标题格式对齐 CHANGE_REVIEW_ROUND_RE
        st = "open" if open_p0 else "verified"
        body = "---\ncreated: 2026-08-01\n---\n\n# change-review\n\n## Finding 台账\n\n"
        body += "| ID | 级别 | 摘要 | 位置 | 状态 | 根因 | 首见/最近轮 | 基线/修复 commit |\n"
        body += "|----|------|------|------|------|------|-------------|------------------|\n"
        body += f"| P0-1 | P0 | x | a | {st} | implementation | 1/1 | `abc` |\n\n"
        for i in range(extra_rounds):
            body += f"## 复审记录（第 {i + 2} 轮 · 增量 · 2026-08-0{i + 2}）\n\n内容\n\n"
        body += f"## 速报\n结论：{verdict}\n下一步：修\n"
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
        # 时间逆序：最新窗口在最上
        self.assertIn("第二窗", (entries[0].get("title") or "") + (entries[0].get("raw") or ""))
        self.assertIn("第一窗", (entries[-1].get("title") or "") + (entries[-1].get("raw") or ""))

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

    def test_frontmatter_exposed_without_empty_fields(self):
        rec = self.rec()
        fm = rec.get("frontmatter")
        self.assertIsInstance(fm, dict)
        self.assertEqual(fm.get("id"), "demo-progress")
        self.assertEqual(fm.get("seq"), 11)
        self.assertEqual(fm.get("status"), "implementing")
        self.assertNotIn("summary", fm)  # 缺省字段不出现
        self.assertNotIn("issue", fm)

    def test_parse_journal_entries_keeps_recent_window_reports(self):
        text = "\n\n".join(
            f"• {10 + i}:00 「窗{i}」\n\n一句定性：没有需要你裁决的事项。\n"
            for i in range(7)
        )
        entries = self.board.parse_journal_entries(text, limit=5)
        self.assertEqual(len(entries), 5)
        # 取最近 5 条后逆序：窗6 最上、窗2 最下
        self.assertIn("窗6", entries[0]["title"] + entries[0].get("raw", ""))
        self.assertIn("窗2", entries[-1]["title"] + entries[-1].get("raw", ""))


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

    def test_stage_progress_ignores_historical_p0_when_review_passed(self):
        """速报已通过时不得把历史 P0 标题当成当前阻塞。"""
        self.write_review_gate(p0=1, rounds_hint=1, verdict="通过（P0 0 条）", open_p0=0)
        rec = self.rec()
        sp = rec.get("stage_progress")
        if sp is not None:
            self.assertNotIn("P0", sp.get("label") or "", sp)
            self.assertNotEqual(sp.get("stage"), "review")

    def test_stage_progress_prefers_failing_test_over_unchecked_acceptance(self):
        """implementing + 未勾 acceptance 不得盖住失败的 test。"""
        self.write_test_gate(rounds_hint=2, fail=True)
        self.write_acceptance(unchecked=2)
        rec = self.rec()
        self.assertEqual(rec.get("status"), "implementing")
        sp = rec.get("stage_progress")
        self.assertEqual(sp.get("stage"), "test", sp)

    def test_stage_progress_acceptance_only_when_reviewed(self):
        self.write_acceptance(unchecked=1)
        # 改 status 为 reviewed
        body = (self.change_dir / "change.md").read_text(encoding="utf-8")
        (self.change_dir / "change.md").write_text(
            body.replace("status: implementing", "status: reviewed"),
            encoding="utf-8",
        )
        rec = self.rec()
        sp = rec.get("stage_progress")
        self.assertEqual(sp.get("stage"), "acceptance", sp)
        self.assertIn("验收", sp.get("label") or "")

    def test_stage_warn_when_any_gate_rounds_ge_3(self):
        # change-review：首轮 + 2 条复审记录 = 3 轮
        self.write_change_review_gate(extra_rounds=2)
        rec = self.rec()
        sp = rec.get("stage_progress")
        self.assertIsInstance(sp, dict)
        self.assertTrue(sp.get("warn"), sp)
        self.assertGreaterEqual(sp.get("rounds") or 0, 3)

    def test_stage_warn_survives_passed_gate_without_active_stage(self):
        """门已通过、无当前阶段徽标时，轮次 ≥3 仍保留独立 warn。"""
        self.write_change_review_gate(
            extra_rounds=2, verdict="通过", open_p0=False,
        )
        rec = self.rec()
        sp = rec.get("stage_progress")
        self.assertIsInstance(sp, dict, sp)
        self.assertIsNone(sp.get("stage"), sp)
        self.assertFalse(sp.get("label"), sp)
        self.assertTrue(sp.get("warn"), sp)
        self.assertGreaterEqual(sp.get("rounds") or 0, 3)

    def test_stage_warn_survives_archived_with_high_rounds(self):
        """archived 不贴阶段，但历史高轮次仍触发警告。"""
        self.write_change_review_gate(
            extra_rounds=3, verdict="通过", open_p0=False,
        )
        body = (self.change_dir / "change.md").read_text(encoding="utf-8")
        (self.change_dir / "change.md").write_text(
            body.replace("status: implementing", "status: archived"),
            encoding="utf-8",
        )
        rec = self.rec()
        sp = rec.get("stage_progress")
        self.assertIsInstance(sp, dict, sp)
        self.assertIsNone(sp.get("stage"), sp)
        self.assertTrue(sp.get("warn"), sp)
        self.assertGreaterEqual(sp.get("rounds") or 0, 3)

    def test_stage_progress_none_without_gates(self):
        """无质量门时卡面不贴阶段徽标（warn 也不应出现）。"""
        rec = self.rec()
        self.assertIsNone(rec.get("stage_progress"))

    def test_review_open_titles_from_ledger_not_historical_only(self):
        """review 未决标题来自台账 open 行。"""
        self.write_review_gate(p0=2, rounds_hint=1, verdict="不通过", open_p0=1)
        rec = self.rec()
        rv = (rec.get("gates") or {}).get("review") or {}
        self.assertEqual(rv.get("open_p0"), 1)
        titles = rv.get("open_p0_titles") or []
        self.assertEqual(len(titles), 1)
        self.assertIn("P0-1", titles[0])

    def test_reserved_pass_with_open_p1_is_current_stage(self):
        """有保留通过 + 台账 open P1 → 当前仍是 review，不得吞掉未决。"""
        self.write_review_gate(
            p0=0, p1=1, verdict="有保留通过（P1 1 条）", open_p0=0, open_p1=1, p1_status="open",
        )
        rec = self.rec()
        sp = rec.get("stage_progress")
        self.assertIsInstance(sp, dict, sp)
        self.assertEqual(sp.get("stage"), "review", sp)
        self.assertIn("P1", sp.get("label") or "", sp)
        rv = (rec.get("gates") or {}).get("review") or {}
        self.assertEqual(rv.get("open_p1"), 1)
        self.assertTrue(any("P1-1" in t for t in (rv.get("open_p1_titles") or [])))
        self.assertTrue(rec.get("blocker"))

    def test_fixed_p1_counts_as_unresolved_until_verified(self):
        """台账 fixed P1 在复审核销前仍为未决。"""
        self.write_review_gate(
            p0=0, p1=1, verdict="有保留通过（P1 1 条）", open_p0=0, open_p1=1, p1_status="fixed",
        )
        rec = self.rec()
        rv = (rec.get("gates") or {}).get("review") or {}
        self.assertEqual(rv.get("open_p1"), 1)
        self.assertTrue(any("P1-1" in t for t in (rv.get("open_p1_titles") or [])))
        sp = rec.get("stage_progress")
        self.assertEqual(sp.get("stage"), "review", sp)

    def test_verified_p1_with_clean_pass_not_current(self):
        """完全通过 + verified 历史 P1 不回退为当前卡点。"""
        self.write_review_gate(
            p0=0, p1=1, verdict="通过（P0 0 条，P1 0 条）", open_p0=0, open_p1=0,
        )
        rec = self.rec()
        sp = rec.get("stage_progress")
        if sp is not None:
            self.assertNotEqual(sp.get("stage"), "review", sp)
        rv = (rec.get("gates") or {}).get("review") or {}
        self.assertEqual(rv.get("open_p1") or 0, 0)
        self.assertEqual(rv.get("open_p1_titles") or [], [])


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
        self.assertIn("frontmatter", src)
        self.assertIn("stage_progress", src)
        self.assertIn("card-warn", src)
        self.assertIn("md-table", src)
        self.assertIn("md-code", src)
        self.assertIn("current-gate-status", src)
        self.assertIn("当前无卡点", src)

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
        # 动态 / 全文走 mdBlock：条目与全文容器带 md-block，列表项成 <li>
        self.assertIn("j-body md-block", detail)
        self.assertIn("full-md md-block", detail)
        self.assertNotIn('<pre class="full-md">', detail)
        self.assertIn("<li>", detail)  # journal「- 派发」
        self.assertIn("<p>", detail)
        # 概览完整 frontmatter 键值
        self.assertIn("frontmatter", detail)
        self.assertIn("<dt>seq</dt>", detail)
        self.assertIn("<dd>11</dd>", detail)
        self.assertIn("<dt>id</dt>", detail)
        # 全文 tab 含 change 正文片段（渲染后仍可读）；# 标题成 h1
        self.assertIn("Demo Progress", detail)
        self.assertIn("<h1>", detail)
        # 质量门顶部当前状态
        self.assertIn("current-gate-status", detail)
        self.assertIn("当前状态", detail)
        card = result["card"]
        self.assertIn("card-warn", card)
        self.assertTrue(
            "stage" in card or "change-review" in card or "第" in card,
            card,
        )

    def test_gates_tab_shows_current_blocker_and_open_items(self):
        """质量门 tab 顶部展示阶段/卡点/未决明细；无卡点时空态。"""
        self.write_review_gate(p0=1, rounds_hint=1, verdict="不通过", open_p0=1)
        data = self.build()
        rec = data["changes"][0]
        self.assertTrue(rec.get("blocker"))
        html = self.board.render_html(data)
        project_js, markup = self._extract_project_assets(html)
        payload = {"data": data}
        runner = self.root / "detail-runner.js"
        runner.write_text(NODE_DETAIL_RUNNER, encoding="utf-8")
        js_file = self.root / "project-gates.js"
        js_file.write_text(project_js, encoding="utf-8")
        data_file = self.root / "payload-gates.json"
        data_file.write_text(json.dumps(payload), encoding="utf-8")
        markup_file = self.root / "markup-gates.html"
        markup_file.write_text(markup, encoding="utf-8")
        proc = subprocess.run(
            [NODE, str(runner), str(js_file), str(data_file), str(markup_file)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        detail = json.loads(proc.stdout)["detail"]
        self.assertIn("current-gate-status", detail)
        self.assertIn("未决明细", detail)
        self.assertIn("gate-open-list", detail)
        self.assertIn("P0", detail)
        self.assertIn("⛔", detail)
        # 无卡点空态：无 gates 时
        data_clear = json.loads(json.dumps(data))
        data_clear["changes"][0]["gates"] = {}
        data_clear["changes"][0]["blocker"] = None
        data_clear["changes"][0]["stage_progress"] = None
        data_file2 = self.root / "payload-gates-empty.json"
        data_file2.write_text(json.dumps({"data": data_clear}), encoding="utf-8")
        proc2 = subprocess.run(
            [NODE, str(runner), str(js_file), str(data_file2), str(markup_file)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        detail2 = json.loads(proc2.stdout)["detail"]
        self.assertIn("当前无卡点", detail2)

    def test_gates_dom_shows_reserved_pass_fixed_p1(self):
        """有保留通过 + fixed P1：DOM 当前状态含未决明细与卡点。"""
        self.write_review_gate(
            p0=0, p1=1, verdict="有保留通过（P1 1 条）", open_p0=0, open_p1=1, p1_status="fixed",
        )
        data = self.build()
        html = self.board.render_html(data)
        project_js, markup = self._extract_project_assets(html)
        runner = self.root / "detail-runner.js"
        runner.write_text(NODE_DETAIL_RUNNER, encoding="utf-8")
        js_file = self.root / "project-reserved.js"
        js_file.write_text(project_js, encoding="utf-8")
        data_file = self.root / "payload-reserved.json"
        data_file.write_text(json.dumps({"data": data}), encoding="utf-8")
        markup_file = self.root / "markup-reserved.html"
        markup_file.write_text(markup, encoding="utf-8")
        proc = subprocess.run(
            [NODE, str(runner), str(js_file), str(data_file), str(markup_file)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        detail = json.loads(proc.stdout)["detail"]
        self.assertIn("current-gate-status", detail)
        self.assertIn("未决明细", detail)
        self.assertIn("P1", detail)
        self.assertIn("P1-1", detail)
        self.assertIn("⛔", detail)
        self.assertNotIn("无活动质量门阶段", detail)

    def test_md_block_rich_syntax_and_xss_escape(self):
        """全文 mdBlock：标题/表格/代码/checkbox/有序列表 + XSS 探针不回退。"""
        rich = (
            "---\nid: demo-progress\nseq: 11\ntitle: Demo Progress\n"
            "status: implementing\ntier: light\ntype: feature\n"
            "created: 2026-08-02\nsummary: rich-summary\n---\n\n"
            "# H1 Title\n\n## H2 Section\n\n"
            "| ColA | ColB |\n| --- | --- |\n| v1 | v2 |\n\n"
            "```js\nconst x = 1;\n```\n\n"
            "- [x] done task\n- [ ] open task\n\n"
            "1. first\n2. second\n\n"
            "See [link](https://example.com) and **bold** and `code`.\n\n"
            "[js](javascript:alert(1)) [data](data:text/html,hi) [mail](mailto:a@b.c)\n\n"
            "<script>evil()</script>\n"
        )
        (self.change_dir / "change.md").write_text(rich, encoding="utf-8")
        data = self.build()
        rec = data["changes"][0]
        self.assertEqual(rec["frontmatter"].get("summary"), "rich-summary")
        html = self.board.render_html(data)
        project_js, markup = self._extract_project_assets(html)
        # 直接调 mdBlock 钩子，避免整页挂载噪音
        runner = self.root / "mdblock-runner.js"
        runner.write_text(
            "const fs=require('fs');\n"
            "const js=fs.readFileSync(process.argv[2],'utf8');\n"
            "const sample=fs.readFileSync(process.argv[3],'utf8');\n"
            "globalThis.document={getElementById:()=>null,addEventListener(){},removeEventListener(){}};\n"
            "global.window=globalThis.window={};\n"
            "globalThis.setInterval=()=>0;globalThis.clearInterval=()=>{};\n"
            "(0,eval)(js);\n"
            "const out=global.window.EO_PROJECT.__test.mdBlock(sample);\n"
            "process.stdout.write(out);\n",
            encoding="utf-8",
        )
        js_file = self.root / "project-md.js"
        js_file.write_text(project_js, encoding="utf-8")
        sample = self.root / "sample.md"
        sample.write_text(rich, encoding="utf-8")
        proc = subprocess.run(
            [NODE, str(runner), str(js_file), str(sample)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = proc.stdout
        self.assertIn("<h1>", out)
        self.assertIn("<h2>", out)
        self.assertIn('class="md-table"', out)
        self.assertIn("<th>", out)
        self.assertIn("<td>", out)
        self.assertIn('class="md-code"', out)
        self.assertIn("const x = 1;", out)
        self.assertIn('type="checkbox"', out)
        self.assertIn("checked", out)
        self.assertIn("<ol>", out)
        self.assertIn('<a href="https://example.com"', out)
        self.assertIn('<a href="mailto:a@b.c"', out)
        self.assertIn("<strong>", out)
        self.assertIn("<code>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertNotRegex(out, r"<script[\s>]")
        # 危险协议不生成 href（只保留链接文案）
        self.assertNotRegex(out, r'href=["\']javascript:', re.I)
        self.assertNotRegex(out, r'href=["\']data:', re.I)
        self.assertNotIn("javascript:alert", out)
        self.assertNotIn("data:text/html", out)
        self.assertIn("js", out)
        self.assertIn("data", out)
        # 概览侧 frontmatter 含 summary
        payload = {"data": data}
        runner2 = self.root / "detail-runner.js"
        runner2.write_text(NODE_DETAIL_RUNNER, encoding="utf-8")
        data_file = self.root / "payload-rich.json"
        data_file.write_text(json.dumps(payload), encoding="utf-8")
        markup_file = self.root / "markup-rich.html"
        markup_file.write_text(markup, encoding="utf-8")
        proc2 = subprocess.run(
            [NODE, str(runner2), str(js_file), str(data_file), str(markup_file)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc2.returncode, 0, proc2.stderr)
        detail = json.loads(proc2.stdout)["detail"]
        self.assertIn("<dt>summary</dt>", detail)
        self.assertIn("rich-summary", detail)

    def _extract_project_assets(self, html):
        m_js = re.search(
            r'<script>\s*(window\.EO_PROJECT[\s\S]*?)</script>',
            html,
        )
        self.assertIsNotNone(m_js)
        m_markup = re.search(
            r'id="eo-project-markup">([\s\S]*?)</script>',
            html,
        )
        self.assertIsNotNone(m_markup)
        return m_js.group(1), m_markup.group(1)

    def test_active_tab_survives_detail_refresh(self):
        """serve 热刷新重建详情后仍停留在用户选中的 tab（目标不存在回概览）。"""
        self.write_journal("• 12:00 「窗」\n\n一句定性：没有需要你裁决的事项。\n")
        data = self.build()
        html = self.board.render_html(data)
        project_js, markup = self._extract_project_assets(html)
        runner = self.root / "tab-restore-runner.js"
        runner.write_text(NODE_TAB_RESTORE_RUNNER, encoding="utf-8")
        js_file = self.root / "project.js"
        js_file.write_text(project_js, encoding="utf-8")
        data_file = self.root / "payload.json"
        data_file.write_text(json.dumps({"data": data}), encoding="utf-8")
        markup_file = self.root / "markup.html"
        markup_file.write_text(markup, encoding="utf-8")
        proc = subprocess.run(
            [NODE, str(runner), str(js_file), str(data_file), str(markup_file)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertTrue(result.get("ok"), result)
        self.assertEqual(result.get("beforeTab"), "journal")
        self.assertEqual(result.get("afterTab"), "journal")
        self.assertEqual(result.get("afterPane"), "journal")

    def test_journal_absent_renders_empty_hint_in_detail(self):
        """无 journal 时动态 pane 出空态提示，且五 tab 仍在。"""
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
        self.assertIn("full-md md-block", detail)
        self.assertNotIn("journal-entry", detail)


if __name__ == "__main__":
    unittest.main()
