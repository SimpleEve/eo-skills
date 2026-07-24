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


if __name__ == "__main__":
    unittest.main()
