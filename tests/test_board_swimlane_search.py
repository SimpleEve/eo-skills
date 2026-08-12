"""泳道定位搜索与列折叠：键盘唤起、#seq、定位态、折叠记忆、热刷新清除。"""

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
from unittest import mock


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


# 交互场景垫片：可挂载、派发 keydown/click、读 locating/collapsed/search open、模拟 buildBoard 热刷新。
NODE_SWIMLANE_RUNNER = r"""
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
    toArray() { return [...s]; },
  };
}

function el(name, attrs) {
  const node = {
    name, tagName: (name || 'div').toUpperCase(),
    attrs: Object.assign({}, attrs || {}),
    style: {}, disabled: false, textContent: '', value: '',
    isContentEditable: false, parentNode: null, dataset: {},
    _html: '', _listeners: {}, _children: [], classList: classList(),
    addEventListener(type, fn) {
      (this._listeners[type] = this._listeners[type] || []).push(fn);
    },
    removeEventListener(type, fn) {
      const list = this._listeners[type] || [];
      this._listeners[type] = list.filter(f => f !== fn);
    },
    dispatch(type, event) {
      for (const fn of (this._listeners[type] || [])) fn(event);
    },
    setAttribute(k, v) {
      this.attrs[k] = String(v);
      if (k.startsWith('data-')) this.dataset[k.slice(5)] = String(v);
    },
    getAttribute(k) {
      return this.attrs[k] != null ? this.attrs[k] : null;
    },
    focus() { document.activeElement = this; },
    scrollIntoView() { this._scrolled = true; },
    closest(sel) {
      if (sel === '.card' && this.name === 'card') return this;
      if (sel === '.search-panel' && (this.name === 'search-panel' || this._inSearch)) return this;
      if (sel === '.col' && this.name === 'col') return this;
      let p = this.parentNode;
      while (p) {
        if (sel === '.card' && p.name === 'card') return p;
        if (sel === '.search-panel' && (p.name === 'search-panel' || p._inSearch)) return p;
        if (sel === '.col' && p.name === 'col') return p;
        p = p.parentNode;
      }
      return null;
    },
    contains(other) {
      if (other === this) return true;
      let p = other && other.parentNode;
      while (p) { if (p === this) return true; p = p.parentNode; }
      return false;
    },
    querySelector(sel) {
      if (sel && sel.startsWith('#')) {
        const id = sel.slice(1);
        return (this._ids && this._ids[id]) || null;
      }
      if (sel === '.col-toggle') return (this._toggles || [])[0] || null;
      if (sel && sel.startsWith('.col[data-status=')) {
        const status = sel.match(/data-status="([^"]+)"/)[1];
        return (this._cols || []).find(c => c.getAttribute('data-status') === status) || null;
      }
      if (sel === '.detail-tab.active') {
        return (this._tabs || []).find(t => t.classList.contains('active')) || null;
      }
      return null;
    },
    querySelectorAll(sel) {
      if (sel === '.card[data-detail]') return this._cards || [];
      if (sel === '.card.located') return (this._cards || []).filter(c => c.classList.contains('located'));
      if (sel === '.col-toggle') return this._toggles || [];
      if (sel === '.col.collapsed') return (this._cols || []).filter(c => c.classList.contains('collapsed'));
      if (sel === '.col') return this._cols || [];
      if (sel === '.search-result') return this._results || [];
      if (sel === '.detail-tab') return this._tabs || [];
      if (sel === '.detail-pane') return this._panes || [];
      if (sel === '.card') return this._cards || [];
      return [];
    },
    get innerHTML() { return this._html; },
    set innerHTML(v) {
      this._html = String(v || '');
      if (this.name === 'p-board' || this.name === 'board') {
        rebuildBoard(this, this._html);
      }
      if (this.name === 'p-search-results') {
        this._results = [...this._html.matchAll(/data-search-index="(\d+)"/g)].map((m) => {
          const b = el('button', { 'data-search-index': m[1] });
          b.name = 'search-result';
          b.classList = classList(['search-result']);
          b._inSearch = true;
          b.parentNode = this;
          return b;
        });
      }
      if (this.name === 'p-body') {
        const tabIds = [...this._html.matchAll(/data-tab="([^"]+)"/g)].map(m => m[1]);
        this._tabs = tabIds.map((id, i) => {
          const t = el('button', { 'data-tab': id });
          t.classList = classList(i === 0 ? ['detail-tab', 'active'] : ['detail-tab']);
          return t;
        });
      }
      if (this.name === 'p-topbar' || this.name === 'p-strip' || this.name === 'p-warn') {
        // no-op structural parse
      }
    },
  };
  return node;
}

function rebuildBoard(board, html) {
  const cols = [];
  const cards = [];
  const toggles = [];
  const colRe = /<section class="col([^"]*)" data-status="([^"]+)"/g;
  let m;
  const colMeta = [];
  while ((m = colRe.exec(html))) {
    colMeta.push({ classes: m[1], status: m[2], index: m.index });
  }
  for (let i = 0; i < colMeta.length; i++) {
    const meta = colMeta[i];
    const end = i + 1 < colMeta.length ? colMeta[i + 1].index : html.length;
    const chunk = html.slice(meta.index, end);
    const col = el('col', { 'data-status': meta.status });
    col.name = 'col';
    const init = ['col'];
    if (/\bcollapsed\b/.test(meta.classes)) init.push('collapsed');
    col.classList = classList(init);
    col.parentNode = board;
    const toggle = el('button', {
      'aria-label': (/\bcollapsed\b/.test(meta.classes) ? '展开' : '折叠'),
      'aria-expanded': (/\bcollapsed\b/.test(meta.classes) ? 'false' : 'true'),
    });
    toggle.name = 'col-toggle';
    toggle.classList = classList(['col-toggle']);
    toggle.parentNode = col;
    toggle.closest = (sel) => (sel === '.col' ? col : null);
    col._toggles = [toggle];
    toggles.push(toggle);
    const cardRe = /data-detail="([^"]+)"/g;
    let cm;
    while ((cm = cardRe.exec(chunk))) {
      const detail = cm[1];
      const card = el('card', { 'data-detail': detail });
      card.name = 'card';
      card.classList = classList(['card']);
      card.dataset.detail = detail;
      card.parentNode = col;
      card.scrollIntoView = () => { board._scrolledTo = detail; card._scrolled = true; };
      cards.push(card);
    }
    cols.push(col);
  }
  board._cols = cols;
  board._cards = cards;
  board._toggles = toggles;
  board._ids = board._ids || {};
}

const store = Object.create(null);
globalThis.localStorage = {
  getItem(k) { return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null; },
  setItem(k, v) { store[k] = String(v); },
  removeItem(k) { delete store[k]; },
  _dump() { return { ...store }; },
};

const els = {};
const byId = (id) => els[id] || (els[id] = el(id));
byId('eo-project-markup').textContent = markup;
byId('eo-project-css').textContent = '';

const root = el('root');
const pBoard = el('p-board');
const pSearchBackdrop = el('p-search-backdrop');
const pSearchInput = el('p-search-input');
pSearchInput.tagName = 'INPUT';
const pSearchResults = el('p-search-results');
const pDrawer = el('p-drawer');
const pBackdrop = el('p-backdrop');
const pBody = el('p-body');
const pChips = el('p-chips');
const pTitle = el('p-title');
const pClose = el('p-close');
const pTopbar = el('p-topbar');
const pStrip = el('p-strip');
const pWarn = el('p-warn');
const pSrc = el('p-src-toggle');
const searchPanel = el('search-panel');
searchPanel.name = 'search-panel';
searchPanel._inSearch = true;

root._ids = {
  'p-board': pBoard, 'p-search-backdrop': pSearchBackdrop, 'p-search-input': pSearchInput,
  'p-search-results': pSearchResults, 'p-drawer': pDrawer, 'p-backdrop': pBackdrop,
  'p-body': pBody, 'p-chips': pChips, 'p-title': pTitle, 'p-close': pClose,
  'p-topbar': pTopbar, 'p-strip': pStrip, 'p-warn': pWarn, 'p-src-toggle': pSrc,
};
pBoard.parentNode = root;
pSearchBackdrop.parentNode = root;
pSearchInput.parentNode = searchPanel;
searchPanel.parentNode = pSearchBackdrop;
pSearchResults.parentNode = searchPanel;

root.querySelector = (sel) => {
  if (sel && sel.startsWith('#')) return root._ids[sel.slice(1)] || null;
  if (sel && sel.startsWith('.col[data-status=')) {
    const status = sel.match(/data-status="([^"]+)"/)[1];
    return (pBoard._cols || []).find(c => c.getAttribute('data-status') === status) || null;
  }
  return null;
};
root.querySelectorAll = (sel) => {
  if (sel === '.card[data-detail]') return pBoard._cards || [];
  if (sel === '.col-toggle') return pBoard._toggles || [];
  if (sel === '.col.collapsed') return (pBoard._cols || []).filter(c => c.classList.contains('collapsed'));
  if (sel === '.col') return pBoard._cols || [];
  return [];
};
root.contains = (node) => {
  if (!node) return false;
  if (node === root) return true;
  let p = node;
  while (p) { if (p === root) return true; p = p.parentNode; }
  // after mount, nodes under root map are considered inside
  return Object.values(root._ids).includes(node) || (pBoard._cards || []).includes(node)
    || (pBoard._cols || []).includes(node) || (pBoard._toggles || []).includes(node)
    || node === searchPanel || node === pSearchResults || node === pSearchInput;
};

const docListeners = {};
globalThis.document = {
  getElementById: byId,
  createElement: () => el('created'),
  head: { appendChild() {} },
  documentElement: { classList: classList() },
  activeElement: null,
  addEventListener(type, fn) {
    (docListeners[type] = docListeners[type] || []).push(fn);
  },
  removeEventListener(type, fn) {
    docListeners[type] = (docListeners[type] || []).filter(f => f !== fn);
  },
  _dispatch(type, event) {
    for (const fn of (docListeners[type] || [])) fn(event);
  },
  _listenerCount(type) { return (docListeners[type] || []).length; },
};
globalThis.window = {};
// 可驱动的 fake timer/fetch：serve 热刷新必须走 startPolling → setInterval(refreshLoop) → fetch → buildBoard
const intervals = [];
globalThis.setInterval = (fn, ms) => {
  const handle = { fn, ms, cleared: false };
  intervals.push(handle);
  return handle;
};
globalThis.clearInterval = (handle) => {
  if (handle && typeof handle === 'object') handle.cleared = true;
};
let nextFetchText = null;
const fetchLog = [];
globalThis.fetch = (url, opts) => {
  fetchLog.push({ url: String(url), opts: opts || {} });
  const text = nextFetchText != null ? nextFetchText : JSON.stringify(payload.data);
  return Promise.resolve({
    ok: true,
    text: () => Promise.resolve(text),
  });
};

(0, eval)(projectJs);
const api = window.EO_PROJECT;

function activeInterval() {
  return intervals.find((h) => !h.cleared) || null;
}

async function tickPolling(bodyText) {
  const handle = activeInterval();
  if (!handle) throw new Error('no active polling interval — mount with DATA.serve and fetch');
  nextFetchText = bodyText;
  handle.fn(); // 生产 refreshLoop：fetch(DATA_URL).then(...).then(buildBoard)
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
}

function snapshot() {
  const located = (pBoard._cards || []).filter(c => c.classList.contains('located')).map(c => c.getAttribute('data-detail'));
  const collapsed = (pBoard._cols || []).filter(c => c.classList.contains('collapsed')).map(c => c.getAttribute('data-status'));
  return {
    searchOpen: pSearchBackdrop.classList.contains('open'),
    locating: pBoard.classList.contains('locating'),
    located,
    scrolledTo: pBoard._scrolledTo || null,
    collapsed,
    resultsHtml: pSearchResults.innerHTML,
    storage: localStorage._dump(),
    keydownListeners: document._listenerCount('keydown'),
    clickListeners: document._listenerCount('click'),
  };
}

function fireKey(opts) {
  const event = Object.assign({
    key: '', metaKey: false, ctrlKey: false, target: document.activeElement,
    preventDefault() { this._prevented = true; },
    _prevented: false,
  }, opts || {});
  document._dispatch('keydown', event);
  return event;
}

function fireDocClick(target) {
  const event = {
    target: target || el('outside'),
    preventDefault() {},
  };
  if (!event.target.parentNode && event.target !== root) {
    // blank area still "inside" root for locate clear path when root.contains
    event.target.parentNode = root;
  }
  document._dispatch('click', event);
}

const out = [];

async function runScenarios() {
  for (const step of scenarios) {
    const op = step.op;
    if (op === 'mount') {
      const data = JSON.parse(JSON.stringify(payload.data));
      if (step.serve) data.serve = true;
      fetchLog.length = 0;
      api.mount({
        root, data,
        dataUrl: step.dataUrl || '/data.json',
        homeUrl: step.homeUrl || '',
        projectKey: step.projectKey || 'demo~key',
      });
      out.push({
        op, ...snapshot(),
        polling: !!activeInterval(),
        fetchCalls: fetchLog.length,
      });
    } else if (op === 'unmount') {
      api.unmount();
      out.push({
        op,
        keydownListeners: document._listenerCount('keydown'),
        clickListeners: document._listenerCount('click'),
        polling: !!activeInterval(),
      });
    } else if (op === 'key') {
      fireKey(step.event || {});
      out.push({ op, ...snapshot() });
    } else if (op === 'focusInput') {
      document.activeElement = pSearchInput;
      out.push({ op, active: 'input' });
    } else if (op === 'blur') {
      const body = el('body');
      body.tagName = 'BODY';
      document.activeElement = body;
      out.push({ op, active: 'body' });
    } else if (op === 'typeSearch') {
      pSearchInput.value = step.value || '';
      pSearchInput.dispatch('input', { target: pSearchInput });
      out.push({ op, value: pSearchInput.value, ...snapshot() });
    } else if (op === 'clickBackdrop') {
      pSearchBackdrop.dispatch('click', { target: pSearchBackdrop });
      out.push({ op, ...snapshot() });
    } else if (op === 'clickBlank') {
      const blank = el('blank');
      blank.parentNode = root;
      fireDocClick(blank);
      out.push({ op, ...snapshot() });
    } else if (op === 'collapse') {
      const col = (pBoard._cols || []).find(c => c.getAttribute('data-status') === step.status);
      const toggle = col && col._toggles && col._toggles[0];
      if (toggle) {
        const listeners = toggle._listeners.click || [];
        for (const fn of listeners) fn({ stopPropagation() {}, target: toggle });
      }
      out.push({ op, status: step.status, ...snapshot() });
    } else if (op === 'searchCards') {
      const hits = api.__test.searchCards(step.query);
      out.push({
        op, query: step.query,
        keys: hits.map(h => h.key),
        statuses: hits.map(h => h.status),
        count: hits.length,
        titles: hits.map(h => h.card.title),
      });
    } else if (op === 'rebuildBoard') {
      // 折叠记忆跨 remount（localStorage），与 serve 热刷新路径分离
      const key = step.projectKey || 'demo~key';
      const collapsedBefore = snapshot().collapsed;
      api.unmount();
      api.mount({
        root, data: JSON.parse(JSON.stringify(payload.data)),
        dataUrl: '/data.json', homeUrl: '', projectKey: key,
      });
      out.push({ op, collapsedBefore, ...snapshot() });
    } else if (op === 'hotRefreshPoll') {
      // 生产路径：startPolling 注册的 refreshLoop → fetch(DATA_URL) → buildBoard → clearLocate
      // 禁止 unmount/mount（那会由 unmount 自行清 locatedKey，测不到接线）
      const before = snapshot();
      const listenersBefore = {
        keydown: document._listenerCount('keydown'),
        click: document._listenerCount('click'),
      };
      const dataUrl = step.dataUrl || '/p/demo~key/data.json';
      const next = JSON.parse(JSON.stringify(payload.data));
      next.serve = true;
      next.generated_at = step.stamp || '2026-08-12 12:00:01'; // 保证 hash 变化
      const callsBefore = fetchLog.length;
      await tickPolling(JSON.stringify(next));
      const lastFetch = fetchLog[fetchLog.length - 1] || null;
      out.push({
        op,
        beforeLocate: before.locating,
        beforeLocated: before.located,
        beforeCollapsed: before.collapsed,
        ...snapshot(),
        fetchCalls: fetchLog.length - callsBefore,
        fetchUrl: lastFetch && lastFetch.url,
        fetchCache: lastFetch && lastFetch.opts && lastFetch.opts.cache,
        listenersBefore,
        keydownListeners: document._listenerCount('keydown'),
        clickListeners: document._listenerCount('click'),
        stillPolling: !!activeInterval(),
      });
    } else {
      out.push({ op, error: 'unknown' });
    }
  }
}

runScenarios().then(() => {
  process.stdout.write(JSON.stringify(out));
}).catch((err) => {
  process.stderr.write(String(err && err.stack || err));
  process.exit(1);
});
"""


