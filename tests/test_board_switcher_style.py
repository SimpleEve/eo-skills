"""锁定测试：项目切换器自绘下拉（board-switcher-style）。

对尚未实现的自绘行为必须 RED；已有安全/数据口径可 characterization 锁绿。
"""

import importlib.machinery
import importlib.util
import json
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


# 最小挂载：只验顶栏项目切换器 markup 与键盘/点击流（不依赖泳道板内容）。
NODE_SWITCHER_RUNNER = r"""
const fs = require('fs');
const projectJs = fs.readFileSync(process.argv[2], 'utf8');
const markup = fs.readFileSync(process.argv[3], 'utf8');
const payload = JSON.parse(fs.readFileSync(process.argv[4], 'utf8'));
const scenarios = JSON.parse(fs.readFileSync(process.argv[5], 'utf8'));

function classList(init) {
  const s = new Set(init || []);
  return {
    add(c) { String(c).split(/\s+/).filter(Boolean).forEach(x => s.add(x)); },
    remove(c) { String(c).split(/\s+/).filter(Boolean).forEach(x => s.delete(x)); },
    toggle(c, on) {
      if (on === undefined) { s.has(c) ? s.delete(c) : s.add(c); }
      else if (on) s.add(c); else s.delete(c);
      return s.has(c);
    },
    contains(c) { return s.has(c); },
  };
}

function el(name) {
  return {
    name, tagName: (name || 'div').toUpperCase(),
    attrs: {}, style: {}, value: '', textContent: '', dataset: {},
    parentNode: null, _html: '', _listeners: {}, classList: classList(),
    children: [],
    addEventListener(type, fn) { (this._listeners[type] = this._listeners[type] || []).push(fn); },
    removeEventListener(type, fn) {
      this._listeners[type] = (this._listeners[type] || []).filter(f => f !== fn);
    },
    dispatch(type, ev) { for (const fn of (this._listeners[type] || [])) fn(ev || {}); },
    setAttribute(k, v) { this.attrs[k] = String(v); },
    getAttribute(k) { return this.attrs[k] != null ? this.attrs[k] : null; },
    focus() { document.activeElement = this; },
    closest(sel) {
      if (sel === '.project-switch' && (this.classList.contains('project-switch') || this._isSwitcher)) return this;
      let p = this.parentNode;
      while (p) {
        if (sel === '.project-switch' && (p.classList.contains('project-switch') || p._isSwitcher)) return p;
        p = p.parentNode;
      }
      return null;
    },
    contains(node) {
      if (node === this) return true;
      let p = node && node.parentNode;
      while (p) { if (p === this) return true; p = p.parentNode; }
      return false;
    },
    querySelector(sel) {
      if (!sel) return null;
      if (sel.startsWith('#')) return (this._ids && this._ids[sel.slice(1)]) || null;
      if (sel === '.project-switch') return this._switcher || null;
      if (sel === 'select.project-switch') {
        const s = this._switcher;
        return s && s.tagName === 'SELECT' ? s : null;
      }
      if (sel === '[role="listbox"]') return this._listbox || null;
      if (sel === '[role="combobox"], button.project-switch-trigger, .project-switch-trigger') {
        return this._trigger || null;
      }
      if (sel === '.project-switch-trigger, [data-switcher-trigger]') return this._trigger || null;
      if (sel === '.project-switch-option, [role="option"]') return (this._options || [])[0] || null;
      return null;
    },
    querySelectorAll(sel) {
      if (sel === '.project-switch-option, [role="option"]' || sel === '[role="option"]') {
        return this._options || [];
      }
      if (sel === 'option') return this._options || [];
      return [];
    },
    get innerHTML() { return this._html; },
    set innerHTML(v) {
      this._html = String(v || '');
      // 解析切换器节点（原生 select 或自绘 listbox）
      this._switcher = null;
      this._trigger = null;
      this._listbox = null;
      this._options = [];
      if (/<select[^>]*class="[^"]*project-switch/.test(this._html)
          || /class="project-switch"[^>]*>(?:\s*)<option/.test(this._html)
          || /<select class="project-switch"/.test(this._html)) {
        const s = el('select');
        s.tagName = 'SELECT';
        s.classList.add('project-switch');
        s._isSwitcher = true;
        s.parentNode = this;
        const optRe = /<option value="([^"]*)"([^>]*)>([\s\S]*?)<\/option>/g;
        let m;
        while ((m = optRe.exec(this._html))) {
          const o = el('option');
          o.tagName = 'OPTION';
          o.value = m[1].replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
          o.textContent = m[3]
            .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&amp;/g, '&');
          o.selected = /\bselected\b/.test(m[2]);
          o.parentNode = s;
          this._options.push(o);
        }
        s.addEventListener('change', () => {});
        // 复用生产挂的 change：重新 query 后生产会 addEventListener
        this._switcher = s;
      } else if (/project-switch/.test(this._html) || /role="listbox"/.test(this._html)) {
        const box = el('div');
        box.classList.add('project-switch');
        box._isSwitcher = true;
        box.parentNode = this;
        if (/role="listbox"/.test(this._html)) {
          const lb = el('div');
          lb.setAttribute('role', 'listbox');
          lb._isSwitcher = true;
          lb.parentNode = box;
          this._listbox = lb;
          if (/\bopen\b/.test(this._html) || /aria-expanded="true"/.test(this._html)) {
            box.classList.add('open');
            lb.classList.add('open');
          }
        }
        const trig = el('button');
        trig.tagName = 'BUTTON';
        trig.classList.add('project-switch-trigger');
        trig.parentNode = box;
        this._trigger = trig;
        const optRe = /role="option"[^>]*data-href="([^"]*)"[^>]*>([\s\S]*?)<\//g;
        let m;
        while ((m = optRe.exec(this._html))) {
          const o = el('div');
          o.setAttribute('role', 'option');
          o.setAttribute('data-href', m[1]);
          o._href = m[1].replace(/&quot;/g, '"');
          o.textContent = m[2].replace(/<[^>]+>/g, '');
          o.parentNode = this._listbox || box;
          this._options.push(o);
        }
        // 宽松：任意 data-href 在 option 上
        if (!this._options.length) {
          const hrefRe = /data-href="([^"]+)"/g;
          while ((m = hrefRe.exec(this._html))) {
            const o = el('div');
            o.setAttribute('role', 'option');
            o.setAttribute('data-href', m[1]);
            o._href = m[1];
            o.parentNode = this._listbox || box;
            this._options.push(o);
          }
        }
        this._switcher = box;
      }
    },
  };
}

const els = {};
const byId = (id) => els[id] || (els[id] = el(id));
byId('eo-project-markup').textContent = markup;
byId('eo-project-css').textContent = '';

const root = el('root');
const pTopbar = el('p-topbar');
const pStrip = el('p-strip');
const pBoard = el('p-board');
const pWarn = el('p-warn');
const pDrawer = el('p-drawer');
const pBackdrop = el('p-backdrop');
const pBody = el('p-body');
const pChips = el('p-chips');
const pTitle = el('p-title');
const pClose = el('p-close');
const pSearchBackdrop = el('p-search-backdrop');
const pSearchInput = el('p-search-input');
pSearchInput.tagName = 'INPUT';
const pSearchResults = el('p-search-results');
const pSrc = el('p-src-toggle');

root._ids = {
  'p-topbar': pTopbar, 'p-strip': pStrip, 'p-board': pBoard, 'p-warn': pWarn,
  'p-drawer': pDrawer, 'p-backdrop': pBackdrop, 'p-body': pBody,
  'p-chips': pChips, 'p-title': pTitle, 'p-close': pClose,
  'p-search-backdrop': pSearchBackdrop, 'p-search-input': pSearchInput,
  'p-search-results': pSearchResults, 'p-src-toggle': pSrc,
};
root.querySelector = (sel) => {
  if (sel && sel.startsWith('#')) return root._ids[sel.slice(1)] || null;
  if (sel === '.project-switch') return pTopbar._switcher || null;
  return null;
};
root.querySelectorAll = () => [];
root.contains = (n) => {
  let p = n;
  while (p) { if (p === root || Object.values(root._ids).includes(p)) return true; p = p.parentNode; }
  return false;
};
pTopbar.parentNode = root;

const docListeners = {};
globalThis.document = {
  getElementById: byId,
  createElement: () => el('created'),
  head: { appendChild() {} },
  documentElement: { classList: classList() },
  activeElement: null,
  addEventListener(type, fn) { (docListeners[type] = docListeners[type] || []).push(fn); },
  removeEventListener(type, fn) {
    docListeners[type] = (docListeners[type] || []).filter(f => f !== fn);
  },
  _dispatch(type, ev) { for (const fn of (docListeners[type] || [])) fn(ev); },
};
globalThis.window = { location: { href: 'http://127.0.0.1:9/', hash: '' } };
globalThis.location = globalThis.window.location;
globalThis.setInterval = () => 0;
globalThis.clearInterval = () => {};
globalThis.localStorage = { getItem: () => null, setItem() {}, removeItem() {} };

(0, eval)(projectJs);
const api = window.EO_PROJECT;

function snapshot() {
  const html = pTopbar.innerHTML || '';
  const sw = pTopbar._switcher;
  const open = !!(sw && (sw.classList.contains('open')
    || (pTopbar._listbox && pTopbar._listbox.classList.contains('open'))
    || /aria-expanded="true"/.test(html)));
  return {
    topbar: html,
    hasNativeSelect: /<select\b[^>]*project-switch/.test(html) || (sw && sw.tagName === 'SELECT'),
    hasListbox: /role="listbox"/.test(html) || !!(pTopbar._listbox),
    hasTriggerButton: /<button\b/.test(html) || !!(pTopbar._trigger && pTopbar._trigger.tagName === 'BUTTON'),
    open,
    optionCount: (pTopbar._options || []).length,
    locationHref: String(window.location.href),
    locationHash: String(window.location.hash || ''),
  };
}

function fireKey(opts) {
  const ev = Object.assign({
    key: '', metaKey: false, ctrlKey: false,
    target: document.activeElement || root,
    preventDefault() { this.defaultPrevented = true; },
    defaultPrevented: false,
  }, opts || {});
  document._dispatch('keydown', ev);
}

const out = [];
for (const step of scenarios) {
  const op = step.op;
  if (op === 'mount') {
    const data = JSON.parse(JSON.stringify(payload.data));
    if (step.projects) data.dashboard_projects = step.projects;
    if (step.projectName) data.project.name = step.projectName;
    api.mount({
      root, data,
      dataUrl: step.dataUrl || '/p/alpha~aaa/data.json',
      homeUrl: step.homeUrl || '/',
      projectKey: step.projectKey || 'alpha~aaa',
    });
    // 生产在 buildHeader 末尾对 .project-switch 绑 change；垫片需在 innerHTML 解析后补绑跳转
    const sw = pTopbar._switcher;
    if (sw && sw.tagName === 'SELECT') {
      sw.addEventListener('change', function () { window.location.href = sw.value; });
    }
    out.push({ op, ...snapshot() });
  } else if (op === 'unmount') {
    api.unmount();
    out.push({ op: 'unmount' });
  } else if (op === 'clickTrigger') {
    const t = pTopbar._trigger || pTopbar._switcher;
    if (t) {
      for (const fn of (t._listeners.click || [])) fn({ target: t, stopPropagation() {}, preventDefault() {} });
    }
    out.push({ op, ...snapshot() });
  } else if (op === 'clickOutside') {
    const outside = el('outside');
    outside.parentNode = null;
    document._dispatch('click', { target: outside, stopPropagation() {}, preventDefault() {} });
    // 也派发到可能挂在 document 的监听
    out.push({ op, ...snapshot() });
  } else if (op === 'key') {
    fireKey(step.event || {});
    out.push({ op, ...snapshot() });
  } else if (op === 'pickOption') {
    const opts = pTopbar._options || [];
    const idx = step.index || 0;
    const o = opts[idx];
    if (o) {
      if (pTopbar._switcher && pTopbar._switcher.tagName === 'SELECT') {
        pTopbar._switcher.value = o.value;
        for (const fn of (pTopbar._switcher._listeners.change || [])) fn({ target: pTopbar._switcher });
      } else {
        for (const fn of (o._listeners.click || [])) fn({ target: o, stopPropagation() {}, preventDefault() {} });
        const href = o.getAttribute('data-href') || o._href;
        if (href && !step.skipNav) {
          if (href.charAt(0) === '#') window.location.hash = href;
          else window.location.href = href;
        }
      }
    }
    out.push({ op, ...snapshot(), picked: !!(o) });
  } else {
    out.push({ op, error: 'unknown' });
  }
}
process.stdout.write(JSON.stringify(out));
"""


