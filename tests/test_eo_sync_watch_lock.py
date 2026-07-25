"""Real-process coverage for eo-sync watch single-instance scope locking.

Same-scope watches are mutually exclusive (second exits with code 2 and holder
info); --all vs single-project overlap only warns; stale scope locks self-clean;
SIGTERM/SIGINT release the lock. Every lock and projection lives below one
TemporaryDirectory via EO_HOME.
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

DEAD_PID = 2 ** 31 - 1

CHANGE = """---
id: sample
seq: 1
title: Sample
summary: Watch lock fixture
status: confirmed
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


class WatchScopeLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.eo_home = self.root / "eo-home"
        self.outside = self.root / "outside"
        self.outside.mkdir()
        self.processes = []
        self._log_seq = 0

    def tearDown(self):
        for proc, log in self.processes:
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=10)
            log.close()

    def _env(self):
        env = dict(os.environ)
        env["EO_HOME"] = str(self.eo_home)
        env["EO_SYNC_TODAY"] = "2026-07-25"
        env["PATH"] = os.pathsep.join([str(CLI_DIR), env.get("PATH", "")])
        return env

    def _project(self, name):
        repo = self.root / name
        repo.mkdir()
        vault = self.root / f"{name}-vault"
        vault.mkdir()
        config = {
            "project_name": name,
            "mode": "vault",
            "project_root": str(vault),
            "doc_root": "eo-doc",
            "sync": {"obsidian": {"enabled": True, "stub_dir": "stubs"}},
        }
        (repo / ".eo-project.json").write_text(json.dumps(config), encoding="utf-8")
        change = repo / "eo-doc" / "changes" / "01-sample" / "change.md"
        change.parent.mkdir(parents=True)
        change.write_text(CHANGE, encoding="utf-8")
        git(repo, "init", "-q")
        git(repo, "add", "-A")
        git(repo, "-c", "user.email=t@example.test", "-c", "user.name=test", "commit", "-qm", "fixture")
        return repo

    def _watch(self, *args, cwd=None):
        self._log_seq += 1
        log_path = self.root / f"stderr-{self._log_seq}.log"
        log = open(log_path, "w", encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, str(EO_SYNC), "watch", "--interval", "1", *args],
            cwd=cwd or self.outside,
            env=self._env(),
            stdout=subprocess.DEVNULL,
            stderr=log,
        )
        self.processes.append((proc, log))
        return proc, log_path

    def _wait_for_log(self, log_path, needle, timeout=8):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if log_path.is_file() and needle in log_path.read_text(encoding="utf-8"):
                return
            time.sleep(0.1)
        content = log_path.read_text(encoding="utf-8") if log_path.is_file() else "<no log>"
        self.fail(f"{needle!r} not seen within {timeout}s; stderr:\n{content}")

    def _wait_started(self, log_path):
        self._wait_for_log(log_path, "eo-sync watch 已启动")

    def _assert_still_running(self, proc, log_path, grace=1.5):
        time.sleep(grace)
        if proc.poll() is not None:
            self.fail(f"watch exited unexpectedly rc={proc.returncode}; stderr:\n{log_path.read_text(encoding='utf-8')}")

    def _stop(self, proc, sig=signal.SIGTERM):
        proc.send_signal(sig)
        proc.wait(timeout=10)

    def _wait_exit(self, proc, log_path, timeout=8):
        try:
            return proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.fail(f"watch did not exit within {timeout}s; stderr:\n{log_path.read_text(encoding='utf-8')}")

    def test_all_scope_second_instance_exits_locked(self):
        first, first_log = self._watch("--all")
        self._wait_started(first_log)
        second, second_log = self._watch("--all")
        self.assertEqual(self._wait_exit(second, second_log), 2)
        err = second_log.read_text(encoding="utf-8")
        self.assertIn("已在运行", err)
        self.assertIn(str(first.pid), err)
        self.assertIn("--all", err)
        self.assertIn("启动于", err)

    def test_project_scope_mutex_same_repo_including_bare_watch(self):
        repo = self._project("solo")
        first, first_log = self._watch("--project", str(repo))
        self._wait_started(first_log)

        second, second_log = self._watch("--project", str(repo))
        self.assertEqual(self._wait_exit(second, second_log), 2)
        err = second_log.read_text(encoding="utf-8")
        self.assertIn("已在运行", err)
        self.assertIn(str(first.pid), err)
        self.assertIn("启动于", err)

        bare, bare_log = self._watch(cwd=repo)
        self.assertEqual(self._wait_exit(bare, bare_log), 2)
        self.assertIn("已在运行", bare_log.read_text(encoding="utf-8"))

        other = self._project("other")
        third, third_log = self._watch("--project", str(other))
        self._wait_started(third_log)
        self._assert_still_running(third, third_log)

    def test_cross_scope_overlap_warns_but_both_run(self):
        repo = self._project("solo")
        allproc, all_log = self._watch("--all")
        self._wait_started(all_log)

        projproc, proj_log = self._watch("--project", str(repo))
        self._wait_started(proj_log)
        self._assert_still_running(projproc, proj_log)
        proj_err = proj_log.read_text(encoding="utf-8")
        self.assertIn("作用域重叠", proj_err)
        self.assertIn(str(allproc.pid), proj_err)

        self._stop(allproc)
        allproc2, all_log2 = self._watch("--all")
        self._wait_started(all_log2)
        self._assert_still_running(allproc2, all_log2)
        all_err = all_log2.read_text(encoding="utf-8")
        self.assertIn("作用域重叠", all_err)
        self.assertIn(str(projproc.pid), all_err)

    def test_stale_scope_lock_is_cleared_on_start(self):
        state_dir = self.eo_home / "sync-state"
        state_dir.mkdir(parents=True)
        (state_dir / "watch-all.lock").write_text(
            json.dumps({"pid": DEAD_PID, "at": time.time() - 3600}), encoding="utf-8"
        )
        proc, log = self._watch("--all")
        self._wait_started(log)
        self._assert_still_running(proc, log)
        holder = json.loads((state_dir / "watch-all.lock").read_text(encoding="utf-8"))
        self.assertEqual(holder.get("pid"), proc.pid)

    def test_signal_exit_releases_lock_for_next_start(self):
        repo = self._project("solo")
        first, first_log = self._watch("--project", str(repo))
        self._wait_started(first_log)
        self.assertTrue(list((self.eo_home / "sync-state").glob("watch-*.lock")))
        self._stop(first, signal.SIGTERM)

        second, second_log = self._watch("--project", str(repo))
        self._wait_started(second_log)
        self._assert_still_running(second, second_log)
        self._stop(second, signal.SIGINT)
        self.assertEqual(second.returncode, 0)

        third, third_log = self._watch("--project", str(repo))
        self._wait_started(third_log)
        self._assert_still_running(third, third_log)


if __name__ == "__main__":
    unittest.main()