@unittest.skipUnless(NODE, "缺少 node，无法跑泳道前端垫片")
class SwimlaneSearchInteractionTests(unittest.TestCase):
    """AC-1/3/4/7/8：通过 EO_PROJECT.mount 真实入口 + 键盘/点击事件验证。"""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.board = load_module(f"eo_board_swim_{id(self)}", BOARD_PATH)
        self.project_js = self.root / "project.js"
        self.markup = self.root / "markup.html"
        self.data_file = self.root / "data.json"
        self.scenario_file = self.root / "scenarios.json"
        self.runner = self.root / "runner.js"
        self.project_js.write_text(self.board.PROJECT_JS, encoding="utf-8")
        self.markup.write_text(self.board.PROJECT_MARKUP, encoding="utf-8")
        self.runner.write_text(NODE_SWIMLANE_RUNNER, encoding="utf-8")
        self.payload = {
            "data": {
                "project": {
                    "name": "demo",
                    "mode": "vault",
                    "project_root": "/tmp/demo-pm",
                    "board_enabled": True,
                    "github_issue": False,
                },
                "scanned_worktrees": 1,
                "generated_at": "2026-08-12 12:00",
                "serve": False,
                "roadmap": None,
                "stats": {
                    "active_changes": 2,
                    "backlog_count": 1,
                    "direct_commits": {"total": 0, "fix": 0, "ui": 0},
                    "stale_count": 0,
                    "blocked_count": 0,
                },
                "warnings": [],
                "changes": [
                    {
                        "id": "alpha",
                        "seq": 21,
                        "title": "Alpha Title",
                        "status": "implementing",
                        "tier": "full",
                        "type": "feature",
                        "summary": "alpha summary",
                        "full_text": "# Alpha\n\n## 3. TODO\n- [ ] UNIQUE_BODY_TOKEN in todo\n",
                        "ac": [{"done": False, "text": "a"}],
                        "todo": None,
                        "path": "/demo/alpha.md",
                        "kind": "change",
                        "dirname": "01-alpha",
                        "last_touch": "2026-08-12",
                    },
                    {
                        "id": "beta",
                        "seq": 7,
                        "title": "Beta Other",
                        "status": "draft",
                        "tier": "light",
                        "type": "fix",
                        "summary": "beta",
                        "full_text": "# Beta\n",
                        "ac": [],
                        "todo": None,
                        "path": "/demo/beta.md",
                        "kind": "change",
                        "dirname": "02-beta",
                        "last_touch": "2026-08-11",
                    },
                ],
                "backlog": [
                    {
                        "id": "bl1",
                        "title": "Backlog Item",
                        "body": "BACKLOG_BODY_TOKEN details",
                        "path": "/demo/bl1.md",
                        "tags": [],
                        "created": "2026-08-01",
                        "kind": "backlog",
                        "issue": None,
                    }
                ],
                "backlog_archive": {"count": 0, "adopted": 0, "dropped": 0},
            }
        }
        self.data_file.write_text(json.dumps(self.payload), encoding="utf-8")

    def tearDown(self):
        self.tempdir.cleanup()

    def run_scenarios(self, scenarios):
        self.scenario_file.write_text(json.dumps(scenarios), encoding="utf-8")
        proc = subprocess.run(
            [NODE, str(self.runner), str(self.project_js), str(self.markup),
             str(self.data_file), str(self.scenario_file)],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        return json.loads(proc.stdout)

    def test_search_open_close_and_slash_exempt_when_typing(self):
        steps = self.run_scenarios([
            {"op": "mount", "projectKey": "demo~a"},
            {"op": "key", "event": {"key": "k", "metaKey": True}},  # Cmd+K open
            {"op": "key", "event": {"key": "Escape"}},  # Esc close
            {"op": "blur"},  # focus leaves search input after close
            {"op": "key", "event": {"key": "k", "ctrlKey": True}},  # Ctrl+K open
            {"op": "key", "event": {"key": "Escape"}},
            {"op": "blur"},
            {"op": "key", "event": {"key": "/"}},  # slash open
            {"op": "clickBackdrop"},  # outside close
            {"op": "blur"},
            {"op": "key", "event": {"key": "/"}},  # open again
            {"op": "focusInput"},
            {"op": "key", "event": {"key": "/"}},  # focused in input: must stay open
            {"op": "unmount"},
        ])
        self.assertFalse(steps[0]["searchOpen"])
        self.assertTrue(steps[1]["searchOpen"])
        self.assertFalse(steps[2]["searchOpen"])
        self.assertTrue(steps[4]["searchOpen"])
        self.assertFalse(steps[5]["searchOpen"])
        self.assertTrue(steps[7]["searchOpen"])
        self.assertFalse(steps[8]["searchOpen"])
        self.assertTrue(steps[10]["searchOpen"])
        self.assertTrue(steps[12]["searchOpen"])
        self.assertEqual(steps[13]["keydownListeners"], 0)
        self.assertEqual(steps[13]["clickListeners"], 0)

    def test_seq_search_enter_locate_and_missing_empty(self):
        steps = self.run_scenarios([
            {"op": "mount", "projectKey": "demo~a"},
            {"op": "searchCards", "query": "#21"},
            {"op": "searchCards", "query": "#999"},
            {"op": "key", "event": {"key": "/"}},
            {"op": "typeSearch", "value": "#21"},
            {"op": "key", "event": {"key": "Enter"}},
            {"op": "key", "event": {"key": "Escape"}},
            {"op": "key", "event": {"key": "/"}},
            {"op": "typeSearch", "value": "#999"},
        ])
        hit = steps[1]
        self.assertEqual(hit["count"], 1)
        self.assertEqual(hit["keys"], ["ch:alpha"])
        self.assertEqual(hit["statuses"], ["implementing"])
        miss = steps[2]
        self.assertEqual(miss["count"], 0)
        located = steps[5]
        self.assertFalse(located["searchOpen"])
        self.assertTrue(located["locating"])
        self.assertEqual(located["located"], ["ch:alpha"])
        self.assertEqual(located["scrolledTo"], "ch:alpha")
        cleared = steps[6]
        self.assertFalse(cleared["locating"])
        self.assertEqual(cleared["located"], [])
        empty_panel = steps[8]
        self.assertIn("没有匹配结果", empty_panel["resultsHtml"])

    def test_locate_dims_via_board_locating_and_blank_click_clears(self):
        steps = self.run_scenarios([
            {"op": "mount", "projectKey": "demo~a"},
            {"op": "key", "event": {"key": "/"}},
            {"op": "typeSearch", "value": "#7"},
            {"op": "key", "event": {"key": "Enter"}},
            {"op": "clickBlank"},
        ])
        located = steps[3]
        self.assertTrue(located["locating"])
        self.assertEqual(located["located"], ["ch:beta"])
        cleared = steps[4]
        self.assertFalse(cleared["locating"])
        self.assertEqual(cleared["located"], [])

    def test_collapse_persists_in_local_storage_across_remount(self):
        steps = self.run_scenarios([
            {"op": "mount", "projectKey": "proj-one"},
            {"op": "collapse", "status": "backlog"},
            {"op": "rebuildBoard", "projectKey": "proj-one"},
            {"op": "unmount"},
            {"op": "mount", "projectKey": "proj-two"},
        ])
        collapsed = steps[1]
        self.assertIn("backlog", collapsed["collapsed"])
        self.assertIn("eo-board:collapsed:proj-one", collapsed["storage"])
        self.assertIn("backlog", json.loads(collapsed["storage"]["eo-board:collapsed:proj-one"]))
        remount = steps[2]
        self.assertIn("backlog", remount["collapsed"])  # same project key restores
        other = steps[4]
        self.assertNotIn("backlog", other["collapsed"])  # different project key isolated

    def test_locate_into_collapsed_column_auto_expands(self):
        steps = self.run_scenarios([
            {"op": "mount", "projectKey": "demo~a"},
            {"op": "collapse", "status": "backlog"},
            {"op": "searchCards", "query": "BACKLOG_BODY_TOKEN"},
            {"op": "key", "event": {"key": "/"}},
            {"op": "typeSearch", "value": "BACKLOG_BODY_TOKEN"},
            {"op": "key", "event": {"key": "Enter"}},
        ])
        self.assertIn("backlog", steps[1]["collapsed"])
        self.assertEqual(steps[2]["count"], 1)
        self.assertEqual(steps[2]["statuses"], ["backlog"])
        located = steps[5]
        self.assertNotIn("backlog", located["collapsed"])  # auto expanded
        self.assertTrue(located["locating"])
        self.assertEqual(located["located"], ["bl:bl1"])

    def test_hot_refresh_clears_locate_state_but_keeps_collapse(self):
        """serve 热刷新必须走 setInterval(refreshLoop)→fetch→buildBoard，不能 unmount/mount。"""
        steps = self.run_scenarios([
            {
                "op": "mount",
                "projectKey": "demo~a",
                "serve": True,
                "dataUrl": "/p/demo~a/data.json",
            },
            {"op": "collapse", "status": "draft"},
            {"op": "blur"},
            {"op": "key", "event": {"key": "/"}},
            {"op": "typeSearch", "value": "#21"},
            {"op": "key", "event": {"key": "Enter"}},
            {
                "op": "hotRefreshPoll",
                "dataUrl": "/p/demo~a/data.json",
                "stamp": "2026-08-12 12:00:01",
            },
        ])
        mounted = steps[0]
        self.assertTrue(mounted["polling"], "DATA.serve 时应注册 refreshLoop 定时器")
        before = steps[5]
        self.assertTrue(before["locating"])
        self.assertIn("draft", before["collapsed"])
        after = steps[6]
        self.assertTrue(after["beforeLocate"])
        self.assertFalse(after["locating"])
        self.assertEqual(after["located"], [])
        self.assertIn("draft", after["collapsed"])
        # 接线证据：真实 fetch 到 DATA_URL，且未拆掉 document 监听 / 定时器
        self.assertEqual(after["fetchCalls"], 1)
        self.assertEqual(after["fetchUrl"], "/p/demo~a/data.json")
        self.assertEqual(after["fetchCache"], "no-store")
        self.assertEqual(after["keydownListeners"], after["listenersBefore"]["keydown"])
        self.assertGreater(after["keydownListeners"], 0)
        self.assertTrue(after["stillPolling"])


class SwimlaneSearchLogicAndSurfaceTests(unittest.TestCase):
    """无 node 也可跑的纯逻辑 + 源码表面断言。"""

    def setUp(self):
        self.board = load_module(f"eo_board_surface_{id(self)}", BOARD_PATH)

    def test_project_js_exposes_search_and_collapse_surface(self):
        js = self.board.PROJECT_JS.replace("\r\n", "\n")
        for needle in (
            "function openSearch",
            "function closeSearch",
            "function searchCards",
            "function locateSearchResult",
            "function clearLocate",
            "function setColumnCollapsed",
            "collapsedStorageKey",
            "document.addEventListener('keydown', keyHandler)",
            "document.removeEventListener('keydown', keyHandler)",
            "buildBoard() {\n  clearLocate()",
            "function startPolling()",
            "timer = setInterval(refreshLoop, 3000)",
            "buildHeader();\n      buildBoard();",
        ):
            self.assertIn(needle, js)
        # 生产 refreshLoop 必须把 fetch 结果接到 buildBoard（字符串锁 + 交互测双保险）
        refresh = js.split("function refreshLoop()")[1].split("timer = setInterval")[0]
        self.assertIn("fetch(DATA_URL", refresh)
        self.assertIn("buildBoard()", refresh)
        markup = self.board.PROJECT_MARKUP
        self.assertIn('id="p-search-backdrop"', markup)
        self.assertIn('id="p-search-input"', markup)

    def test_snapshot_mount_passes_project_key_for_collapse_memory(self):
        src = BOARD_PATH.read_text(encoding="utf-8")
        self.assertIn("projectKey: row.route_key", src)

    @unittest.skipUnless(NODE, "缺少 node")
    def test_keyword_and_backlog_body_match_via_search_cards(self):
        # 复用交互 runner 只跑 searchCards 步
        t = SwimlaneSearchInteractionTests("run")
        t.setUp()
        try:
            steps = t.run_scenarios([
                {"op": "mount", "projectKey": "k"},
                {"op": "searchCards", "query": "UNIQUE_BODY_TOKEN"},
                {"op": "searchCards", "query": "BACKLOG_BODY_TOKEN"},
                {"op": "searchCards", "query": "no-such-token-zzz"},
            ])
        finally:
            t.tearDown()
        self.assertEqual(steps[1]["count"], 1)
        self.assertEqual(steps[1]["keys"], ["ch:alpha"])
        self.assertEqual(steps[2]["count"], 1)
        self.assertEqual(steps[2]["statuses"], ["backlog"])
        self.assertEqual(steps[3]["count"], 0)


if __name__ == "__main__":
    unittest.main()