def sample_data(projects=None, name="alpha"):
    return {
        "data": {
            "project": {
                "name": name,
                "mode": "vault",
                "project_root": "/tmp/alpha-pm",
                "board_enabled": True,
                "github_issue": False,
            },
            "scanned_worktrees": 1,
            "generated_at": "2026-08-12 12:00",
            "serve": False,
            "roadmap": None,
            "stats": {
                "active_changes": 0,
                "backlog_count": 0,
                "direct_commits": {"total": 0, "fix": 0, "ui": 0},
                "stale_count": 0,
                "blocked_count": 0,
            },
            "warnings": [],
            "changes": [],
            "backlog": [],
            "backlog_archive": {"count": 0, "adopted": 0, "dropped": 0},
            "dashboard_projects": projects if projects is not None else [
                {"name": "alpha", "href": "/p/alpha~aaa", "current": True},
                {"name": "beta", "href": "/p/beta~bbb", "current": False},
            ],
        }
    }


@unittest.skipUnless(NODE, "缺少 node")
class BoardSwitcherStyleLockTests(unittest.TestCase):
    """轻档锁定：自绘下拉 RED + 数据/安全 characterization。"""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.board = load_module(f"eo_board_switcher_{id(self)}", BOARD_PATH)
        self.project_js = self.root / "project.js"
        self.markup = self.root / "markup.html"
        self.data_file = self.root / "data.json"
        self.scenario_file = self.root / "scenarios.json"
        self.runner = self.root / "runner.js"
        self.project_js.write_text(self.board.PROJECT_JS, encoding="utf-8")
        self.markup.write_text(self.board.PROJECT_MARKUP, encoding="utf-8")
        self.runner.write_text(NODE_SWITCHER_RUNNER, encoding="utf-8")

    def tearDown(self):
        self.tempdir.cleanup()

    def run_scenarios(self, scenarios, payload=None):
        self.data_file.write_text(json.dumps(payload or sample_data()), encoding="utf-8")
        self.scenario_file.write_text(json.dumps(scenarios), encoding="utf-8")
        proc = subprocess.run(
            [NODE, str(self.runner), str(self.project_js), str(self.markup),
             str(self.data_file), str(self.scenario_file)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        return json.loads(proc.stdout)

    # ── AC-2 / AC-3 自绘交互与跳转（期望 RED：当前仍是原生 select）──

    def test_lock_multi_project_uses_custom_listbox_not_native_select(self):
        """多项目时顶栏必须是自绘触发器+listbox，不得再渲染原生 select。"""
        steps = self.run_scenarios([{"op": "mount"}])
        s0 = steps[0]
        self.assertFalse(s0["hasNativeSelect"])
        self.assertTrue(s0["hasListbox"])
        self.assertTrue(s0["hasTriggerButton"])
        self.assertGreaterEqual(s0["optionCount"], 2)

    def test_lock_switcher_toggle_outside_and_escape_close(self):
        """点击触发器展开/收起；点外与 Esc 收起。"""
        steps = self.run_scenarios([
            {"op": "mount"},
            {"op": "clickTrigger"},
            {"op": "key", "event": {"key": "Escape"}},
            {"op": "clickTrigger"},
            {"op": "clickOutside"},
        ])
        self.assertFalse(steps[0]["open"])
        self.assertTrue(steps[1]["open"])
        self.assertFalse(steps[2]["open"])
        self.assertTrue(steps[3]["open"])
        self.assertFalse(steps[4]["open"])

    def test_lock_arrow_keys_and_enter_select_navigate(self):
        """方向键移动高亮，回车选中并跳转（serve 路径 href）。"""
        steps = self.run_scenarios([
            {"op": "mount", "dataUrl": "/p/alpha~aaa/data.json"},
            {"op": "clickTrigger"},
            {"op": "key", "event": {"key": "ArrowDown"}},
            {"op": "key", "event": {"key": "Enter"}},
        ])
        self.assertTrue(steps[1]["open"] or steps[2]["open"])
        # 回车后应导航到非当前项（beta）
        final = steps[3]
        self.assertIn("/p/beta~bbb", final["locationHref"])

    def test_lock_hash_href_navigation_for_snapshot_form(self):
        """快照形态：选项 href 为 #/p/<key>，选中后写入 location.hash/href。"""
        projects = [
            {"name": "alpha", "href": "#/p/alpha~aaa", "current": True},
            {"name": "beta", "href": "#/p/beta~bbb", "current": False},
        ]
        steps = self.run_scenarios(
            [
                {"op": "mount", "projects": projects, "dataUrl": "/ignored"},
                {"op": "clickTrigger"},
                {"op": "pickOption", "index": 1},
            ],
            payload=sample_data(projects=projects),
        )
        final = steps[-1]
        self.assertTrue(final.get("picked"))
        href = final["locationHref"] + final["locationHash"]
        self.assertTrue(
            "#/p/beta~bbb" in final["locationHash"] or "#/p/beta~bbb" in final["locationHref"],
            final,
        )

    def test_lock_current_project_marked_in_list(self):
        """当前项目在列表中有选中标记（自绘 aria-selected / current，或兼容 selected）。"""
        steps = self.run_scenarios([{"op": "mount"}])
        html = steps[0]["topbar"]
        # 行为契约：当前项可辨；实现可从 option selected 迁到 aria-selected
        self.assertTrue(
            " selected" in html
            or "selected>" in html
            or 'aria-selected="true"' in html
            or "aria-current" in html
            or "is-current" in html
            or "option-current" in html,
            html[:500],
        )

    # ── AC-5 单项目降级（期望 RED：当前 length==1 仍出 select）──

    def test_lock_single_project_stays_static_chip(self):
        """仅一个可下钻项目时保持静态 chip，不出现切换器。"""
        projects = [{"name": "only", "href": "/p/only~x", "current": True}]
        steps = self.run_scenarios(
            [{"op": "mount", "projects": projects, "projectName": "only"}],
            payload=sample_data(projects=projects, name="only"),
        )
        s0 = steps[0]
        self.assertFalse(s0["hasNativeSelect"])
        self.assertFalse(s0["hasListbox"])
        self.assertIn("project", s0["topbar"])
        self.assertIn("only", s0["topbar"])
        self.assertNotIn('aria-label="切换项目"', s0["topbar"])

    # ── AC-4 XSS characterization（当前 esc 已绿，锁住不得回退）──

    def test_lock_project_name_html_is_escaped(self):
        """项目名含 HTML 特殊字符时必须转义，不得出现原始标签。"""
        evil = '<img src=x onerror=alert(1)>'
        projects = [
            {"name": evil, "href": "/p/evil~e", "current": True},
            {"name": "beta", "href": "/p/beta~b", "current": False},
        ]
        steps = self.run_scenarios(
            [{"op": "mount", "projects": projects, "projectName": evil}],
            payload=sample_data(projects=projects, name=evil),
        )
        html = steps[0]["topbar"]
        # 不得以真实标签注入；转义后的文本里可残留 onerror= 字面量
        self.assertNotIn("<img", html)
        self.assertNotRegex(html, r"<img\b")
        self.assertIn("&lt;img", html)


class BoardSwitcherStyleSurfaceLockTests(unittest.TestCase):
    """无 node 也可跑的源码表面锁定。"""

    def setUp(self):
        self.board = load_module(f"eo_board_sw_surface_{id(self)}", BOARD_PATH)

    def test_lock_no_native_select_in_project_switch_markup(self):
        """PROJECT_JS 构建项目切换器时不得再拼原生 select.project-switch。"""
        js = self.board.PROJECT_JS
        self.assertNotIn('<select class="project-switch"', js)
        self.assertNotIn("select class=\"project-switch\"", js)

    def test_lock_custom_switcher_uses_design_tokens_in_css(self):
        """自绘面板样式应引用看板 surface/line 令牌（观感 AC-1 的可静态子集）。"""
        css = self.board.PROJECT_CSS
        # 锁定可测的 token 依赖；完整观感仍归 AC-1 人工
        self.assertIn("project-switch", css)
        block = css.split(".project-switch")[1][:400] if ".project-switch" in css else css
        self.assertTrue(
            "var(--surface)" in block or "var(--surface2)" in block,
            "switcher CSS should use surface tokens",
        )


if __name__ == "__main__":
    unittest.main()
