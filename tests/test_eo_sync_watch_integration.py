"""Real-process coverage for eo-sync watch.

These tests deliberately exercise the long-lived CLI instead of the in-process
tick seams.  Every project, adapter, registry, lock, and projection lives below
one TemporaryDirectory via EO_HOME.
"""

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_DIR = REPO_ROOT / "cli"
EO_SYNC = CLI_DIR / "eo-sync"
EO_BOARD = CLI_DIR / "eo-board"


CHANGE = """---
id: sample
seq: 1
title: Sample
summary: Watch integration fixture
status: {status}
tier: full
type: feature
base_commit: ~
created: 2026-07-25
---

# Sample

## 2. Acceptance
- [ ] AC-1 fixture
"""


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


class WatchIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.eo_home = self.root / "eo-home"
        self.outside = self.root / "outside"
        self.outside.mkdir()
        self.processes = []

    def tearDown(self):
        for proc in self.processes:
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
                proc.communicate(timeout=10)

    def _env(self, extra=None):
        env = dict(os.environ)
        env["EO_HOME"] = str(self.eo_home)
        env["EO_SYNC_TODAY"] = "2026-07-25"
        env["PATH"] = os.pathsep.join([str(CLI_DIR), env.get("PATH", "")])
        if extra:
            env.update(extra)
        return env

    def _project(self, name, sync=None):
        repo = self.root / name
        repo.mkdir()
        vault = self.root / f"{name}-vault"
        vault.mkdir()
        config = {
            "project_name": name,
            "mode": "vault",
            "project_root": str(vault),
            "doc_root": "eo-doc",
            "sync": sync if sync is not None else {"obsidian": {"enabled": True, "stub_dir": "stubs"}},
        }
        (repo / ".eo-project.json").write_text(json.dumps(config), encoding="utf-8")
        change = repo / "eo-doc" / "changes" / "01-sample" / "change.md"
        change.parent.mkdir(parents=True)
        change.write_text(CHANGE.format(status="confirmed"), encoding="utf-8")
        git(repo, "init", "-q")
        git(repo, "add", "-A")
        git(repo, "-c", "user.email=t@example.test", "-c", "user.name=test", "commit", "-qm", "fixture")
        return repo, change, vault / "stubs" / "sample.md"

    def _register(self, repo):
        result = subprocess.run(
            [sys.executable, str(EO_BOARD), "--register", str(repo)],
            cwd=self.outside,
            env=self._env(),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def _watch(self, *args, extra_env=None):
        proc = subprocess.Popen(
            [sys.executable, str(EO_SYNC), "watch", "--interval", "1", *args],
            cwd=self.outside,
            env=self._env(extra_env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.processes.append(proc)
        return proc

    def _stop(self, proc):
        if proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
        stdout, stderr = proc.communicate(timeout=10)
        return stdout, stderr

    def _wait_for(self, predicate, message, timeout=6):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.1)
        self.fail(message)

    def _stub_has_status(self, stub, status):
        return stub.is_file() and f"status: {status}" in stub.read_text(encoding="utf-8")

    def test_project_watch_updates_stub_after_status_transition_from_any_directory(self):
        repo, change, stub = self._project("solo")
        proc = self._watch("--project", str(repo))
        self._wait_for(lambda: self._stub_has_status(stub, "confirmed"), "initial projection was not created")
        # Let the first tick finish its post-run key recomputation before changing SoT.
        time.sleep(1.2)
        change.write_text(CHANGE.format(status="reviewed"), encoding="utf-8")
        future = time.time() + 2
        os.utime(change, (future, future))
        self._wait_for(lambda: self._stub_has_status(stub, "reviewed"), "watch did not catch up after one interval")
        time.sleep(0.3)
        _, stderr = self._stop(proc)
        self.assertGreaterEqual(stderr.count("[eo-sync watch] ✓"), 2, stderr)
        self.assertIn("已停止", stderr)

    def test_transition_during_post_sync_key_recompute_is_not_lost(self):
        repo, change, stub = self._project("race")
        proc = self._watch("--project", str(repo))
        self._wait_for(lambda: self._stub_has_status(stub, "confirmed"), "initial projection was not created")
        # The stub write precedes watch_project_tick()'s post-run key recomputation.
        # A SoT change here must still trigger a later tick rather than being absorbed
        # into the new baseline without ever reaching the projection.
        change.write_text(CHANGE.format(status="reviewed"), encoding="utf-8")
        future = time.time() + 2
        os.utime(change, (future, future))
        try:
            self._wait_for(lambda: self._stub_has_status(stub, "reviewed"), "watch lost a transition during post-sync key recomputation")
        except AssertionError:
            _, stderr = self._stop(proc)
            self.fail(f"watch lost a transition during post-sync key recomputation:\n{stderr}")
        time.sleep(1.3)
        _, stderr = self._stop(proc)
        self.assertEqual(stderr.count("[eo-sync watch] ✓"), 2, stderr)
        self.assertIn("下一轮复跑确认", stderr)

    def test_partial_failure_records_baseline_then_stays_quiet(self):
        repo, _, _ = self._project("failure", sync={"fail": {"enabled": True}})
        adapter_dir = self.root / "adapters"
        adapter_dir.mkdir()
        adapter = adapter_dir / "eo-sync-fail"
        adapter.write_text(
            "#!/usr/bin/env python3\n"
            "import json, sys\n"
            "if sys.argv[1] == 'capabilities':\n"
            " print(json.dumps({'protocol_version': 1, 'name': 'fail', 'entities': ['change'], 'projections': [], 'identity_fields': []}))\n"
            "else:\n"
            " sys.stderr.write('intentional plan failure\\n')\n"
            " sys.exit(7)\n",
            encoding="utf-8",
        )
        adapter.chmod(0o755)
        proc = self._watch("--project", str(repo), extra_env={
            "PATH": os.pathsep.join([str(adapter_dir), str(CLI_DIR), os.environ.get("PATH", "")]),
        })
        time.sleep(3.3)
        _, stderr = self._stop(proc)
        self.assertEqual(stderr.count("[eo-sync watch] ✓"), 1, stderr)
        self.assertEqual(stderr.count("适配器 fail plan 失败"), 1, stderr)
        self.assertIn("部分失败", stderr)

    def test_held_lock_skips_then_next_round_catches_up(self):
        repo, _, stub = self._project("locked")
        git_dir = (repo / ".git").resolve()
        import hashlib
        hash8 = hashlib.sha256(str(git_dir).encode("utf-8")).hexdigest()[:8]
        lock_path = self.eo_home / "sync-state" / f"locked-{hash8}.json.lock"
        holder = subprocess.Popen(
            [sys.executable, "-c", (
                "import fcntl,json,os,sys,time; p=sys.argv[1]; os.makedirs(os.path.dirname(p),exist_ok=True); "
                "fd=os.open(p,os.O_RDWR|os.O_CREAT,0o644); fcntl.flock(fd,fcntl.LOCK_EX); "
                "os.write(fd,json.dumps({'pid':os.getpid(),'at':time.time()}).encode()); print('ready',flush=True); time.sleep(1.4)"
            ), str(lock_path)],
            stdout=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(holder.stdout.readline().strip(), "ready")
        proc = self._watch("--project", str(repo))
        self._wait_for(lambda: self._stub_has_status(stub, "confirmed"), "projection did not recover after lock release")
        time.sleep(0.3)
        _, stderr = self._stop(proc)
        holder.communicate(timeout=10)
        self.assertIn("锁被占用", stderr)
        self.assertIn("已同步", stderr)

    def test_all_watch_suppresses_invalid_path_then_recovers_without_harming_valid_project(self):
        valid, _, valid_stub = self._project("valid")
        self._register(valid)
        registry = self.eo_home / "projects.json"
        data = json.loads(registry.read_text(encoding="utf-8"))
        ghost = self.root / "ghost"
        data["projects"].append({"name": "ghost", "path": str(ghost), "registered_at": "2026-07-25"})
        registry.write_text(json.dumps(data), encoding="utf-8")
        board = subprocess.run([sys.executable, str(EO_BOARD), "--all"], cwd=self.outside,
                               env=self._env(), capture_output=True, text=True)
        self.assertEqual(board.returncode, 0, board.stderr)
        self.assertIn("valid", board.stdout)
        self.assertIn("ghost", board.stdout)
        self.assertIn("路径失效", board.stdout)
        proc = self._watch("--all")
        self._wait_for(lambda: self._stub_has_status(valid_stub, "confirmed"), "valid project was blocked by bad registry path")
        time.sleep(2.2)
        ghost_repo, _, ghost_stub = self._project("ghost")
        self.assertEqual(ghost_repo, ghost)
        self._wait_for(lambda: self._stub_has_status(ghost_stub, "confirmed"), "repaired registry project was not reincluded")
        time.sleep(0.3)
        _, stderr = self._stop(proc)
        self.assertEqual(stderr.count("ghost：路径失效或缺 .eo-project.json"), 1, stderr)

    def test_all_watch_tracks_two_projects_and_new_registration_on_next_round(self):
        first, _, first_stub = self._project("first")
        second, _, second_stub = self._project("second")
        self._register(first)
        self._register(second)
        proc = self._watch("--all")
        self._wait_for(lambda: self._stub_has_status(first_stub, "confirmed"), "first project was not synchronized")
        self._wait_for(lambda: self._stub_has_status(second_stub, "confirmed"), "second project was not synchronized")
        third, _, third_stub = self._project("third")
        self._register(third)
        self._wait_for(lambda: self._stub_has_status(third_stub, "confirmed"), "newly registered project was not picked up")
        time.sleep(0.3)
        _, stderr = self._stop(proc)
        self.assertGreaterEqual(stderr.count("[eo-sync watch] ✓"), 3, stderr)


if __name__ == "__main__":
    unittest.main()
