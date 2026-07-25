import importlib.machinery
import importlib.util
import json
import os
import socket
from datetime import date
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
BASELINE_REVISION = "792522d"


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

    def test_extracted_board_matches_baseline_for_terminal_html_and_serve_data(self):
        baseline_source = run_git(REPO_ROOT, "show", f"{BASELINE_REVISION}:cli/eo-board").stdout
        baseline_path = self.root / "eo_board_baseline.py"
        baseline_path.write_text(baseline_source, encoding="utf-8")
        baseline = load_module(f"eo_board_baseline_{id(self)}", baseline_path)

        baseline_cfg = baseline.load_project_config(self.repo / ".eo-project.json")
        baseline_data = baseline.build_data(baseline_cfg)
        current_data = self.board.build_data(self.cfg)
        baseline_data["generated_at"] = current_data["generated_at"]
        self.assertEqual(current_data, baseline_data)
        self.assertEqual(self.board.render_terminal(current_data), baseline.render_terminal(baseline_data))
        self.assertEqual(self.board.render_html(current_data), baseline.render_html(baseline_data))

        self.start_server()
        served = self.get_json()
        served["generated_at"] = baseline_data["generated_at"]
        served["serve"] = False
        self.assertEqual(served, baseline_data)

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
