import importlib.machinery
import importlib.util
import io
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = REPO_ROOT / "cli" / "eo-helper"

EXPECTED_MENU = [
    ("全局实时看板", ["eo-board", "--serve"], "exec"),
    ("注册本项目到多项目看板", ["eo-board", "--register"], "run"),
    ("同步看板卡片（跑一次）", ["eo-sync", "run"], "run"),
    ("看板自动跟手（常驻）", ["eo-sync", "watch", "--all"], "exec"),
    ("全局终端速览", ["eo-board"], "run"),
]


def load_helper(name="eo_helper_under_test"):
    loader = importlib.machinery.SourceFileLoader(name, str(HELPER_PATH))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


class HelperMenuMapTests(unittest.TestCase):
    """固定 argv 映射是 helper 的全部业务——锁死条目、顺序与执行方式。"""

    def setUp(self):
        self.helper = load_helper()

    def test_menu_is_exactly_the_pinned_entries(self):
        actual = [(i["label"], i["argv"], i["mode"]) for i in self.helper.MENU]
        self.assertEqual(actual, EXPECTED_MENU)

    def test_menu_lines_show_number_to_command_mapping(self):
        text = "\n".join(self.helper.menu_lines())
        self.assertIn("选数字，q 退出", text)
        for idx, item in enumerate(self.helper.MENU, start=1):
            self.assertIn(f"{idx}) {item['label']}", text)
            self.assertIn("→ " + " ".join(item["argv"]), text)

    def test_user_facing_labels_avoid_projection_jargon(self):
        for item in self.helper.MENU:
            self.assertNotIn("投影", item["label"])

    def test_readme_faq_menu_numbers_match_helper_map(self):
        """README FAQ 的菜单编号必须与 helper MENU 下标一致（watch=4 / sync=3）。"""
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        by_label = {label: idx for idx, (label, _, _) in enumerate(EXPECTED_MENU, start=1)}
        watch_n = by_label["看板自动跟手（常驻）"]
        sync_n = by_label["同步看板卡片（跑一次）"]
        self.assertEqual((watch_n, sync_n), (4, 3))
        faq = next(line for line in readme.splitlines() if "看板卡片怎么不动了" in line)
        self.assertIn(f"菜单 {watch_n}", faq)
        self.assertIn(f"菜单 {sync_n}", faq)
        self.assertIn("看板自动跟手", faq)


class HelperInteractiveTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()

    def run_main(self, inputs, which="/usr/bin/stub", run_rc=0):
        """isatty=True 下驱动菜单循环；返回 (exit_code, stdout, run_calls, exec_calls)。"""
        run_calls, exec_calls = [], []

        def fake_run(argv, **kwargs):
            run_calls.append((argv, kwargs))
            return SimpleNamespace(returncode=run_rc)

        def fake_execvp(prog, argv):
            exec_calls.append((prog, argv))

        out = io.StringIO()
        with mock.patch.object(self.helper.sys, "argv", ["eo-helper"]), \
                mock.patch.object(self.helper.sys, "stdin") as stdin, \
                mock.patch.object(self.helper.shutil, "which", return_value=which), \
                mock.patch.object(self.helper.subprocess, "run", side_effect=fake_run), \
                mock.patch.object(self.helper.os, "execvp", side_effect=fake_execvp), \
                mock.patch("builtins.input", side_effect=inputs), \
                redirect_stdout(out):
            stdin.isatty.return_value = True
            code = self.helper.main()
        return code, out.getvalue(), run_calls, exec_calls

    def test_short_command_echoes_then_forwards_and_returns_to_menu(self):
        code, out, run_calls, exec_calls = self.run_main(["3", "q"])
        self.assertEqual(code, 0)
        self.assertIn("→ 正在执行：eo-sync run", out)
        self.assertEqual(run_calls, [((["eo-sync", "run"]), {})])  # stdio 直通：不带捕获参数
        self.assertEqual(exec_calls, [])
        # 回到菜单：执行后菜单至少再打印一次
        self.assertGreaterEqual(out.count("eo-helper · eo-skills 日常入口"), 2)

    def test_long_running_command_execs_and_replaces_process(self):
        code, out, run_calls, exec_calls = self.run_main(["1", "q"])
        self.assertEqual(code, 0)
        self.assertIn("→ 正在执行：eo-board --serve", out)
        self.assertEqual(exec_calls, [("eo-board", ["eo-board", "--serve"])])
        self.assertEqual(run_calls, [])

    def test_nonzero_exit_status_is_visible_not_silent(self):
        code, out, run_calls, _ = self.run_main(["3", "q"], run_rc=1)
        self.assertEqual(code, 0)  # helper 自身菜单循环正常退出返回 0
        self.assertIn("↑ eo-sync run 退出码 1", out)

    def test_invalid_number_prompts_reselect(self):
        code, out, run_calls, exec_calls = self.run_main(["99", "abc", "q"])
        self.assertEqual(code, 0)
        self.assertEqual(out.count("无效编号"), 2)
        self.assertEqual(run_calls, [])
        self.assertEqual(exec_calls, [])

    def test_unicode_digits_and_oversized_input_are_invalid_not_traceback(self):
        # ²（isdigit 真但 int 失败）、全角４、中文数字、阿拉伯-印度数字、超长数字串：
        # 一律走非法编号提示，绝不 traceback
        weird = ["²", "４", "一", "١", "9" * 5000]
        code, out, run_calls, exec_calls = self.run_main(weird + ["q"])
        self.assertEqual(code, 0)
        self.assertEqual(out.count("无效编号"), len(weird))
        self.assertEqual(run_calls, [])
        self.assertEqual(exec_calls, [])

    def test_eof_exits_cleanly_like_q(self):
        code, out, run_calls, exec_calls = self.run_main([EOFError()])
        self.assertEqual(code, 0)
        self.assertEqual(run_calls, [])

    def test_keyboard_interrupt_at_menu_exits_cleanly(self):
        code, out, run_calls, exec_calls = self.run_main([KeyboardInterrupt()])
        self.assertEqual(code, 0)
        self.assertEqual(run_calls, [])

    def test_missing_underlying_cli_hints_install_without_forwarding(self):
        code, out, run_calls, exec_calls = self.run_main(["1", "q"], which=None)
        self.assertEqual(code, 0)
        self.assertIn("install.sh", out)
        self.assertEqual(run_calls, [])
        self.assertEqual(exec_calls, [])


class HelperCliTests(unittest.TestCase):
    """真实子进程：非 TTY 守卫与参数面。"""

    def run_helper(self, *args, stdin=subprocess.DEVNULL):
        return subprocess.run(
            [sys.executable, str(HELPER_PATH), *args],
            stdin=stdin, capture_output=True, text=True, timeout=30,
        )

    def test_non_tty_prints_mapping_table_and_exits_zero(self):
        r = self.run_helper()
        self.assertEqual(r.returncode, 0, r.stderr)
        for item in EXPECTED_MENU:
            self.assertIn(" ".join(item[1]), r.stdout)
        self.assertNotIn("正在执行", r.stdout)  # 不拉起子进程

    def test_piped_stdin_does_not_hang_or_consume_input(self):
        r = subprocess.run(
            [sys.executable, str(HELPER_PATH)],
            input="1\n", capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("正在执行", r.stdout)

    def test_help_flag_prints_table(self):
        r = self.run_helper("-h")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("eo-board --serve", r.stdout)

    def test_unknown_argument_rejected(self):
        r = self.run_helper("--bogus")
        self.assertEqual(r.returncode, 2)
        self.assertIn("未知参数", r.stderr)


if __name__ == "__main__":
    unittest.main()
