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
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_DIR = REPO_ROOT / "cli"
BOARD_PATH = CLI_DIR / "eo-board"
VARIANT_PATH = REPO_ROOT / "eo-doc" / "changes" / "10-board-all-v2" / "design" / "variant-2.html"
BASELINE_REVISION = "792522d"
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
        self.assertEqual(self.board.render_terminal(current_data), baseline.render_terminal(baseline_data))

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
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]

        process = subprocess.Popen(
            [sys.executable, str(BOARD_PATH), "--serve", "--port", str(port), "--no-open"],
            cwd=self.repo,
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
            self.change_path.write_text(
                self.change_path.read_text(encoding="utf-8").replace("status: draft", "status: reviewed"),
                encoding="utf-8",
            )
            self.bump_mtime(self.change_path)
            time.sleep(3.1)
            with urlopen(f"http://127.0.0.1:{port}/data.json", timeout=5) as response:
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


class MultiProjectFixture(unittest.TestCase):
    """多项目 fixture 基座。EO_HOME 一律临时目录，不触碰真实 ~/.eo。"""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name).resolve()
        self.eo_home = self.root / "eo-home"

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
        args = ["--all", "--html", "-o", str(out), "--no-open", *extra]
        if scan:
            args = ["--all", "--scan", str(scan), "--html", "-o", str(out), "--no-open", *extra]
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
        script_start = html.index("<script>", end) + len("<script>")
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


class BoardMultiProjectTests(MultiProjectFixture):
    """--all / --project / --scan 多项目聚合与下钻（终端形态）。"""

    def test_all_one_row_per_project_with_counts_and_as_of(self):
        a = self.make_project("alpha", statuses=("confirmed", "implementing", "archived"), backlog_cards=2)
        b = self.make_project("beta", statuses=("draft",))
        self.register(a)
        self.register(b)
        r = self.run_board("--all")
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
        r = self.run_board("--all")
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
        r = self.run_board("--all")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("alpha", r.stdout)  # 有效项目照常输出
        self.assertIn("非法", r.stdout)

    def test_scan_dedups_same_repo_worktrees(self):
        a = self.make_project("alpha")
        self.register(a)
        parent = self.root / "scan-parent"
        orphan = self.make_project("orphan", statuses=("draft",), parent=parent)
        run_git(orphan, "worktree", "add", "-q", str(parent / "orphan-wt"), "-b", "side")
        r = self.run_board("--all", "--scan", str(parent))
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = [l for l in r.stdout.splitlines() if "(未注册)" in l and not l.startswith("提示")]
        self.assertEqual(len(rows), 1)  # 同仓主/linked worktree 只一行

    def test_all_empty_registry_prints_guidance(self):
        r = self.run_board("--all")
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
        r = self.run_board("--all", "--scan", str(parent))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("orphan (未注册)", r.stdout)
        self.assertIn("--register", r.stdout)
        self.assertEqual(self.registry_file().read_bytes(), before)

    def test_scan_requires_all(self):
        r = self.run_board("--scan", str(self.root))
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
        self.assertIn('<span class="tag branch">⎇ side@alpha-side</span>', content)
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
        extra = {"unreg", "proj-err", "proj-note", "list-empty", "branch"}
        self.assertLessEqual(classes(content) - extra, variant)
        for anchor in ("strip", "proj", "list", "list-head", "row", "r-proj", "r-main",
                       "r-prog", "r-when", "divider", "st-pill", "bar", "todo", "ac"):
            self.assertIn(anchor, classes(content), anchor)


class BoardAllAggregateTests(MultiProjectFixture):
    """--all 的 --html / --serve 聚合形态：数据层注入、缓存单飞、逐请求重读注册表、参数矩阵。"""

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

    # ---------- --all --html ----------

    def test_all_html_with_output_path_contains_blocks_and_inline_errors(self):
        a = self.make_project("alpha", statuses=("confirmed", "implementing"), backlog_cards=1)
        b = self.make_project("beta", statuses=("draft",))
        self.register(a)
        self.register(b)
        data = json.loads(self.registry_file().read_text(encoding="utf-8"))
        data["projects"].append({"name": "ghost", "path": str(self.root / "gone"), "registered_at": "2026-07-25"})
        self.registry_file().write_text(json.dumps(data), encoding="utf-8")
        out = self.root / "sub" / "all.html"
        r = self.run_board("--all", "--html", "-o", str(out), "--no-open")
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
            [sys.executable, str(BOARD_PATH), "--all", "--html", "--no-open"],
            cwd=self.root, env=env, capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        generated = list((tmp_home / "eo-board").glob("eo-board-all-*.html"))
        self.assertEqual(len(generated), 1)
        self.assertIn(str(generated[0]), r.stdout)

    # ---------- --all --serve ----------

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
            [sys.executable, str(BOARD_PATH), "--all", "--serve", "--port", str(port), "--no-open"],
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
                        self.fail("eo-board --all --serve did not accept requests within five seconds")
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
            [sys.executable, str(BOARD_PATH), "--all", "--serve", "--port", str(port), "--no-open"],
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
                        self.fail("eo-board --all --serve did not accept requests within five seconds")
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
            [sys.executable, str(BOARD_PATH), "--all", "--serve", "--port", str(port), "--no-open"],
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
            ["--all", "--project", "somewhere"],
            ["--register", "--all"],
            ["--register", "--html"],
            ["--unregister", "--serve"],
            ["--all", "-o", "x.html"],  # -o 仅在 --html 下有效
            ["-o", "x.html"],
            ["--all", "--port", "7444"],  # --port 仅在 --serve 下有效
            ["--html", "--port", "7444"],
            ["--port", "7444"],
            ["--register", "--no-open"],  # --no-open 仅在 --html/--serve 下有效
            ["--no-open"],
            ["--all", "--html", "--port", "7444", "-o", "x.html", "--no-open"],
        ):
            r = self.run_board(*combo)
            self.assertNotEqual(r.returncode, 0, f"应当拒绝：{combo}")

    def test_argparse_matrix_scan_composes_with_html(self):
        parent = self.root / "scan-parent"
        self.make_project("orphan", statuses=("draft",), parent=parent)
        out = self.root / "scan.html"
        r = self.run_board("--all", "--scan", str(parent), "--html", "-o", str(out), "--no-open")
        self.assertEqual(r.returncode, 0, r.stderr)
        html = out.read_text(encoding="utf-8")
        self.assertIn('"orphan"', html)
        self.assertIn('"scanned_count": 1', html)


if __name__ == "__main__":
    unittest.main()
