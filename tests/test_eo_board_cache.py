import ast
import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import socket
from datetime import date, datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_DIR = REPO_ROOT / "cli"
BOARD_PATH = CLI_DIR / "eo-board"
VARIANT_PATH = REPO_ROOT / "eo-doc" / "changes" / "10-board-all-v2" / "design" / "variant-2.html"
BASELINE_REVISION = "792522d"
BASE_COMMIT_REVISION = "5a0247f"  # 聚合终端输出的兼容基线：此版本之后各版本须逐字节保持一致
NODE = shutil.which("node")

# 页面渲染在内嵌 JS 里，断言要落到真实产出而不是模板文本：给内嵌脚本一层最小 DOM 垫片，
# 用 node 跑一遍拿回 #topbar / #content 的 innerHTML。
NODE_RUNNER = r"""
const fs = require('fs');
const script = fs.readFileSync(process.argv[2], 'utf8');
const dataJson = fs.readFileSync(process.argv[3], 'utf8');
const els = {
  'eo-board-all-data': { textContent: dataJson },
  'topbar': { innerHTML: '' },
  'content': { innerHTML: '' },
};
globalThis.document = { getElementById: (id) => els[id] || null };
globalThis.location = { hash: process.argv[4] || '' };
globalThis.window = { addEventListener: () => {}, location: globalThis.location };
globalThis.setInterval = () => 0;
(0, eval)(script);
process.stdout.write(JSON.stringify({ topbar: els.topbar.innerHTML, content: els.content.innerHTML }));
"""

# 泳道组件是共享的：单项目页和聚合快照的 #/p/<key> 都靠它渲染。垫片补到够 mount 跑完，
# 断言落在它真正写出的看板骨架上，而不是页面里有没有那段脚本文本。
NODE_MOUNT_RUNNER = r"""
const fs = require('fs');
const [projectScript, aggScript, dataJson, projectCss, projectMarkup] =
  process.argv.slice(2, 7).map((p) => fs.readFileSync(p, 'utf8'));

function stub(name) {
  return {
    name, innerHTML: '', textContent: '', style: {}, disabled: false, _q: {},
    querySelector(sel) { return this._q[sel] || (this._q[sel] = stub(sel)); },
    querySelectorAll() { return []; },
    addEventListener() {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    parentNode: { removeChild() {} },
  };
}
const els = {};
const el = (id) => els[id] || (els[id] = stub(id));
el('eo-board-all-data').textContent = dataJson;   // 聚合快照读这个
el('eo-board-data').textContent = dataJson;       // 单项目页读这个
el('eo-project-css').textContent = projectCss;
el('eo-project-markup').textContent = projectMarkup;

globalThis.document = {
  getElementById: el,
  createElement: () => stub('created'),
  head: { appendChild() {} },
  documentElement: { classList: { add() {}, remove() {}, toggle() {} } },
  addEventListener() {}, removeEventListener() {},
};
globalThis.location = { hash: process.argv[7] || '' };
globalThis.window = { addEventListener: () => {}, location: globalThis.location };
globalThis.setInterval = () => 0;
globalThis.clearInterval = () => {};
(0, eval)(projectScript);
globalThis.EO_PROJECT = window.EO_PROJECT;  // 浏览器里 window.X= 就是全局绑定，node 里要补这一步
(0, eval)(aggScript);

const projRoot = el(process.argv[8] || 'projRoot');
const pick = (sel) => (projRoot._q[sel] ? projRoot._q[sel].innerHTML : '');
process.stdout.write(JSON.stringify({
  mountedMarkup: projRoot.innerHTML,
  projectTopbar: pick('#p-topbar'),
  projectStrip: pick('#p-strip'),
  projectBoard: pick('#p-board'),
  homeDisplay: el('homeWrap').style.display,
  aggStyleDisabled: el('aggStyle').disabled,
  homeContent: el('content').innerHTML,
}));
"""


def run_git(repo, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def load_module(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))


class BoardCacheServeTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.repo = self.root / "repo"
        self.vault = self.root / "vault"
        self.repo.mkdir()
        self.vault.mkdir()
        self.change_path = self.repo / "eo-doc" / "changes" / "01-fixture" / "change.md"
        self.change_path.parent.mkdir(parents=True)
        (self.vault / "backlog").mkdir()
        (self.vault / "roadmap.md").write_text(
            "---\nstatus: active\nphase: initial\nupdated: 2026-07-24\n---\n",
            encoding="utf-8",
        )
        self.change_path.write_text(
            "---\nid: fixture\nseq: 1\ntitle: Fixture\nstatus: draft\ntier: light\ntype: enhance\ncreated: 2026-07-24\n---\n\n"
            "# Fixture\n\n## 2. 验收清单\n- [ ] AC-1 fixture\n",
            encoding="utf-8",
        )
        (self.repo / ".eo-project.json").write_text(
            json.dumps(
                {
                    "project_name": "fixture",
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
        run_git(self.repo, "commit", "-m", "initial fixture")

        self.board = load_module(f"eo_board_test_{id(self)}", BOARD_PATH)
        self.board._BOARD_CACHE.clear()
        self.board._BOARD_BUILD_LOCKS.clear()
        self.cfg = self.board.load_project_config(self.repo / ".eo-project.json")
        self.server = None
        self.thread = None

    def tearDown(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=5)
        self.tempdir.cleanup()

    def start_server(self):
        handler = type("FixtureHandler", (self.board.BoardRequestHandler,), {"cfg": self.cfg})
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def get_json(self):
        with urlopen(f"http://127.0.0.1:{self.server.server_port}/data.json", timeout=5) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def bump_mtime(self, path):
        timestamp = time.time() + 2
        os.utime(path, (timestamp, timestamp))

    def assert_preserves(self, current, baseline, path="data"):
        """基线字段逐条仍在且取值不变；新增字段允许（数据层只增不改）。"""
        if isinstance(baseline, dict):
            self.assertIsInstance(current, dict, path)
            for key, value in baseline.items():
                self.assertIn(key, current, f"{path}.{key} 丢失")
                self.assert_preserves(current[key], value, f"{path}.{key}")
        elif isinstance(baseline, list):
            self.assertIsInstance(current, list, path)
            self.assertEqual(len(current), len(baseline), path)
            for i, value in enumerate(baseline):
                self.assert_preserves(current[i], value, f"{path}[{i}]")
        else:
            self.assertEqual(current, baseline, path)

    def test_extracted_board_matches_baseline_for_terminal_and_serve_data(self):
        baseline_source = run_git(REPO_ROOT, "show", f"{BASELINE_REVISION}:cli/eo-board").stdout
        baseline_path = self.root / "eo_board_baseline.py"
        baseline_path.write_text(baseline_source, encoding="utf-8")
        baseline = load_module(f"eo_board_baseline_{id(self)}", baseline_path)

        baseline_cfg = baseline.load_project_config(self.repo / ".eo-project.json")
        baseline_data = baseline.build_data(baseline_cfg)
        current_data = self.board.build_data(self.cfg)
        baseline_data["generated_at"] = current_data["generated_at"]
        self.assert_preserves(current_data, baseline_data)
        terminal = self.board.render_terminal(current_data)
        self.assertNotIn("TIER", terminal)
        for heading in ("SEQ", "SLUG", "TYPE", "AC", "TODO", "分支", "警告"):
            self.assertIn(heading, terminal)
        self.assertIn("fixture", terminal)

        self.start_server()
        served = self.get_json()
        served["generated_at"] = baseline_data["generated_at"]
        served["serve"] = False
        self.assert_preserves(served, baseline_data)

    def test_serve_reuses_cached_build_data_for_second_poll(self):
        calls = 0
        original_build_data = self.board.build_data

        def counted_build_data(cfg):
            nonlocal calls
            calls += 1
            return original_build_data(cfg)

        with mock.patch.object(self.board, "build_data", side_effect=counted_build_data):
            self.start_server()
            first = self.get_json()
            second = self.get_json()

        self.assertTrue(first["serve"])
        self.assertEqual(first, second)
        self.assertEqual(calls, 1)

    def test_cli_serve_exposes_change_to_the_next_three_second_client_poll(self):
        """默认 --serve 是全局 dashboard；cwd 未注册项目会临时并入，下钻 /p/<key> 仍热刷新。"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]

        eo_home = self.root / "eo-home-cli-serve"
        eo_home.mkdir()
        env = dict(os.environ)
        env["EO_HOME"] = str(eo_home)
        process = subprocess.Popen(
            [sys.executable, str(BOARD_PATH), "--serve", "--port", str(port), "--no-open"],
            cwd=self.repo,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 5
            while True:
                try:
                    with urlopen(f"http://127.0.0.1:{port}/", timeout=1) as response:
                        html = response.read().decode("utf-8")
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        self.fail("eo-board --serve did not accept requests within five seconds")
                    time.sleep(0.05)

            self.assertIn("setInterval(refreshLoop, 3000)", html)
            with urlopen(f"http://127.0.0.1:{port}/data.json", timeout=5) as response:
                home = json.loads(response.read().decode("utf-8"))
            self.assertEqual(home["scanned_count"], 1)
            route_key = home["rows"][0]["route_key"]
            self.change_path.write_text(
                self.change_path.read_text(encoding="utf-8").replace("status: draft", "status: reviewed"),
                encoding="utf-8",
            )
            self.bump_mtime(self.change_path)
            time.sleep(3.1)
            with urlopen(f"http://127.0.0.1:{port}/p/{route_key}/data.json", timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(data["changes"][0]["status"], "reviewed")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()

    def test_serve_rebuilds_when_all_freshness_inputs_change(self):
        calls = 0
        original_build_data = self.board.build_data

        def counted_build_data(cfg):
            nonlocal calls
            calls += 1
            return original_build_data(cfg)

        with mock.patch.object(self.board, "build_data", side_effect=counted_build_data):
            self.start_server()
            initial = self.get_json()
            self.assertEqual(calls, 1)

            self.change_path.write_text(
                self.change_path.read_text(encoding="utf-8").replace("status: draft", "status: reviewed"),
                encoding="utf-8",
            )
            self.bump_mtime(self.change_path)
            changed_change = self.get_json()
            self.assertEqual(changed_change["changes"][0]["status"], "reviewed")
            self.assertEqual(calls, 2)

            backlog_card = self.vault / "backlog" / "new-card.md"
            backlog_card.write_text("---\ntitle: Fresh backlog\nstatus: backlog\n---\n", encoding="utf-8")
            self.bump_mtime(backlog_card)
            changed_backlog = self.get_json()
            self.assertEqual(changed_backlog["stats"]["backlog_count"], 1)
            self.assertEqual(calls, 3)

            roadmap = self.vault / "roadmap.md"
            roadmap.write_text(
                roadmap.read_text(encoding="utf-8").replace("phase: initial", "phase: refreshed"),
                encoding="utf-8",
            )
            self.bump_mtime(roadmap)
            changed_roadmap = self.get_json()
            self.assertEqual(changed_roadmap["roadmap"]["phase"], "refreshed")
            self.assertEqual(calls, 4)

            run_git(self.repo, "branch", "ref-update")
            self.get_json()
            self.assertEqual(calls, 5)

            run_git(self.repo, "checkout", "-b", "same-sha-branch")
            changed_branch = self.get_json()
            self.assertEqual(changed_branch["worktrees"][0]["branch"], "same-sha-branch")
            self.assertEqual(calls, 6)

            before_commit_total = changed_branch["stats"]["direct_commits"]["total"]
            (self.repo / "commit-marker.txt").write_text("refresh\n", encoding="utf-8")
            run_git(self.repo, "add", "commit-marker.txt")
            run_git(self.repo, "commit", "-m", "fix: refresh source")
            changed_commit = self.get_json()
            self.assertEqual(changed_commit["stats"]["direct_commits"]["total"], before_commit_total + 1)
            self.assertEqual(calls, 7)

            import eo_lib.freshness as freshness

            class JanuaryDate(date):
                @classmethod
                def today(cls):
                    return cls(2025, 1, 24)

            class FebruaryDate(date):
                @classmethod
                def today(cls):
                    return cls(2025, 2, 24)

            with mock.patch.object(freshness, "date", JanuaryDate), mock.patch.object(self.board, "date", JanuaryDate):
                january = self.get_json()
            with mock.patch.object(freshness, "date", FebruaryDate), mock.patch.object(self.board, "date", FebruaryDate):
                february = self.get_json()
            self.assertEqual(january["stats"]["direct_commits"]["since"], "2025-01-01")
            self.assertEqual(february["stats"]["direct_commits"]["since"], "2025-02-01")
            self.assertEqual(calls, 9)
            self.assertNotEqual(initial["stats"]["direct_commits"]["since"], february["stats"]["direct_commits"]["since"])


NODE_DIVERGE_RUNNER = r"""
const fs = require('fs');
const projectJs = fs.readFileSync(process.argv[2], 'utf8');
const payload = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
function stub(name) {
  return {
    name, innerHTML: '', textContent: '', style: {}, disabled: false, _q: {},
    classList: { _s: new Set(), add(c){this._s.add(c);}, remove(c){this._s.delete(c);},
      toggle(c,on){if(on===undefined){this._s.has(c)?this._s.delete(c):this._s.add(c);}else if(on)this._s.add(c);else this._s.delete(c);},
      contains(c){return this._s.has(c);} },
    querySelector(sel){return this._q[sel]||(this._q[sel]=stub(sel));},
    querySelectorAll(sel){
      if(sel==='.detail-tab')return this._tabs||[];
      if(sel==='.detail-pane')return this._panes||[];
      if(sel&&sel.startsWith('.card'))return this._cards||[];
      return [];
    },
    addEventListener(type,fn){(this._listeners=this._listeners||{})[type]=fn;},
    setAttribute(k,v){this[k]=v;this['data-'+k]=v;},
    getAttribute(k){return this[k]||this['data-'+k]||null;},
    focus(){},
  };
}
const els={};
const el=(id)=>els[id]||(els[id]=stub(id));
el('eo-project-markup').textContent=fs.readFileSync(process.argv[4],'utf8');
el('eo-project-css').textContent='';
const root=stub('root');
const drawer=stub('p-drawer');const backdrop=stub('p-backdrop');
const pBody=stub('p-body');const pChips=stub('p-chips');const pTitle=stub('p-title');
const pClose=stub('p-close');const pBoard=stub('p-board');const pTopbar=stub('p-topbar');
const pStrip=stub('p-strip');const pWarn=stub('p-warn');
root.querySelector=(sel)=>{
  const map={'#p-drawer':drawer,'#p-backdrop':backdrop,'#p-body':pBody,
    '#p-chips':pChips,'#p-title':pTitle,'#p-close':pClose,
    '#p-board':pBoard,'#p-topbar':pTopbar,'#p-strip':pStrip,'#p-warn':pWarn,
    '#p-src-toggle':stub('p-src-toggle')};
  return map[sel]||stub(sel);
};
root.querySelectorAll=(sel)=>{if(sel==='.card[data-detail]')return root._cards||[];return [];};
globalThis.document={getElementById:el,createElement:()=>stub('created'),
  head:{appendChild(){}},documentElement:{classList:{add(){},remove(){},toggle(){}}},
  addEventListener(){},removeEventListener(){},activeElement:null};
globalThis.window={EO_PROJECT:null};
globalThis.setInterval=()=>0;globalThis.clearInterval=()=>{};
(0,eval)(projectJs);
const api=window.EO_PROJECT;
api.mount({root,data:payload.data,dataUrl:'/data.json',homeUrl:''});
const keys=[];
const re=/data-detail="(ch:[^"]+)"/g;
let m;
while((m=re.exec(pBoard.innerHTML||''))!==null){keys.push(m[1].replace(/&quot;/g,'"'));}
const extra=JSON.parse(process.argv[5]||'[]');
const details=[];
if(api.__test&&api.__test.openDetail){
  for(const key of keys.concat(extra)){api.__test.openDetail(key);details.push({key:key,body:pBody.innerHTML});}
}
process.stdout.write(JSON.stringify({keys:keys,details:details}));
"""


class BoardForkCollapseTests(BoardCacheServeTests):
    """多 worktree 下同 id change 折叠为单卡：最近活动最新者出卡，其余内容变体收进 forks。"""

    def add_side_worktree(self, branch="side"):
        side = self.root / "side-wt"
        run_git(self.repo, "worktree", "add", "-q", str(side), "-b", branch)
        return side

    def diverge_side_change(self, side, old="title: Fixture", new="title: Fixture-side"):
        sc = side / "eo-doc" / "changes" / "01-fixture" / "change.md"
        sc.write_text(sc.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
        return sc

    @staticmethod
    def _pin_mtime(path, epoch):
        os.utime(path, (epoch, epoch))

    def test_diverged_copies_collapse_to_latest_single_card(self):
        """分叉副本折叠为一张卡：动静最新的 side 副本出卡，main 副本进 forks。"""
        side = self.add_side_worktree()
        sc = self.diverge_side_change(side)
        now = time.time()
        self._pin_mtime(self.change_path, now + 100)
        self._pin_mtime(sc, now + 200)
        data = self.board.build_data(self.cfg)
        cards = [c for c in data["changes"] if c["id"] == "fixture"]
        self.assertEqual(len(cards), 1)
        card = cards[0]
        self.assertEqual(Path(card["worktree"]).resolve(), side.resolve())
        self.assertEqual(card["title"], "Fixture-side")
        self.assertTrue(card.get("diverged"))
        self.assertEqual(len(card["forks"]), 1)
        fork = card["forks"][0]
        self.assertEqual(Path(fork["worktree"]).resolve(), self.repo.resolve())
        self.assertEqual(fork["title"], "Fixture")

    def test_latest_wins_regardless_of_worktree(self):
        """main 副本动静更新时由 main 出卡：归属不看主从，只看动静先后。"""
        side = self.add_side_worktree()
        sc = self.diverge_side_change(side)
        now = time.time()
        self._pin_mtime(sc, now + 100)
        self._pin_mtime(self.change_path, now + 200)
        data = self.board.build_data(self.cfg)
        cards = [c for c in data["changes"] if c["id"] == "fixture"]
        self.assertEqual(len(cards), 1)
        self.assertEqual(Path(cards[0]["worktree"]).resolve(), self.repo.resolve())
        self.assertEqual(cards[0]["title"], "Fixture")
        self.assertEqual([f["title"] for f in cards[0]["forks"]], ["Fixture-side"])

    def test_identical_copies_merge_to_one_card(self):
        """内容一致的副本只出一张卡，无分叉标记、无 forks。"""
        self.add_side_worktree()  # 继承相同 change.md
        data = self.board.build_data(self.cfg)
        cards = [c for c in data["changes"] if c["id"] == "fixture"]
        self.assertEqual(len(cards), 1)
        self.assertFalse(cards[0].get("diverged", False))
        self.assertFalse(cards[0].get("forks"))

    def test_identical_copies_attribute_to_latest_mtime(self):
        """内容一致时仍按 change 目录动静归属，不固定落到主 worktree。"""
        side = self.add_side_worktree()
        now = time.time()
        self._pin_mtime(self.change_path, now + 100)
        self._pin_mtime(side / "eo-doc" / "changes" / "01-fixture" / "change.md", now + 200)
        data = self.board.build_data(self.cfg)
        cards = [c for c in data["changes"] if c["id"] == "fixture"]
        self.assertEqual(len(cards), 1)
        self.assertFalse(cards[0].get("diverged", False))
        self.assertEqual(Path(cards[0]["worktree"]).resolve(), side.resolve())

    def test_stale_main_does_not_inherit_other_branch_commit_time(self):
        """过期主 worktree 不能靠 git log --all 吃到其它分支提交时间。

        同状态分叉 + 两边文件 mtime 都早于新提交时，--all 会让活动尺子打平，
        再按路径降序选中主目录（PWD），出卡内容却是最老一份。HEAD 尺子必须选出
        真正提交了新正文的 side 副本。
        """
        self.change_path.write_text(
            self.change_path.read_text(encoding="utf-8")
            .replace("status: draft", "status: implementing")
            .replace("title: Fixture", "title: Fixture-old"),
            encoding="utf-8",
        )
        run_git(self.repo, "add", "eo-doc/changes/01-fixture/change.md")
        run_git(self.repo, "commit", "-m", "main old implementing")

        side = self.root / "dev-wt"
        run_git(self.repo, "worktree", "add", "-q", str(side), "-b", "side")
        sc = side / "eo-doc" / "changes" / "01-fixture" / "change.md"
        sc.write_text(
            sc.read_text(encoding="utf-8").replace("title: Fixture-old", "title: Fixture-live"),
            encoding="utf-8",
        )
        run_git(side, "add", "eo-doc/changes/01-fixture/change.md")
        run_git(side, "commit", "-m", "side live implementing")

        old = 1_700_000_000  # 2023-11，早于上述两次提交
        self._pin_mtime(self.change_path, old)
        self._pin_mtime(sc, old)

        data = self.board.build_data(self.cfg)
        cards = [c for c in data["changes"] if c["id"] == "fixture"]
        self.assertEqual(len(cards), 1)
        card = cards[0]
        self.assertEqual(Path(card["worktree"]).resolve(), side.resolve())
        self.assertEqual(card["status"], "implementing")
        self.assertEqual(card["title"], "Fixture-live")

    def test_shown_card_and_forks_carry_attribution_data(self):
        """出卡与 forks 都带归属数据（branch/worktree/status/activity），徽标计数有据。"""
        side = self.add_side_worktree()
        sc = self.diverge_side_change(side)
        now = time.time()
        self._pin_mtime(self.change_path, now + 100)
        self._pin_mtime(sc, now + 200)
        data = self.board.build_data(self.cfg)
        card = [c for c in data["changes"] if c["id"] == "fixture"][0]
        self.assertTrue(card.get("diverged"))
        self.assertEqual(card["branch"], "side")
        self.assertEqual(card["worktree_name"], "side-wt")
        fork = card["forks"][0]
        self.assertEqual(fork["branch"], "main")
        self.assertEqual(fork["worktree_name"], "repo")
        self.assertEqual(fork["title"], "Fixture")
        self.assertTrue(fork.get("activity_at"))

    @unittest.skipUnless(NODE, "缺少 node，无法渲染泳道页验证分叉卡详情")
    def test_single_card_key_and_fork_switch_in_detail(self):
        """分叉折叠后页面只渲染一张卡；详情带分叉徽标与副本列表，fork 键可切到对应副本详情。"""
        side = self.add_side_worktree()
        sc = self.diverge_side_change(side)
        now = time.time()
        self._pin_mtime(self.change_path, now + 100)
        self._pin_mtime(sc, now + 200)
        data = self.board.build_data(self.cfg)
        html = self.board.render_html(data)
        m_js = re.search(r'<script>\s*(window\.EO_PROJECT[\s\S]*?)</script>', html)
        m_markup = re.search(r'id="eo-project-markup">([\s\S]*?)</script>', html)
        self.assertIsNotNone(m_js)
        self.assertIsNotNone(m_markup)
        runner = self.root / "diverge-runner.js"
        runner.write_text(NODE_DIVERGE_RUNNER, encoding="utf-8")
        js_file = self.root / "project.js"
        js_file.write_text(m_js.group(1), encoding="utf-8")
        data_file = self.root / "payload.json"
        data_file.write_text(json.dumps({"data": data}), encoding="utf-8")
        markup_file = self.root / "markup.html"
        markup_file.write_text(m_markup.group(1), encoding="utf-8")
        proc = subprocess.run(
            [NODE, str(runner), str(js_file), str(data_file), str(markup_file),
             json.dumps(["ch:fixture@repo"])],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        # 折叠后只渲染一张卡
        self.assertEqual(result["keys"], ["ch:fixture"])
        details = {d["key"]: d["body"] for d in result["details"]}
        main_body = details["ch:fixture"]
        # 出卡详情带分叉徽标（计数 = 其余内容变体数）
        self.assertIn("分叉×1", main_body)
        self.assertIn("title: Fixture-side", main_body)
        # fork 键切换到 main 副本的详情，内容对应其 change.md
        fork_body = details["ch:fixture@repo"]
        self.assertNotEqual(main_body, fork_body)
        self.assertIn("title: Fixture", fork_body)
        self.assertNotIn("title: Fixture-side", fork_body)

    def test_serve_refreshes_latest_attribution_after_divergence(self):
        """serve 挂起时制造分叉：一个轮询周期内仍只出一张卡，归属刷新为最新副本。"""
        side = self.add_side_worktree()  # 初始一致 -> 1 card
        self.start_server()
        first = self.get_json()
        self.assertEqual(len([c for c in first["changes"] if c["id"] == "fixture"]), 1)
        sc = self.diverge_side_change(side)  # 制造分叉
        self.bump_mtime(sc)
        time.sleep(3.1)
        second = self.get_json()
        cards = [c for c in second["changes"] if c["id"] == "fixture"]
        self.assertEqual(len(cards), 1)
        self.assertEqual(Path(cards[0]["worktree"]).resolve(), side.resolve())
        self.assertEqual(len(cards[0]["forks"]), 1)

    def test_ac6_stale_lower_status_filtered(self):
        """更新的高状态副本领先时，更旧且状态更低的遗留不出卡也不进 forks。"""
        side = self.add_side_worktree()
        # main=archived（更新），side=implementing（更旧遗留）
        self.change_path.write_text(
            self.change_path.read_text(encoding="utf-8").replace("status: draft", "status: archived"),
            encoding="utf-8",
        )
        side_change = side / "eo-doc" / "changes" / "01-fixture" / "change.md"
        side_change.write_text(
            side_change.read_text(encoding="utf-8").replace("status: draft", "status: implementing"),
            encoding="utf-8",
        )
        now = time.time()
        self._pin_mtime(side_change, now + 100)
        self._pin_mtime(self.change_path, now + 200)
        data = self.board.build_data(self.cfg)
        cards = [c for c in data["changes"] if c["id"] == "fixture"]
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["status"], "archived")
        self.assertFalse(cards[0].get("diverged", False))
        self.assertFalse(cards[0].get("forks"))

    def test_newer_lower_status_copy_beats_stale_main(self):
        """主 worktree 状态更高但更旧时不能挡住正在改的新副本。"""
        side = self.add_side_worktree()
        self.change_path.write_text(
            self.change_path.read_text(encoding="utf-8")
            .replace("status: draft", "status: confirmed")
            .replace("title: Fixture", "title: Fixture-old"),
            encoding="utf-8",
        )
        side_change = side / "eo-doc" / "changes" / "01-fixture" / "change.md"
        side_change.write_text(
            side_change.read_text(encoding="utf-8")
            .replace("status: draft", "status: draft")
            .replace("title: Fixture", "title: Fixture-live"),
            encoding="utf-8",
        )
        now = time.time()
        self._pin_mtime(self.change_path, now + 100)
        self._pin_mtime(side_change, now + 200)
        data = self.board.build_data(self.cfg)
        cards = [c for c in data["changes"] if c["id"] == "fixture"]
        self.assertEqual(len(cards), 1)
        card = cards[0]
        self.assertEqual(card["title"], "Fixture-live")
        self.assertEqual(card["status"], "draft")
        self.assertEqual(Path(card["worktree"]).resolve(), side.resolve())
        self.assertEqual([f["status"] for f in card.get("forks") or []], ["confirmed"])

    def test_base_lower_keeps_higher_via_collapse(self):
        """更新的高状态副本出卡；更旧且状态更低的遗留不进 forks。"""
        side = self.add_side_worktree()
        self.change_path.write_text(
            self.change_path.read_text(encoding="utf-8").replace("status: draft", "status: implementing"),
            encoding="utf-8",
        )
        side_change = side / "eo-doc" / "changes" / "01-fixture" / "change.md"
        side_change.write_text(
            side_change.read_text(encoding="utf-8").replace("status: draft", "status: reviewed"),
            encoding="utf-8",
        )
        now = time.time()
        self._pin_mtime(self.change_path, now + 100)
        self._pin_mtime(side_change, now + 200)
        data = self.board.build_data(self.cfg)
        cards = [c for c in data["changes"] if c["id"] == "fixture"]
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["status"], "reviewed")
        self.assertEqual(Path(cards[0]["worktree"]).resolve(), side.resolve())
        self.assertFalse(cards[0].get("diverged", False))
        self.assertFalse(cards[0].get("forks"))

    def test_ac6_base_missing_change_no_filter(self):
        """AC-6: 基准没有该 change 时无阈值不过滤。"""
        side = self.add_side_worktree()
        # 只在 side 创建一个新 change，main 没有
        new_dir = side / "eo-doc" / "changes" / "02-side-only"
        new_dir.mkdir(parents=True)
        (new_dir / "change.md").write_text(
            "---\nid: side-only\nseq: 2\ntitle: Side\nstatus: draft\ntier: light\n---\n\n# Side\n",
            encoding="utf-8",
        )
        data = self.board.build_data(self.cfg)
        cards = [c for c in data["changes"] if c["id"] == "side-only"]
        self.assertEqual(len(cards), 1)
        self.assertFalse(cards[0].get("diverged", False))

    def test_group_changes_by_divergence_unit(self):
        """group_changes_by_divergence：内容一致合并、分叉分组。"""
        from eo_lib.changes import group_changes_by_divergence
        rec_a = {"path": "/a/change.md"}
        rec_b = {"path": "/b/change.md"}
        rec_c = {"path": "/c/change.md"}
        tmp = self.root / "changes"
        tmp.mkdir()
        pa, pb, pc = tmp / "a.md", tmp / "b.md", tmp / "c.md"
        pa.write_text("same", encoding="utf-8")
        pb.write_text("same", encoding="utf-8")  # 与 a 一致
        pc.write_text("different", encoding="utf-8")  # 分叉
        rec_a["path"], rec_b["path"], rec_c["path"] = str(pa), str(pb), str(pc)
        groups = group_changes_by_divergence([rec_a, rec_b, rec_c])
        self.assertEqual(len(groups), 2)  # 两组：{a,b} 和 {c}
        sizes = sorted(len(g) for g in groups)
        self.assertEqual(sizes, [1, 2])
        # 单条直接返回一组
        self.assertEqual(len(group_changes_by_divergence([rec_a])), 1)
        self.assertEqual(len(group_changes_by_divergence([])), 1)


class MultiProjectFixture(unittest.TestCase):
    """多项目 fixture 基座。EO_HOME 一律临时目录，不触碰真实 ~/.eo。

    默认 cwd 切到临时 root：全局 dashboard 会把含 .eo-project.json 的 cwd 临时并入，
    若不隔离，加载测试的真实仓库会被扫进聚合结果。
    """

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name).resolve()
        self.eo_home = self.root / "eo-home"
        self._orig_cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self._orig_cwd)

    def make_project(self, name, statuses=(), backlog_cards=0, parent=None):
        repo = (parent or self.root) / name
        repo.mkdir(parents=True)
        pm = self.root / f"{name}-pm"
        (pm / "backlog").mkdir(parents=True)
        (pm / "roadmap.md").write_text(
            "---\nstatus: active\nphase: p1\nupdated: 2026-07-25\n---\n", encoding="utf-8"
        )
        for i in range(backlog_cards):
            (pm / "backlog" / f"card-{i}.md").write_text(
                f"---\ntitle: 卡{i}\nstatus: backlog\ncreated: 2026-07-25\n---\n内容\n", encoding="utf-8"
            )
        for i, status in enumerate(statuses, start=1):
            p = repo / "eo-doc" / "changes" / f"{i:02d}-c{i}" / "change.md"
            p.parent.mkdir(parents=True)
            p.write_text(
                f"---\nid: c{i}\nseq: {i}\ntitle: C{i}\nstatus: {status}\ntier: full\ntype: feature\ncreated: 2026-07-25\n---\n\n"
                "# C\n\n## 2. 验收清单\n- [ ] AC-1 一\n",
                encoding="utf-8",
            )
        (repo / ".eo-project.json").write_text(json.dumps({
            "project_name": name,
            "mode": "vault",
            "project_root": str(pm),
            "doc_root": "eo-doc",
        }), encoding="utf-8")
        run_git(repo, "init", "-q", "-b", "main")
        run_git(repo, "config", "user.name", "t")
        run_git(repo, "config", "user.email", "t@t")
        run_git(repo, "add", "-A")
        run_git(repo, "commit", "-qm", "init")
        return repo

    def run_board(self, *args, cwd=None):
        env = dict(os.environ)
        env["EO_HOME"] = str(self.eo_home)
        return subprocess.run(
            [sys.executable, str(BOARD_PATH), *args],
            cwd=cwd or self.root, env=env, capture_output=True, text=True,
        )

    def register(self, repo):
        r = self.run_board("--register", str(repo))
        assert r.returncode == 0, r.stderr

    def registry_file(self):
        return self.eo_home / "projects.json"

    def age_change(self, repo, dirname, days):
        """把某 change 目录的最后 commit 时间与文件 mtime 一起推到 days 天前。"""
        target = repo / "eo-doc" / "changes" / dirname
        change_file = target / "change.md"
        change_file.write_text(change_file.read_text(encoding="utf-8") + "\n<!-- aged -->\n", encoding="utf-8")
        when = datetime.now().astimezone() - timedelta(days=days)
        env = dict(os.environ, GIT_AUTHOR_DATE=when.isoformat(), GIT_COMMITTER_DATE=when.isoformat())
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-qm", f"age {dirname}"], cwd=repo, env=env, check=True, capture_output=True)
        stamp = when.timestamp()
        for path in [target, *target.rglob("*")]:
            os.utime(path, (stamp, stamp))
        return when

    def age_project_sources(self, repo, name, days):
        """把项目级数据源（changes 树 + 管理侧 backlog/roadmap）mtime 一并推到过去，构造静默项目。"""
        stamp = (datetime.now().astimezone() - timedelta(days=days)).timestamp()
        for root in (self.root / f"{name}-pm", repo / "eo-doc"):
            for path in [root, *root.rglob("*")]:
                os.utime(path, (stamp, stamp))

    def load_board_module(self):
        board = load_module(f"eo_board_stream_{id(self)}", BOARD_PATH)
        board._BOARD_CACHE.clear()
        board._BOARD_BUILD_LOCKS.clear()
        return board

    def write_change(self, worktree, dirname, body_id, **fm):
        target = worktree / "eo-doc" / "changes" / dirname
        target.mkdir(parents=True, exist_ok=True)
        fields = {"id": body_id, "seq": 9, "title": f"T-{body_id}", "status": "implementing",
                  "tier": "full", "type": "feature", "created": "2026-07-25"}
        fields.update(fm)
        head = "\n".join(f"{k}: {v}" for k, v in fields.items())
        (target / "change.md").write_text(
            f"---\n{head}\n---\n\n# {fields['title']}\n\n"
            "## 2. 验收清单\n- [x] AC-1 一\n- [ ] AC-2 二\n\n"
            "## 3. TODO\n\n### Batch 1\n- [x] TODO-1 甲\n- [ ] TODO-2 乙\n",
            encoding="utf-8",
        )
        return target

    def add_acceptance_blocker(self, change_dir, unchecked=2):
        (change_dir / "acceptance.md").write_text(
            "# 人工验收单\n\n" + "".join("- [ ] 通过：待勾项\n" for _ in range(unchecked)),
            encoding="utf-8",
        )

    def snapshot_html(self, *extra, scan=None):
        out = self.root / "all.html"
        args = ["--html", "-o", str(out), "--no-open", *extra]
        if scan:
            args = ["--scan", str(scan), "--html", "-o", str(out), "--no-open", *extra]
        r = self.run_board(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        return out

    def render_snapshot(self, html_path, hash_=""):
        """把快照里的内嵌脚本用 node 跑一遍，返回 {topbar, content} 的真实 innerHTML。"""
        html = Path(html_path).read_text(encoding="utf-8")
        marker = 'id="eo-board-all-data">'
        start = html.index(marker) + len(marker)
        end = html.index("</script>", start)
        data_json = html[start:end]
        # 页面尾部那段才是聚合首页脚本（前面还有内嵌的单项目资产脚本）
        script_start = html.rindex("<script>") + len("<script>")
        script_end = html.index("</script>", script_start)

        runner = self.root / "runner.js"
        runner.write_text(NODE_RUNNER, encoding="utf-8")
        script_file = self.root / "app.js"
        script_file.write_text(html[script_start:script_end], encoding="utf-8")
        data_file = self.root / "data.json"
        data_file.write_text(data_json, encoding="utf-8")
        proc = subprocess.run(
            [NODE, str(runner), str(script_file), str(data_file), hash_],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def slice_between(self, html, opener, closer="</script>"):
        start = html.index(opener) + len(opener)
        return html[start:html.index(closer, start)]

    def mount_project_board(self, html_path, data_id, root_id, hash_=""):
        """在最小垫片里真正跑一遍挂载路径（单项目页的启动脚本 / 聚合快照的 #/p/<key> 路由），
        返回共享泳道组件写出的各块 innerHTML。"""
        html = Path(html_path).read_text(encoding="utf-8")
        markup_open = 'id="eo-project-markup">'
        markup_end = html.index("</script>", html.index(markup_open))
        project_start = html.index("<script>", markup_end) + len("<script>")
        boot_start = html.rindex("<script>") + len("<script>")
        css_open = 'id="eo-project-css">'

        files = {
            "project.js": html[project_start:html.index("</script>", project_start)],
            "boot.js": html[boot_start:html.index("</script>", boot_start)],
            "data.json": self.slice_between(html, f'id="{data_id}">'),
            "project.css": self.slice_between(html, css_open) if css_open in html else "",
            "project.html": self.slice_between(html, markup_open),
            "mount-runner.js": NODE_MOUNT_RUNNER,
        }
        for name, body in files.items():
            (self.root / name).write_text(body, encoding="utf-8")
        proc = subprocess.run(
            [NODE, str(self.root / "mount-runner.js"),
             *(str(self.root / n) for n in ("project.js", "boot.js", "data.json", "project.css", "project.html")),
             hash_, root_id],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def mount_snapshot_project(self, html_path, route_key):
        return self.mount_project_board(html_path, "eo-board-all-data", "projRoot", f"#/p/{route_key}")

    def assert_swimlane_rendered(self, mounted, change_title):
        self.assertIn('id="p-board"', mounted["mountedMarkup"])          # 骨架进了挂载点
        self.assertEqual(mounted["projectBoard"].count('<section class="col"'), 6)
        for zh in ("待办池", "草稿", "已确认", "实施中", "审查通过", "已归档"):
            self.assertIn(zh, mounted["projectBoard"])
        self.assertIn(f'<div class="card-title">{change_title}</div>', mounted["projectBoard"])


class BoardMultiProjectTests(MultiProjectFixture):
    """默认全局 dashboard / --project / --scan 多项目聚合与下钻（终端形态）。"""

    def test_all_one_row_per_project_with_counts_and_as_of(self):
        a = self.make_project("alpha", statuses=("confirmed", "implementing", "archived"), backlog_cards=2)
        b = self.make_project("beta", statuses=("draft",))
        self.register(a)
        self.register(b)
        r = self.run_board()
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        row_a = next(l for l in lines if l.strip().startswith("alpha"))
        row_b = next(l for l in lines if l.strip().startswith("beta"))
        # 列序：draft confirmed implementing reviewed archived backlog as-of
        self.assertRegex(row_a, r"alpha\s+0\s+1\s+1\s+0\s+1\s+2\s+\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
        self.assertRegex(row_b, r"beta\s+1\s+0\s+0\s+0\s+0\s+0\s+\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

    def test_all_invalid_entry_shows_error_row_without_breaking_others(self):
        a = self.make_project("alpha", statuses=("confirmed",))
        self.register(a)
        data = json.loads(self.registry_file().read_text(encoding="utf-8"))
        data["projects"].append({"name": "ghost", "path": str(self.root / "gone"), "registered_at": "2026-07-25"})
        self.registry_file().write_text(json.dumps(data), encoding="utf-8")
        r = self.run_board()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("alpha", r.stdout)
        self.assertIn("ghost", r.stdout)
        self.assertIn("✗", r.stdout)

    def test_all_structural_bad_entry_isolated_to_own_row(self):
        a = self.make_project("alpha", statuses=("confirmed",))
        self.register(a)
        data = json.loads(self.registry_file().read_text(encoding="utf-8"))
        data["projects"].append({"name": "bad", "path": 123})
        self.registry_file().write_text(json.dumps(data), encoding="utf-8")
        r = self.run_board()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("alpha", r.stdout)  # 有效项目照常输出
        self.assertIn("非法", r.stdout)

    def test_scan_dedups_same_repo_worktrees(self):
        a = self.make_project("alpha")
        self.register(a)
        parent = self.root / "scan-parent"
        orphan = self.make_project("orphan", statuses=("draft",), parent=parent)
        run_git(orphan, "worktree", "add", "-q", str(parent / "orphan-wt"), "-b", "side")
        r = self.run_board("--scan", str(parent))
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = [l for l in r.stdout.splitlines() if "(未注册)" in l and not l.startswith("提示")]
        self.assertEqual(len(rows), 1)  # 同仓主/linked worktree 只一行

    def test_all_empty_registry_prints_guidance(self):
        r = self.run_board()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--register", r.stdout)

    def test_project_by_name_and_by_path_from_anywhere(self):
        a = self.make_project("alpha", statuses=("confirmed",))
        self.register(a)
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        by_name = self.run_board("--project", "alpha", cwd=elsewhere)
        self.assertEqual(by_name.returncode, 0, by_name.stderr)
        self.assertIn("eo board · alpha", by_name.stdout)
        by_path = self.run_board("--project", str(a), cwd=elsewhere)
        self.assertEqual(by_path.returncode, 0, by_path.stderr)
        self.assertIn("eo board · alpha", by_path.stdout)

    def test_project_name_ambiguity_lists_candidates(self):
        a = self.make_project("dup", parent=self.root / "d1")
        b = self.make_project("dup2", parent=self.root / "d2")
        # 第二个项目改成同注册名（配置同名，路径不同）
        cfg = json.loads((b / ".eo-project.json").read_text(encoding="utf-8"))
        cfg["project_name"] = "dup"
        (b / ".eo-project.json").write_text(json.dumps(cfg), encoding="utf-8")
        self.register(a)
        self.register(b)
        r = self.run_board("--project", "dup", cwd=self.root)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("命中多个", r.stderr)
        self.assertIn(str(a.resolve()), r.stderr)
        self.assertIn(str(b.resolve()), r.stderr)

    def test_scan_merges_unregistered_without_writing_registry(self):
        a = self.make_project("alpha")
        self.register(a)
        before = self.registry_file().read_bytes()
        parent = self.root / "scan-parent"
        self.make_project("orphan", statuses=("draft",), parent=parent)
        r = self.run_board("--scan", str(parent))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("orphan (未注册)", r.stdout)
        self.assertIn("--register", r.stdout)
        self.assertEqual(self.registry_file().read_bytes(), before)

    def test_all_flag_is_retired_with_guidance(self):
        r = self.run_board("--all")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("已退役", r.stderr)
        self.assertIn("去掉该旗标", r.stderr)

    def test_scan_works_on_default_dashboard_without_all(self):
        parent = self.root / "scan-parent"
        self.make_project("orphan", statuses=("draft",), parent=parent)
        r = self.run_board("--scan", str(parent))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("orphan (未注册)", r.stdout)

    def test_scan_rejects_with_project(self):
        r = self.run_board("--scan", str(self.root), "--project", "x")
        self.assertNotEqual(r.returncode, 0)


class BoardAllStreamDataTests(MultiProjectFixture):
    """聚合数据抬升：route_key、项目级元信息、非 archived change 明细、activity_at 与 3 天活跃窗。"""

    def env_patch(self):
        return mock.patch.dict(os.environ, {"EO_HOME": str(self.eo_home)})

    def test_rows_carry_route_key_project_meta_and_non_archived_changes(self):
        alpha = self.make_project("alpha", statuses=("confirmed", "implementing", "archived"), backlog_cards=2)
        self.register(alpha)
        board = self.load_board_module()
        with self.env_patch():
            agg = board.build_all_data()
        row = agg["rows"][0]
        self.assertEqual(row["label"], "alpha")
        self.assertEqual(row["route_key"], board.make_route_key("alpha", alpha))
        self.assertEqual(row["main_branch"], "main")
        self.assertEqual(row["worktree_count"], 1)
        self.assertEqual(row["path"], str(alpha))
        self.assertIsNotNone(row["activity_at"])
        self.assertTrue(row["active"])
        self.assertEqual([c["status"] for c in row["changes"]], ["confirmed", "implementing"])
        first = row["changes"][0]
        self.assertEqual(
            {first["seq"], first["id"], first["tier"], first["type"], first["project"]},
            {1, "c1", "full", "feature", "alpha"},
        )
        self.assertEqual((first["ac_done"], first["ac_total"]), (0, 1))
        self.assertEqual((first["todo_done"], first["todo_total"]), (None, None))
        self.assertEqual(first["route_key"], row["route_key"])
        self.assertTrue(first["is_default_worktree"])
        self.assertIsNone(first["blocker"])

    def test_route_key_separates_same_named_projects_and_encodes_cjk(self):
        one = self.make_project("同名", parent=self.root / "one")
        two = self.make_project("同名2", parent=self.root / "two")
        cfg = json.loads((two / ".eo-project.json").read_text(encoding="utf-8"))
        cfg["project_name"] = "同名"
        (two / ".eo-project.json").write_text(json.dumps(cfg), encoding="utf-8")
        self.register(one)
        self.register(two)
        board = self.load_board_module()
        with self.env_patch():
            agg = board.build_all_data()
        keys = [r["route_key"] for r in agg["rows"]]
        self.assertEqual(len(set(keys)), 2)
        for key in keys:
            self.assertTrue(key.startswith("%E5%90%8C%E5%90%8D~"), key)
            self.assertNotIn("/", key)

    def test_uncommitted_edit_moves_change_activity_ahead_of_older_sibling(self):
        alpha = self.make_project("alpha", statuses=("implementing", "implementing"))
        self.register(alpha)
        self.age_change(alpha, "01-c1", days=6)
        self.age_change(alpha, "02-c2", days=5)
        board = self.load_board_module()
        with self.env_patch():
            before = {c["id"]: c for c in board.build_all_data()["rows"][0]["changes"]}
        self.assertLess(before["c1"]["activity_at"], before["c2"]["activity_at"])
        self.assertFalse(before["c1"]["active"])

        edited = alpha / "eo-doc" / "changes" / "01-c1" / "change.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\n未提交编辑\n", encoding="utf-8")
        with self.env_patch():
            after = board.build_all_data()["rows"][0]["changes"]
        self.assertEqual(sorted(after, key=lambda c: c["activity_at"], reverse=True)[0]["id"], "c1")
        by_id = {c["id"]: c for c in after}
        self.assertTrue(by_id["c1"]["active"])
        # last_touch 仍是那次旧 commit 的日粒度日期——排序键换成 activity_at 才看得见未提交编辑
        self.assertLess(by_id["c1"]["activity_at"][:10], date.today().isoformat() + "T")

    def test_active_flag_splits_on_three_day_boundary(self):
        alpha = self.make_project("alpha", statuses=("implementing", "implementing"))
        self.register(alpha)
        self.age_change(alpha, "01-c1", days=2)
        self.age_change(alpha, "02-c2", days=4)
        board = self.load_board_module()
        with self.env_patch():
            changes = {c["id"]: c for c in board.build_all_data()["rows"][0]["changes"]}
        self.assertTrue(changes["c1"]["active"])
        self.assertFalse(changes["c2"]["active"])

    def test_silent_project_row_loses_active_flag(self):
        quiet = self.make_project("quiet", statuses=("implementing",))
        self.register(quiet)
        self.age_change(quiet, "01-c1", days=9)
        self.age_project_sources(quiet, "quiet", days=9)
        board = self.load_board_module()
        with self.env_patch():
            row = board.build_all_data()["rows"][0]
        self.assertFalse(row["active"])
        self.assertFalse(row["changes"][0]["active"])

    def test_stream_entries_match_the_project_own_board_records(self):
        alpha = self.make_project("alpha", statuses=("implementing", "archived"))
        self.register(alpha)
        board = self.load_board_module()
        with self.env_patch():
            row = board.build_all_data()["rows"][0]
        own = board.build_data(board.load_project_config(alpha / ".eo-project.json"))
        by_id = {c["id"]: c for c in own["changes"]}
        self.assertEqual([c["id"] for c in row["changes"]], ["c1"])
        for entry in row["changes"]:
            rec = by_id[entry["id"]]
            self.assertEqual(
                (entry["seq"], entry["status"], entry["tier"], entry["type"], entry["activity_at"],
                 entry["blocker"], entry["branch"], entry["worktree_name"]),
                (rec["seq"], rec["status"], rec["tier"], rec["type"], rec["activity_at"],
                 rec["blocker"], rec["branch"], rec["worktree_name"]),
            )
            self.assertEqual((entry["ac_done"], entry["ac_total"]), board.count_ac(rec["ac"]))

    def test_fresh_and_cached_getters_produce_identical_rows(self):
        self.register(self.make_project("alpha", statuses=("confirmed", "archived"), backlog_cards=1))
        self.register(self.make_project("beta", statuses=("implementing",)))
        board = self.load_board_module()
        with self.env_patch():
            fresh = board.build_all_data()
            cached = board.build_all_data(get_entry=board._get_board_entry_cached)

        def comparable(agg):
            rows = []
            for row in sorted(agg["rows"], key=lambda r: r["label"]):
                row = dict(row)
                row.pop("as_of")
                rows.append(row)
            return rows

        self.assertEqual(comparable(fresh), comparable(cached))


@unittest.skipUnless(NODE, "缺少 node，无法在无浏览器环境渲染内嵌视图")
class BoardAllHomeViewTests(MultiProjectFixture):
    """首页壳：change 流视图字段/排序/降权、项目摘要条卡、双视图切换框架、下钻链接。"""

    def build_scene(self):
        alpha = self.make_project("alpha", statuses=("implementing", "archived"), backlog_cards=2)
        # 先做旧，再开侧枝：否则侧枝 ref 上留着那条「现在」的 init commit，
        # `git log --all -1` 按提交时间取最新，01-c1 永远读不到被做旧的时间
        self.age_change(alpha, "01-c1", days=5)
        side = self.root / "alpha-side"
        run_git(alpha, "worktree", "add", "-q", str(side), "-b", "side")
        hot = self.write_change(side, "03-hot", "hot", seq=3, summary="侧枝上的热变更")
        self.add_acceptance_blocker(hot, unchecked=2)
        beta = self.make_project("beta")
        self.write_change(beta, "01-bcool", "bcool", seq=2, status="draft", summary="beta 的变更")
        self.age_change(beta, "01-bcool", days=1)
        self.register(alpha)
        self.register(beta)
        return alpha, beta

    def test_stream_rows_carry_fields_sort_by_activity_and_dim_silent_tail(self):
        self.build_scene()
        content = self.render_snapshot(self.snapshot_html())["content"]

        self.assertIn("进行中 change <b>3</b>", content)
        self.assertIn("跨项目 · 最近活动倒序 · 不含 archived（1 归档见项目栏）", content)
        self.assertIn('<span class="chip blocker-sum">⛔ blocker <b>1</b></span>', content)

        # 行字段：seq+slug、状态、tier·type、summary、进度、非主 worktree 标记、blocker
        self.assertIn("#3 hot", content)
        self.assertIn("实施中", content)
        self.assertIn("<b>full</b>·feature", content)
        self.assertIn("侧枝上的热变更", content)
        self.assertIn('<span class="tag branch wt-split"><span class="wt-line">⎇ side</span><span class="wt-line">alpha-side</span></span>', content)
        self.assertIn('<span class="tag warn">⛔ 人工验收 2 项待勾</span>', content)
        self.assertIn('<span class="prog-num">1/2</span>', content)

        # 排序：未提交的侧枝变更最新 → 流顶；5 天前的 c1 落到降权分界之后
        self.assertLess(content.index("#3 hot"), content.index("#2 bcool"))
        self.assertEqual(content.count('class="divider"'), 1)
        self.assertLess(content.index("#2 bcool"), content.index('class="divider"'))
        self.assertLess(content.index('class="divider"'), content.index("#1 c1"))
        self.assertIn("以下 3 天内无动静", content)
        self.assertEqual(content.count('class="row dim"'), 1)
        self.assertEqual(content.count('class="row"'), 2)
        self.assertNotIn("#2 c2", content)  # archived 不进流

    def test_project_strip_cards_show_meta_and_both_entries_link_to_route(self):
        alpha, _ = self.build_scene()
        board = self.load_board_module()
        key = board.make_route_key("alpha", alpha)
        content = self.render_snapshot(self.snapshot_html())["content"]

        self.assertIn('<a class="proj" href="#/p/' + key + '"', content)
        self.assertIn('<a class="row" href="#/p/' + key + '"', content)
        self.assertIn("⎇ main · 2 worktree", content)
        self.assertIn(str(alpha), content)  # 条卡带目录
        self.assertIn("<b>2</b>backlog", content)
        self.assertIn("as-of ", content)
        self.assertIn('<span class="pill live">● 活跃</span>', content)

    def test_silent_project_card_is_desaturated_but_still_listed(self):
        quiet = self.make_project("quiet", statuses=("implementing",))
        self.register(quiet)
        self.age_change(quiet, "01-c1", days=8)
        self.age_project_sources(quiet, "quiet", days=8)
        content = self.render_snapshot(self.snapshot_html())["content"]
        self.assertIn('class="proj silent"', content)
        self.assertIn('<span class="pill quiet">静默 · 最后动静 8 天前</span>', content)

    def test_view_switch_lives_in_topbar_defaults_to_stream_and_remembers_hash(self):
        self.build_scene()
        html = self.snapshot_html()

        default = self.render_snapshot(html)
        self.assertIn('<div class="viewswitch"', default["topbar"])
        self.assertIn('<a class="vs-btn" href="#/" aria-current="page">change 流</a>', default["topbar"])
        self.assertIn('<a class="vs-btn" href="#/cards">概要卡</a>', default["topbar"])
        self.assertIn('class="list"', default["content"])

        cards = self.render_snapshot(html, "#/cards")
        self.assertIn('<a class="vs-btn" href="#/cards" aria-current="page">概要卡</a>', cards["topbar"])
        self.assertIn('class="grid"', cards["content"])
        self.assertNotIn('class="list"', cards["content"])

    def test_stream_markup_stays_within_variant2_class_vocabulary(self):
        self.build_scene()
        content = self.render_snapshot(self.snapshot_html())["content"]

        def classes(text):
            return {t for attr in re.findall(r'class="([^"]*)"', text) for t in attr.split()}

        variant = classes(VARIANT_PATH.read_text(encoding="utf-8"))
        # 定稿稿没有的边界态：未注册徽标、坏条目错误行、空流提示、分支标签
        extra = {"unreg", "proj-err", "proj-note", "list-empty", "branch", "wt-split", "wt-line"}
        self.assertLessEqual(classes(content) - extra, variant)
        for anchor in ("strip", "proj", "list", "list-head", "row", "r-proj", "r-main",
                       "r-prog", "r-when", "divider", "st-pill", "bar", "todo", "ac"):
            self.assertIn(anchor, classes(content), anchor)


@unittest.skipUnless(NODE, "缺少 node，无法在无浏览器环境渲染内嵌视图")
class BoardAllCardsViewTests(MultiProjectFixture):
    """概要卡视图：并入切换框架、卡片可点下钻、信息面不低于改版前。"""

    def test_cards_view_keeps_every_field_of_the_previous_summary_card(self):
        alpha = self.make_project("alpha", statuses=("confirmed", "implementing"), backlog_cards=3)
        self.register(alpha)
        cfg = json.loads((alpha / ".eo-project.json").read_text(encoding="utf-8"))
        cfg["project_name"] = "alpha-renamed"
        (alpha / ".eo-project.json").write_text(json.dumps(cfg), encoding="utf-8")
        parent = self.root / "scan-parent"
        self.make_project("orphan", statuses=("draft",), parent=parent)
        data = json.loads(self.registry_file().read_text(encoding="utf-8"))
        data["projects"].append({"name": "ghost", "path": str(self.root / "gone"), "registered_at": "2026-07-25"})
        self.registry_file().write_text(json.dumps(data), encoding="utf-8")

        content = self.render_snapshot(self.snapshot_html(scan=parent), "#/cards")["content"]
        self.assertIn('class="grid"', content)
        self.assertIn("alpha-renamed", content)                       # 项目名
        self.assertIn(str(alpha), content)                            # 路径
        self.assertIn("as-of ", content)                              # 新鲜度戳
        for _, zh in (("draft", "草稿"), ("confirmed", "已确认"), ("implementing", "实施中"),
                      ("reviewed", "审查通过"), ("archived", "已归档")):
            self.assertIn(zh, content)                                # 五状态计数
        self.assertIn("<b>3</b>backlog", content)                     # backlog 数
        self.assertIn("注册名 alpha 与项目配置不一致", content)          # 名不一致提示
        self.assertIn('<span class="pill unreg">未注册</span>', content)  # 未注册徽标
        self.assertIn("路径失效或缺 .eo-project.json", content)          # 坏条目行内错误

    def test_cards_are_clickable_and_bad_entries_are_not(self):
        alpha = self.make_project("alpha", statuses=("confirmed",))
        self.register(alpha)
        data = json.loads(self.registry_file().read_text(encoding="utf-8"))
        data["projects"].append({"name": "ghost", "path": str(self.root / "gone"), "registered_at": "2026-07-25"})
        self.registry_file().write_text(json.dumps(data), encoding="utf-8")
        board = self.load_board_module()
        key = board.make_route_key("alpha", alpha)

        content = self.render_snapshot(self.snapshot_html(), "#/cards")["content"]
        self.assertIn('<a class="proj" href="#/p/' + key + '"', content)
        self.assertEqual(content.count('<a class="proj"'), 1)          # 坏条目不可点
        self.assertIn('<div class="proj">', content)

    def test_unknown_project_hash_falls_back_to_guidance_with_home_link(self):
        self.register(self.make_project("alpha"))
        content = self.render_snapshot(self.snapshot_html(), "#/p/gone~00000000")["content"]
        self.assertIn("这份快照里没有该项目的泳道数据", content)
        self.assertIn('href="#/"', content)


class BoardAllRouteTests(MultiProjectFixture):
    """serve 路由 /p/<route_key>：分派、数据端点、返回入口、未知 key 指引、跨槽缓存。"""

    def env_patch(self):
        return mock.patch.dict(os.environ, {"EO_HOME": str(self.eo_home)})

    def start(self, board, scan_dir=None):
        handler = type("RouteHandler", (board.AllBoardRequestHandler,), {"scan_dir": scan_dir})
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server

    def fetch(self, server, path):
        with urlopen(f"http://127.0.0.1:{server.server_port}{path}", timeout=5) as response:
            return response.status, response.read().decode("utf-8")

    def fetch_status(self, server, path):
        try:
            return self.fetch(server, path)
        except HTTPError as e:
            with e:
                return e.code, e.read().decode("utf-8")

    def test_project_route_serves_swimlane_page_with_own_data_endpoint_and_home_link(self):
        alpha = self.make_project("alpha", statuses=("implementing",))
        self.register(alpha)
        board = self.load_board_module()
        key = board.make_route_key("alpha", alpha)
        with self.env_patch():
            server = self.start(board)
            status, html = self.fetch(server, f"/p/{key}")
            _, raw = self.fetch(server, f"/p/{key}/data.json")
        self.assertEqual(status, 200)
        self.assertIn("← 返回首页", html)
        self.assertIn(f"dataUrl: '/p/{key}/data.json'", html)
        self.assertIn("homeUrl: '/'", html)
        self.assertIn("setInterval(refreshLoop, 3000)", html)
        data = json.loads(raw)
        self.assertEqual(data["project"]["name"], "alpha")
        self.assertTrue(data["serve"])
        self.assertEqual([c["id"] for c in data["changes"]], ["c1"])

    def test_same_named_projects_and_renamed_registration_reach_their_own_lane(self):
        one = self.make_project("同名", statuses=("draft",), parent=self.root / "one")
        two = self.make_project("同名2", statuses=("reviewed",), parent=self.root / "two")
        cfg = json.loads((two / ".eo-project.json").read_text(encoding="utf-8"))
        cfg["project_name"] = "同名"
        (two / ".eo-project.json").write_text(json.dumps(cfg), encoding="utf-8")
        self.register(one)
        self.register(two)
        board = self.load_board_module()
        key_one = board.make_route_key("同名", one)
        key_two = board.make_route_key("同名", two)
        self.assertNotEqual(key_one, key_two)
        with self.env_patch():
            server = self.start(board)
            first = json.loads(self.fetch(server, f"/p/{key_one}/data.json")[1])
            second = json.loads(self.fetch(server, f"/p/{key_two}/data.json")[1])
        self.assertEqual([c["status"] for c in first["changes"]], ["draft"])
        self.assertEqual([c["status"] for c in second["changes"]], ["reviewed"])

    def test_scan_merged_unregistered_project_is_drillable_too(self):
        self.register(self.make_project("alpha"))
        parent = self.root / "scan-parent"
        orphan = self.make_project("orphan", statuses=("confirmed",), parent=parent)
        board = self.load_board_module()
        key = board.make_route_key("orphan", orphan)
        with self.env_patch():
            server = self.start(board, scan_dir=str(parent))
            status, raw = self.fetch(server, f"/p/{key}/data.json")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["project"]["name"], "orphan")

    def test_unknown_and_stale_routes_return_guidance_page_not_a_crash(self):
        alpha = self.make_project("alpha")
        self.register(alpha)
        board = self.load_board_module()
        stale = board.make_route_key("alpha", self.root / "moved-away")
        with self.env_patch():
            server = self.start(board)
            for path in (f"/p/{stale}", "/p/", "/p/%E4%B8%8D%E5%AD%98~deadbeef", "/nope"):
                code, body = self.fetch_status(server, path)
                self.assertEqual(code, 404, path)
                self.assertIn('href="/"', body, path)
                self.assertIn("返回首页", body, path)
                self.assertIn("alpha", body, path)  # 指引页列出当前可下钻项目

    def test_home_page_links_match_the_routes_the_server_answers(self):
        alpha = self.make_project("alpha", statuses=("implementing",))
        beta = self.make_project("beta", statuses=("draft",))
        self.register(alpha)
        self.register(beta)
        board = self.load_board_module()
        with self.env_patch():
            server = self.start(board)
            _, raw = self.fetch(server, "/data.json")
            keys = [row["route_key"] for row in json.loads(raw)["rows"]]
            for key in keys:
                self.assertEqual(self.fetch(server, f"/p/{key}")[0], 200, key)
        self.assertEqual(len(keys), 2)

    def test_edited_change_becomes_the_freshest_row_on_the_next_poll(self):
        alpha = self.make_project("alpha", statuses=("implementing",))
        beta = self.make_project("beta", statuses=("implementing",))
        self.register(alpha)
        self.register(beta)
        self.age_change(alpha, "01-c1", days=4)
        board = self.load_board_module()
        with self.env_patch():
            server = self.start(board)
            before = json.loads(self.fetch(server, "/data.json")[1])
            stale = next(c for r in before["rows"] for c in r["changes"] if c["project"] == "alpha")
            self.assertFalse(stale["active"])

            edited = alpha / "eo-doc" / "changes" / "01-c1" / "change.md"
            edited.write_text(edited.read_text(encoding="utf-8") + "\n改一笔\n", encoding="utf-8")
            after = json.loads(self.fetch(server, "/data.json")[1])

        stream = [c for r in after["rows"] for c in r["changes"]]
        top = max(stream, key=lambda c: c["activity_at"])
        self.assertEqual(top["project"], "alpha")
        self.assertTrue(top["active"])

    def test_two_lanes_polled_concurrently_keep_separate_cache_slots(self):
        self.register(self.make_project("alpha", statuses=("confirmed",)))
        self.register(self.make_project("beta", statuses=("draft",)))
        board = self.load_board_module()
        calls = 0
        original = board.build_data
        lock = threading.Lock()
        overlap = threading.Barrier(2, timeout=15)

        def counted(cfg):
            nonlocal calls
            with lock:
                calls += 1
            overlap.wait()
            return original(cfg)

        with self.env_patch():
            keys = {cfg["project_name"]: key for key, cfg in board.build_route_map().items()}
            with mock.patch.object(board, "build_data", side_effect=counted):
                server = self.start(board)
                seen = {}

                def hit(name):
                    seen.setdefault(name, []).append(
                        json.loads(self.fetch(server, f"/p/{keys[name]}/data.json")[1])
                    )

                threads = [threading.Thread(target=hit, args=(n,)) for n in ("alpha", "beta") for _ in range(3)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join(timeout=30)
                self.assertEqual(calls, 2)  # 同槽 3 路并发单飞，双槽并行各 +1
                json.loads(self.fetch(server, f"/p/{keys['alpha']}/data.json")[1])
                self.assertEqual(calls, 2)  # 稳定键重复请求不重扫

        self.assertEqual(len(seen["alpha"]), 3)
        self.assertEqual(len(seen["beta"]), 3)
        for name in ("alpha", "beta"):
            for payload in seen[name]:
                self.assertEqual(payload["project"]["name"], name)


class BoardAllSnapshotRouteTests(MultiProjectFixture):
    """默认 --html 快照：内嵌全量泳道数据、同一套 route_key、零外部请求。"""

    def test_snapshot_embeds_full_board_for_every_project_including_scanned(self):
        alpha = self.make_project("alpha", statuses=("implementing", "archived"), backlog_cards=1)
        self.register(alpha)
        parent = self.root / "scan-parent"
        orphan = self.make_project("orphan", statuses=("draft",), parent=parent)
        out = self.root / "all.html"
        r = self.run_board("--scan", str(parent), "--html", "-o", str(out), "--no-open")
        self.assertEqual(r.returncode, 0, r.stderr)
        html = out.read_text(encoding="utf-8")

        marker = 'id="eo-board-all-data">'
        start = html.index(marker) + len(marker)
        agg = json.loads(html[start:html.index("</script>", start)])
        board = self.load_board_module()
        by_label = {row["label"]: row for row in agg["rows"]}
        self.assertEqual(sorted(by_label), ["alpha", "orphan"])
        self.assertEqual(by_label["alpha"]["route_key"], board.make_route_key("alpha", alpha))
        self.assertEqual(by_label["orphan"]["route_key"], board.make_route_key("orphan", orphan))
        for label, path in (("alpha", alpha), ("orphan", orphan)):
            board_data = by_label[label]["board"]
            own = board.build_data(board.load_project_config(path / ".eo-project.json"))
            self.assertEqual([c["id"] for c in board_data["changes"]], [c["id"] for c in own["changes"]])
            self.assertFalse(board_data["serve"])  # 快照不轮询
        self.assertIn('id="eo-project-css"', html)
        self.assertIn('id="eo-project-markup"', html)
        self.assertIn("window.EO_PROJECT", html)

    @unittest.skipUnless(NODE, "缺少 node，无法在无浏览器环境执行挂载路径")
    def test_snapshot_hash_route_really_mounts_the_shared_project_board(self):
        alpha = self.make_project("alpha", statuses=("implementing", "archived"), backlog_cards=2)
        self.register(alpha)
        board = self.load_board_module()
        key = board.make_route_key("alpha", alpha)

        mounted = self.mount_snapshot_project(self.snapshot_html(), key)
        self.assert_swimlane_rendered(mounted, "C1")
        self.assertEqual(mounted["homeDisplay"], "none")                 # 首页让位
        self.assertTrue(mounted["aggStyleDisabled"])                     # 两套样式表互斥
        self.assertEqual(mounted["homeContent"], "")                     # 没有回落到首页渲染
        self.assertIn('class="card dim"', mounted["projectBoard"])       # 归档卡降权
        self.assertEqual(mounted["projectBoard"].count('<article class="card'), 4)  # 2 change + 2 backlog
        self.assertIn("← 返回首页", mounted["projectTopbar"])
        self.assertIn('href="#/"', mounted["projectTopbar"])
        self.assertIn("alpha", mounted["projectStrip"])

    @unittest.skipUnless(NODE, "缺少 node，无法在无浏览器环境执行挂载路径")
    def test_project_html_opens_swimlane_via_initial_route_with_home_link(self):
        alpha = self.make_project("alpha", statuses=("implementing", "archived"), backlog_cards=1)
        self.register(alpha)
        beta = self.make_project("beta", statuses=("draft",))
        self.register(beta)
        board = self.load_board_module()
        key = board.make_route_key("alpha", alpha)
        out = self.root / "project.html"
        r = self.run_board("--project", "alpha", "--html", "-o", str(out), "--no-open")
        self.assertEqual(r.returncode, 0, r.stderr)

        # --project --html 走聚合快照壳 + initial_route，挂载点仍是 projRoot
        mounted = self.mount_snapshot_project(out, key)
        self.assert_swimlane_rendered(mounted, "C1")
        self.assertIn("← 返回首页", mounted["projectTopbar"])
        self.assertIn('class="project-switch"', mounted["projectTopbar"])
        self.assertIn("alpha", mounted["projectStrip"])

    def test_snapshot_is_self_contained_with_no_outbound_requests(self):
        self.register(self.make_project("alpha", statuses=("implementing",)))
        html = self.snapshot_html().read_text(encoding="utf-8")
        remote = [u for u in re.findall(r'https?://[^\s"\'<>)]+', html) if "www.w3.org/2000/svg" not in u]
        self.assertEqual(remote, [])
        self.assertNotIn("<script src", html)
        self.assertNotIn('<link rel="stylesheet"', html)
        self.assertNotIn("__EO_", html)  # 占位符全部替换干净

    def test_serve_home_page_does_not_carry_snapshot_only_project_assets(self):
        self.register(self.make_project("alpha"))
        board = self.load_board_module()
        with mock.patch.dict(os.environ, {"EO_HOME": str(self.eo_home)}):
            html = board.render_all_html(board.build_all_serve_data(None))
        self.assertNotIn('id="eo-project-css"', html)
        self.assertNotIn("__EO_PROJECT_ASSETS__", html)


class BoardAllRegressionTests(MultiProjectFixture):
    """回归收口：坏条目隔离、终端输出不变、宪法静态核对、用户文档口径。"""

    def env_patch(self):
        return mock.patch.dict(os.environ, {"EO_HOME": str(self.eo_home)})

    def test_bad_entries_stay_out_of_the_stream_without_breaking_healthy_ones(self):
        alpha = self.make_project("alpha", statuses=("implementing",))
        self.register(alpha)
        registry = json.loads(self.registry_file().read_text(encoding="utf-8"))
        registry["projects"].append({"name": "ghost", "path": str(self.root / "gone"), "registered_at": "2026-07-25"})
        registry["projects"].append({"name": "bad", "path": 123})
        self.registry_file().write_text(json.dumps(registry), encoding="utf-8")
        board = self.load_board_module()
        with self.env_patch():
            agg = board.build_all_data()

        healthy = [r for r in agg["rows"] if not r["error"]]
        broken = [r for r in agg["rows"] if r["error"]]
        self.assertEqual([r["label"] for r in healthy], ["alpha"])
        self.assertEqual(len(broken), 2)
        self.assertEqual(len(healthy[0]["changes"]), 1)
        for row in broken:
            self.assertEqual(row.get("changes", []), [])   # 坏条目不往流里塞行
            self.assertIsNone(row.get("route_key"))        # 也不可点

        if NODE:
            content = self.render_snapshot(self.snapshot_html())["content"]
            self.assertIn("进行中 change <b>1</b>", content)
            self.assertEqual(content.count('class="row'), 1)
            self.assertEqual(content.count('class="proj-err"'), 2)

    def test_all_terminal_table_body_stays_compatible_aside_from_global_header(self):
        self.register(self.make_project("alpha", statuses=("confirmed", "implementing", "archived"), backlog_cards=2))
        self.register(self.make_project("beta", statuses=("draft",)))
        baseline_path = self.root / "eo_board_base.py"
        baseline_path.write_text(
            run_git(REPO_ROOT, "show", f"{BASE_COMMIT_REVISION}:cli/eo-board").stdout, encoding="utf-8"
        )
        baseline = load_module(f"eo_board_base_{id(self)}", baseline_path)
        board = self.load_board_module()

        def normalized(text):
            # 表头从 "eo board --all ·" 收敛为 "eo board · 全局 dashboard ·"；只锁表体与指引尾
            text = re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "<as-of>", text)
            lines = text.splitlines()
            if lines:
                lines[0] = re.sub(
                    r"^eo board(?: --all)? · (?:全局 dashboard · )?注册",
                    "eo board · 注册",
                    lines[0],
                )
            return "\n".join(lines)

        with self.env_patch():
            before = baseline.render_all_terminal(baseline.build_all_data())
            after = board.render_all_terminal(board.build_all_data())
        self.assertIn("全局 dashboard", after.splitlines()[0])
        self.assertEqual(normalized(after), normalized(before))

    def test_stays_on_stdlib_only_and_binds_loopback_only(self):
        sources = [BOARD_PATH, *sorted((CLI_DIR / "eo_lib").glob("*.py"))]
        for source in sources:
            tree = ast.parse(source.read_text(encoding="utf-8"))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    imported.add(node.module.split(".")[0])
            third_party = imported - set(sys.stdlib_module_names) - {"eo_lib"}
            self.assertEqual(third_party, set(), f"{source.name} 引入了非标准库依赖")

        board_source = BOARD_PATH.read_text(encoding="utf-8")
        self.assertEqual(board_source.count('ThreadingHTTPServer(("127.0.0.1"'), 2)
        for forbidden in ("0.0.0.0", "::"):
            self.assertNotIn(f'"{forbidden}"', board_source)

    def test_user_docs_match_the_new_aggregate_behaviour(self):
        cli_ref = (REPO_ROOT / "docs" / "cli-reference.md").read_text(encoding="utf-8")
        guide = (REPO_ROOT / "docs" / "GUIDE.md").read_text(encoding="utf-8")
        shared = ("change 流", "概要卡", "route_key", "/p/<route_key>", "返回首页", "--scan", "hash")
        for doc, name, anchors in (
            (cli_ref, "cli-reference.md", shared + ("#/cards", "`#/`")),
            (guide, "GUIDE.md", shared),
        ):
            for anchor in anchors:
                self.assertTrue(anchor in doc, f"{name} 缺少「{anchor}」口径")


class BoardAllAggregateTests(MultiProjectFixture):
    """默认 --html / --serve 聚合形态：数据层注入、缓存单飞、逐请求重读注册表、参数矩阵。"""

    def load_board(self):
        board = load_module(f"eo_board_all_{id(self)}", BOARD_PATH)
        board._BOARD_CACHE.clear()
        board._BOARD_BUILD_LOCKS.clear()
        return board

    def env_patch(self):
        return mock.patch.dict(os.environ, {"EO_HOME": str(self.eo_home)})

    def start_all_server(self, board, scan_dir=None):
        handler = type("AllFixtureHandler", (board.AllBoardRequestHandler,), {"scan_dir": scan_dir})
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server

    def get_all_json(self, server):
        with urlopen(f"http://127.0.0.1:{server.server_port}/data.json", timeout=5) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    # ---------- 聚合数据层：getter 注入 ----------

    def test_build_all_data_fresh_getter_rebuilds_every_call(self):
        a = self.make_project("alpha", statuses=("confirmed",))
        self.register(a)
        board = self.load_board()
        calls = 0
        original = board.build_data

        def counted(cfg):
            nonlocal calls
            calls += 1
            return original(cfg)

        with self.env_patch(), mock.patch.object(board, "build_data", side_effect=counted):
            first = board.build_all_data()
            second = board.build_all_data()
        self.assertEqual(calls, 2)
        self.assertEqual(first["reg_count"], 1)
        self.assertIsNone(first["rows"][0]["error"])
        self.assertEqual(second["rows"][0]["counts"], {"confirmed": 1})

    def test_build_all_data_cached_getter_hits_cache_and_keeps_as_of(self):
        from datetime import datetime as real_datetime, timedelta

        a = self.make_project("alpha", statuses=("confirmed",))
        self.register(a)
        board = self.load_board()
        calls = 0
        original = board.build_data

        def counted(cfg):
            nonlocal calls
            calls += 1
            return original(cfg)

        class ShiftedDateTime(real_datetime):
            shift = timedelta()

            @classmethod
            def now(cls, tz=None):
                return real_datetime.now(tz) + cls.shift

        with self.env_patch(), \
                mock.patch.object(board, "build_data", side_effect=counted), \
                mock.patch.object(board, "datetime", ShiftedDateTime):
            first = board.build_all_data(get_entry=board._get_board_entry_cached)
            ShiftedDateTime.shift = timedelta(hours=2)
            second = board.build_all_data(get_entry=board._get_board_entry_cached)
        self.assertEqual(calls, 1)  # 第二次命中缓存不重扫
        # 缓存命中时 as-of 保持构建时刻，不按请求时刻重打
        self.assertEqual(second["rows"][0]["as_of"], first["rows"][0]["as_of"])

    # ---------- 默认 --html ----------

    def test_all_html_with_output_path_contains_blocks_and_inline_errors(self):
        a = self.make_project("alpha", statuses=("confirmed", "implementing"), backlog_cards=1)
        b = self.make_project("beta", statuses=("draft",))
        self.register(a)
        self.register(b)
        data = json.loads(self.registry_file().read_text(encoding="utf-8"))
        data["projects"].append({"name": "ghost", "path": str(self.root / "gone"), "registered_at": "2026-07-25"})
        self.registry_file().write_text(json.dumps(data), encoding="utf-8")
        out = self.root / "sub" / "all.html"
        r = self.run_board("--html", "-o", str(out), "--no-open")
        self.assertEqual(r.returncode, 0, r.stderr)
        html = out.read_text(encoding="utf-8")
        self.assertIn("eo board · 所有项目", html)
        self.assertIn('"alpha"', html)  # 每项目区块数据就位（JSON 注入 + 前端渲染）
        self.assertIn('"beta"', html)
        self.assertIn('"ghost"', html)
        self.assertIn("路径失效或缺 .eo-project.json", html)  # 坏条目行内错误不缺席
        self.assertIn('"reg_count": 3', html)
        self.assertNotIn("__EO_BOARD_ALL_DATA_JSON__", html)

    def test_all_html_default_path_goes_to_tmp_like_single_project(self):
        a = self.make_project("alpha")
        self.register(a)
        tmp_home = self.root / "tmp-home"
        tmp_home.mkdir()
        env = dict(os.environ)
        env["EO_HOME"] = str(self.eo_home)
        env["TMPDIR"] = str(tmp_home)
        r = subprocess.run(
            [sys.executable, str(BOARD_PATH), "--html", "--no-open"],
            cwd=self.root, env=env, capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        generated = list((tmp_home / "eo-board").glob("eo-board-all-*.html"))
        self.assertEqual(len(generated), 1)
        self.assertIn(str(generated[0]), r.stdout)

    # ---------- 默认 --serve ----------

    def test_all_serve_single_flight_per_slot_and_stable_key_no_rebuild(self):
        self.register(self.make_project("alpha", statuses=("confirmed",)))
        self.register(self.make_project("beta", statuses=("draft",)))
        board = self.load_board()
        calls = 0
        original = board.build_data
        lock = threading.Lock()
        # 两个槽的构建必须同时在场才能过桥——若跨槽退化成串行，这里超时、
        # 构建抛 BrokenBarrierError 落进行内 error，最下方的 error 断言随之失败
        overlap = threading.Barrier(2, timeout=15)

        def counted(cfg):
            nonlocal calls
            with lock:
                calls += 1
            overlap.wait()
            return original(cfg)

        with self.env_patch(), mock.patch.object(board, "build_data", side_effect=counted):
            server = self.start_all_server(board)
            results = []

            def hit():
                results.append(self.get_all_json(server))

            threads = [threading.Thread(target=hit) for _ in range(6)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)
            # 同槽 6 路并发只触发一次重扫；双槽并行各 +1
            self.assertEqual(calls, 2)
            self.assertEqual(len(results), 6)
            # 稳定键重复请求计数不增
            again = self.get_all_json(server)
            self.assertEqual(calls, 2)
        names = sorted(row["label"] for row in again["rows"])
        self.assertEqual(names, ["alpha", "beta"])
        self.assertEqual([row["error"] for row in again["rows"]], [None, None])
        self.assertTrue(again["serve"])

    def test_all_serve_rereads_registry_each_request(self):
        self.register(self.make_project("alpha"))
        beta = self.make_project("beta", statuses=("draft",))
        board = self.load_board()
        with self.env_patch():
            server = self.start_all_server(board)
            before = self.get_all_json(server)
            self.assertEqual([r["label"] for r in before["rows"]], ["alpha"])
            self.register(beta)  # serve 挂起期间新注册
            after = self.get_all_json(server)
        self.assertEqual(sorted(r["label"] for r in after["rows"]), ["alpha", "beta"])

    def test_all_serve_bad_entry_inline_and_empty_registry_guidance(self):
        board = self.load_board()
        with self.env_patch():
            server = self.start_all_server(board)
            empty = self.get_all_json(server)
            self.assertEqual(empty["reg_count"], 0)
            self.assertEqual(empty["rows"], [])
            with urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=5) as response:
                self.assertEqual(response.status, 200)
                html = response.read().decode("utf-8")
            self.assertIn("注册表为空", html)
            self.assertIn("--register", html)

            self.register(self.make_project("alpha"))
            data = json.loads(self.registry_file().read_text(encoding="utf-8"))
            data["projects"].append({"name": "bad", "path": 123})
            self.registry_file().write_text(json.dumps(data), encoding="utf-8")
            mixed = self.get_all_json(server)
        by_label = {r["label"]: r for r in mixed["rows"]}
        self.assertIsNone(by_label["alpha"]["error"])
        bad_rows = [r for r in mixed["rows"] if r["error"]]
        self.assertEqual(len(bad_rows), 1)
        self.assertIn("非法", bad_rows[0]["error"])

    def test_all_serve_cli_end_to_end(self):
        alpha = self.make_project("alpha", statuses=("implementing",))
        self.register(alpha)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = dict(os.environ)
        env["EO_HOME"] = str(self.eo_home)
        process = subprocess.Popen(
            [sys.executable, str(BOARD_PATH), "--serve", "--port", str(port), "--no-open"],
            cwd=self.root, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            deadline = time.monotonic() + 5
            while True:
                try:
                    with urlopen(f"http://127.0.0.1:{port}/", timeout=1) as response:
                        html = response.read().decode("utf-8")
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        self.fail("eo-board --serve did not accept requests within five seconds")
                    time.sleep(0.05)
            self.assertIn("setInterval(refreshLoop, 3000)", html)  # 3 秒轮询热刷新沿用
            with urlopen(f"http://127.0.0.1:{port}/data.json", timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            self.assertEqual(data["rows"][0]["label"], "alpha")
            self.assertEqual(data["rows"][0]["counts"], {"implementing": 1})
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()

    def test_all_serve_cli_refreshes_changed_status_on_next_poll(self):
        alpha = self.make_project("alpha", statuses=("draft",))
        self.register(alpha)
        change = alpha / "eo-doc" / "changes" / "01-c1" / "change.md"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = dict(os.environ)
        env["EO_HOME"] = str(self.eo_home)
        process = subprocess.Popen(
            [sys.executable, str(BOARD_PATH), "--serve", "--port", str(port), "--no-open"],
            cwd=self.root, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            deadline = time.monotonic() + 5
            while True:
                try:
                    with urlopen(f"http://127.0.0.1:{port}/", timeout=1) as response:
                        html = response.read().decode("utf-8")
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        self.fail("eo-board --serve did not accept requests within five seconds")
                    time.sleep(0.05)
            self.assertIn("setInterval(refreshLoop, 3000)", html)
            self.assertEqual(self.get_all_status(port), "draft")
            change.write_text(change.read_text(encoding="utf-8").replace("status: draft", "status: reviewed"), encoding="utf-8")
            timestamp = time.time() + 2
            os.utime(change, (timestamp, timestamp))
            time.sleep(3.1)  # 与页面轮询间隔一致后取下一次数据，验证热刷新所依赖的服务端更新。
            self.assertEqual(self.get_all_status(port), "reviewed")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()

    def get_all_status(self, port):
        with urlopen(f"http://127.0.0.1:{port}/data.json", timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        return next(iter(data["rows"][0]["counts"]))

    def test_all_serve_cli_rereads_registry_after_empty_guidance(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = dict(os.environ)
        env["EO_HOME"] = str(self.eo_home)
        process = subprocess.Popen(
            [sys.executable, str(BOARD_PATH), "--serve", "--port", str(port), "--no-open"],
            cwd=self.root, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            deadline = time.monotonic() + 5
            while True:
                try:
                    with urlopen(f"http://127.0.0.1:{port}/", timeout=1) as response:
                        html = response.read().decode("utf-8")
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        self.fail("empty all-project serve did not accept requests within five seconds")
                    time.sleep(0.05)
            self.assertIn("注册表为空", html)
            self.assertIn("--register", html)
            self.register(self.make_project("beta", statuses=("confirmed",)))
            with urlopen(f"http://127.0.0.1:{port}/data.json", timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            self.assertEqual([(row["label"], row["counts"]) for row in data["rows"]], [("beta", {"confirmed": 1})])
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()

    # ---------- 参数组合矩阵 ----------

    def test_argparse_matrix_rejections(self):
        for combo in (
            ["--all"],  # 已退役
            ["--all", "--project", "somewhere"],
            ["--all", "--html", "--no-open"],
            ["--register", "--all"],
            ["--register", "--html"],
            ["--unregister", "--serve"],
            ["--scan", str(self.root), "--project", "somewhere"],
            ["-o", "x.html"],  # -o 仅在 --html 下有效
            ["--html", "--port", "7444"],  # --port 仅在 --serve 下有效
            ["--port", "7444"],
            ["--register", "--no-open"],  # --no-open 仅在 --html/--serve 下有效
            ["--no-open"],
            ["--html", "--port", "7444", "-o", "x.html", "--no-open"],
        ):
            r = self.run_board(*combo)
            self.assertNotEqual(r.returncode, 0, f"应当拒绝：{combo}")

    def test_argparse_matrix_scan_composes_with_html(self):
        parent = self.root / "scan-parent"
        self.make_project("orphan", statuses=("draft",), parent=parent)
        out = self.root / "scan.html"
        r = self.run_board("--scan", str(parent), "--html", "-o", str(out), "--no-open")
        self.assertEqual(r.returncode, 0, r.stderr)
        html = out.read_text(encoding="utf-8")
        self.assertIn('"orphan"', html)
        self.assertIn('"scanned_count": 1', html)


class BoardGlobalDashboardTests(MultiProjectFixture):
    """全局 dashboard 收敛：默认入口、cwd 并入、项目下拉数据与跳转。"""

    def env_patch(self):
        return mock.patch.dict(os.environ, {"EO_HOME": str(self.eo_home)})

    def test_default_terminal_is_global_dashboard_without_all_flag(self):
        self.register(self.make_project("alpha", statuses=("confirmed",)))
        self.register(self.make_project("beta", statuses=("draft",)))
        r = self.run_board()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("全局 dashboard", r.stdout)
        self.assertIn("alpha", r.stdout)
        self.assertIn("beta", r.stdout)
        self.assertNotIn("eo board · alpha", r.stdout.splitlines()[0] if r.stdout else "")

    def test_default_html_is_aggregate_home_not_single_project(self):
        alpha = self.make_project("alpha", statuses=("implementing",))
        self.register(alpha)
        out = self.root / "home.html"
        r = self.run_board("--html", "-o", str(out), "--no-open", cwd=alpha)
        self.assertEqual(r.returncode, 0, r.stderr)
        html = out.read_text(encoding="utf-8")
        self.assertIn('id="eo-board-all-data"', html)
        self.assertIn("eo board · 所有项目", html)
        self.assertNotIn('id="eo-board-data"', html)

    def test_cwd_unregistered_project_is_merged_like_scan(self):
        orphan = self.make_project("orphan", statuses=("draft",))
        before = self.registry_file().read_bytes() if self.registry_file().exists() else b""
        r = self.run_board(cwd=orphan)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("orphan (未注册)", r.stdout)
        self.assertIn("全局 dashboard", r.stdout)
        after = self.registry_file().read_bytes() if self.registry_file().exists() else b""
        self.assertEqual(after, before)

    def test_empty_registry_and_non_project_cwd_prints_register_guidance(self):
        elsewhere = self.root / "nowhere"
        elsewhere.mkdir()
        r = self.run_board(cwd=elsewhere)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("注册表为空", r.stdout)
        self.assertIn("--register", r.stdout)

    def test_build_all_data_injects_dashboard_projects_into_each_embedded_board(self):
        alpha = self.make_project("alpha", statuses=("implementing",))
        beta = self.make_project("beta", statuses=("draft",))
        self.register(alpha)
        self.register(beta)
        board = self.load_board_module()
        with self.env_patch():
            agg = board.build_all_data(embed_board=True)
        by_label = {row["label"]: row for row in agg["rows"]}
        alpha_projects = by_label["alpha"]["board"]["dashboard_projects"]
        names = [p["name"] for p in alpha_projects]
        self.assertEqual(sorted(names), ["alpha", "beta"])
        current = next(p for p in alpha_projects if p["name"] == "alpha")
        other = next(p for p in alpha_projects if p["name"] == "beta")
        self.assertTrue(current["current"])
        self.assertFalse(other["current"])
        self.assertTrue(current["href"].startswith("#/p/"))
        self.assertTrue(other["href"].startswith("#/p/"))
        self.assertNotEqual(current["href"], other["href"])

    @unittest.skipUnless(NODE, "缺少 node，无法在无浏览器环境执行挂载路径")
    def test_snapshot_project_switch_lists_all_drillable_and_uses_hash_hrefs(self):
        alpha = self.make_project("alpha", statuses=("implementing",))
        beta = self.make_project("beta", statuses=("draft",))
        self.register(alpha)
        self.register(beta)
        parent = self.root / "scan-parent"
        orphan = self.make_project("orphan", statuses=("confirmed",), parent=parent)
        board = self.load_board_module()
        alpha_key = board.make_route_key("alpha", alpha)
        beta_key = board.make_route_key("beta", beta)
        orphan_key = board.make_route_key("orphan", orphan)

        mounted = self.mount_snapshot_project(self.snapshot_html(scan=parent), alpha_key)
        top = mounted["projectTopbar"]
        self.assertIn('class="project-switch"', top)
        self.assertIn(f'value="#/p/{alpha_key}"', top)
        self.assertIn(f'value="#/p/{beta_key}"', top)
        self.assertIn(f'value="#/p/{orphan_key}"', top)
        self.assertIn("selected", top)

    def test_serve_project_page_switch_lists_all_with_path_hrefs(self):
        alpha = self.make_project("alpha", statuses=("implementing",))
        beta = self.make_project("beta", statuses=("draft",))
        self.register(alpha)
        self.register(beta)
        board = self.load_board_module()
        alpha_key = board.make_route_key("alpha", alpha)
        beta_key = board.make_route_key("beta", beta)
        handler = type("DashHandler", (board.AllBoardRequestHandler,), {"scan_dir": None})
        with self.env_patch():
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(thread.join, 5)
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            with urlopen(f"http://127.0.0.1:{server.server_port}/p/{alpha_key}", timeout=5) as response:
                html = response.read().decode("utf-8")
            with urlopen(f"http://127.0.0.1:{server.server_port}/p/{alpha_key}/data.json", timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            with urlopen(f"http://127.0.0.1:{server.server_port}/p/{beta_key}", timeout=5) as response:
                self.assertEqual(response.status, 200)

        projects = data["dashboard_projects"]
        by_name = {p["name"]: p for p in projects}
        self.assertEqual(sorted(by_name), ["alpha", "beta"])
        self.assertEqual(by_name["alpha"]["href"], f"/p/{alpha_key}")
        self.assertEqual(by_name["beta"]["href"], f"/p/{beta_key}")
        self.assertTrue(by_name["alpha"]["current"])
        self.assertFalse(by_name["beta"]["current"])
        # 页面内嵌 JSON 带齐 href；下拉 markup 由 JS 渲染，跳转写 location.href = option.value
        self.assertIn(f'"href": "/p/{beta_key}"', html)
        self.assertIn('class="project-switch"', html)
        self.assertIn("window.location.href = switcher.value", html)

    def test_project_terminal_still_directs_to_single_project_summary(self):
        alpha = self.make_project("alpha", statuses=("confirmed", "implementing"))
        self.register(alpha)
        r = self.run_board("--project", "alpha")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("eo board · alpha", r.stdout)
        self.assertNotIn("全局 dashboard", r.stdout)

    def _register_main_and_linked_worktree(self, name="alpha", statuses=("implementing",)):
        """注册主 worktree，并在同仓开 linked worktree（路径不同、repo identity 相同）。"""
        main = self.make_project(name, statuses=statuses)
        self.register(main)
        linked = self.root / f"{name}-linked"
        run_git(main, "worktree", "add", "-q", str(linked), "-b", f"{name}-linked-br")
        return main, linked

    def test_project_html_linked_worktree_sets_initial_route_for_explicit_path(self):
        """注册主 worktree 后 --project <linked 路径> --html 的 initial_route 必须命中 linked。"""
        main, linked = self._register_main_and_linked_worktree()
        board = self.load_board_module()
        main_key = board.make_route_key("alpha", main)
        linked_key = board.make_route_key("alpha", linked)
        self.assertNotEqual(main_key, linked_key)

        out = self.root / "linked.html"
        r = self.run_board("--project", str(linked), "--html", "-o", str(out), "--no-open")
        self.assertEqual(r.returncode, 0, r.stderr)
        html = out.read_text(encoding="utf-8")
        marker = 'id="eo-board-all-data">'
        start = html.index(marker) + len(marker)
        agg = json.loads(html[start:html.index("</script>", start)])
        self.assertEqual(agg.get("initial_route"), linked_key)
        by_path = {row.get("path"): row for row in agg["rows"] if not row.get("error")}
        self.assertIn(str(linked.resolve()), by_path)
        self.assertEqual(by_path[str(linked.resolve())]["route_key"], linked_key)
        self.assertIsNotNone(by_path[str(linked.resolve())].get("board"))

    def test_project_serve_linked_worktree_route_and_data_are_reachable(self):
        """真实 CLI：--project <linked 路径> --serve 的首开 URL 与 /p/<key>/data 接线。

        必须走 main → cmd_all_serve(args, cfg)，不能手工拼 AllBoardRequestHandler，
        否则 cfg=cfg / explicit_dir / 首开路由退化时用例仍会绿。
        """
        main, linked = self._register_main_and_linked_worktree()
        board = self.load_board_module()
        linked_key = board.make_route_key("alpha", linked)
        main_key = board.make_route_key("alpha", main)
        self.assertNotEqual(main_key, linked_key)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = dict(os.environ)
        env["EO_HOME"] = str(self.eo_home)
        env["PYTHONUNBUFFERED"] = "1"
        process = subprocess.Popen(
            [
                sys.executable, str(BOARD_PATH),
                "--project", str(linked),
                "--serve", "--port", str(port), "--no-open",
            ],
            cwd=self.root, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            # 首开 URL 由 cmd_all_serve 在 serve_forever 前打印：.../p/<linked_key>
            banner = ""
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        self.fail(
                            f"eo-board --project --serve exited early: "
                            f"rc={process.returncode} stderr={process.stderr.read()}"
                        )
                    continue
                banner += line
                if "http://127.0.0.1:" in line:
                    break
            expected_open = f"http://127.0.0.1:{port}/p/{linked_key}"
            self.assertIn(expected_open, banner)

            # 等服务真正接受请求后再取数（打印 banner 后仍可能略有延迟）
            page = None
            data = None
            home = None
            wait_until = time.monotonic() + 5
            while True:
                try:
                    with urlopen(expected_open, timeout=1) as response:
                        self.assertEqual(response.status, 200)
                        page = response.read().decode("utf-8")
                    with urlopen(f"{expected_open}/data.json", timeout=5) as response:
                        self.assertEqual(response.status, 200)
                        data = json.loads(response.read().decode("utf-8"))
                    with urlopen(f"http://127.0.0.1:{port}/data.json", timeout=5) as response:
                        self.assertEqual(response.status, 200)
                        home = json.loads(response.read().decode("utf-8"))
                    break
                except OSError:
                    if time.monotonic() >= wait_until:
                        self.fail(
                            "eo-board --project <linked> --serve did not accept "
                            "linked route requests within five seconds"
                        )
                    time.sleep(0.05)

            self.assertEqual(data["project"]["name"], "alpha")
            self.assertIn(f'"href": "/p/{linked_key}"', page)
            home_keys = {row["route_key"] for row in home["rows"] if row.get("route_key")}
            self.assertIn(linked_key, home_keys)
            # 注册主 worktree 的 route 不应被误当成首开目标
            self.assertNotIn(f"http://127.0.0.1:{port}/p/{main_key}", banner.splitlines()[0] if banner else "")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()

    def test_default_aggregate_still_dedups_same_repo_without_explicit_dir(self):
        """默认聚合（无 explicit_dir）仍按 repo identity 去重：注册主 + cwd linked 不双行。"""
        main, linked = self._register_main_and_linked_worktree()
        board = self.load_board_module()
        with self.env_patch():
            without = board.build_all_data()
            with_cwd = board.build_all_data(cwd_dir=str(linked.resolve()))
            with_explicit = board.build_all_data(explicit_dir=str(linked.resolve()))

        def alpha_paths(agg):
            return sorted(
                str(Path(r["path"]).resolve())
                for r in agg["rows"]
                if not r.get("error") and r.get("label") == "alpha"
            )

        self.assertEqual(alpha_paths(without), [str(main.resolve())])
        self.assertEqual(alpha_paths(with_cwd), [str(main.resolve())])  # cwd 同仓被 known 挡掉
        # 显式目标必须进集合（可与注册主并存，route_key 不同）
        self.assertIn(str(linked.resolve()), alpha_paths(with_explicit))

    def test_backlog_note_renders_as_escaped_plain_text_not_mdinline(self):
        """backlog 卡片正文摘要保持 esc 纯文本，不走 mdInline。"""
        src = BOARD_PATH.read_text(encoding="utf-8")
        start = src.index("function backlogCard(d)")
        end = src.index("\nfunction ", start + 1)
        body = src[start:end]
        self.assertIn("bl-note", body)
        self.assertRegex(body, r"bl-note.*>'\s*\+\s*esc\(")
        self.assertNotRegex(body, r"bl-note.*>'\s*\+\s*mdInline\(")


if __name__ == "__main__":
    unittest.main()
