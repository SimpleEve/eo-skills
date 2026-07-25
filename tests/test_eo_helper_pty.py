import os
import pty
import select
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = REPO_ROOT / "cli" / "eo-helper"


class HelperPtyTests(unittest.TestCase):
    """真实 PTY 验证菜单转发和 os.exec 接管，而非仅 mock 内部调用。"""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.env = dict(os.environ)
        self.env["PATH"] = os.pathsep.join([str(self.bin_dir), self.env.get("PATH", "")])
        self.env["EO_HOME"] = str(self.root / "eo-home")
        self.pid = None
        self.master = None
        self.buffer = b""
        self.addCleanup(self.stop_child)

    def write_command(self, name, body):
        path = self.bin_dir / name
        path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
        path.chmod(0o755)

    def start_helper(self):
        pid, master = pty.fork()
        if pid == 0:
            os.chdir(self.root)
            os.execve(str(HELPER_PATH), [str(HELPER_PATH)], self.env)
        self.pid = pid
        self.master = master

    def read_until(self, expected, timeout=5):
        deadline = time.monotonic() + timeout
        marker = expected.encode()
        while marker not in self.buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self.fail(f"PTY did not receive {expected!r}; got {self.buffer.decode(errors='replace')!r}")
            readable, _, _ = select.select([self.master], [], [], remaining)
            if readable:
                try:
                    chunk = os.read(self.master, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                self.buffer += chunk
        end = self.buffer.index(marker) + len(marker)
        output, self.buffer = self.buffer[:end], self.buffer[end:]
        return output.decode(errors="replace")

    def wait_for_exit(self, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                self.pid = None
                return os.waitstatus_to_exitcode(status)
            time.sleep(0.02)
        self.fail("helper child did not exit")

    def stop_child(self):
        if self.pid is not None:
            try:
                os.kill(self.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                try:
                    if os.waitpid(self.pid, os.WNOHANG)[0]:
                        break
                except ChildProcessError:
                    break
                time.sleep(0.02)
            else:
                try:
                    os.kill(self.pid, signal.SIGKILL)
                    os.waitpid(self.pid, 0)
                except ProcessLookupError:
                    pass
                except ChildProcessError:
                    pass
            self.pid = None
        if self.master is not None:
            os.close(self.master)
            self.master = None

    def test_short_command_echoes_output_nonzero_status_and_returns_to_menu(self):
        self.write_command("eo-sync", 'echo "sync-output:$*"\nexit 7\n')
        self.start_helper()
        self.read_until("> ")
        os.write(self.master, b"4\n")
        output = self.read_until("↑ eo-sync run 退出码 7")
        self.assertIn("→ 正在执行：eo-sync run", output)
        self.assertIn("sync-output:run", output)
        self.read_until("> ")
        os.write(self.master, b"q\n")
        self.read_until("q")
        self.assertEqual(self.wait_for_exit(), 0)

    def test_long_command_execs_in_place_and_ctrl_c_reaches_underlying_process(self):
        self.write_command(
            "eo-board",
            "echo \"board-pid:$$ args:$*\"\ntrap 'echo board-int; exit 130' INT\nwhile :; do sleep 1; done\n",
        )
        self.start_helper()
        helper_pid = self.pid
        self.read_until("> ")
        os.write(self.master, b"2\n")
        output = self.read_until("args:--all --serve")
        self.assertIn("→ 正在执行：eo-board --all --serve", output)
        self.assertIn(f"board-pid:{helper_pid}", output)
        os.write(self.master, b"\x03")
        self.read_until("board-int")
        self.assertEqual(self.wait_for_exit(), 130)


class HelperInstallTests(unittest.TestCase):
    def test_install_links_helper_in_temporary_prefix_and_promotes_it(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            prefix = root / "prefix" / "bin"
            env = dict(os.environ, HOME=str(root / "home"), EO_BIN_DIR=str(prefix))
            result = subprocess.run(
                ["sh", "install.sh", "--codex-only"], cwd=REPO_ROOT, env=env,
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            helper = prefix / "eo-helper"
            self.assertTrue(helper.is_symlink())
            self.assertTrue(os.path.samefile(helper, HELPER_PATH))
            self.assertIn("日常只需记一条命令——eo-helper", result.stdout)
            menu = subprocess.run([str(helper)], stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=10)
            self.assertEqual(menu.returncode, 0, menu.stderr)
            self.assertIn("eo-board --all --serve", menu.stdout)


if __name__ == "__main__":
    unittest.main()
