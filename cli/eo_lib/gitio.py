"""git 子进程封装。失败一律返回空串，调用方按缺数据降级。"""

import subprocess
from pathlib import Path


def repo_identity(path):
    """规范化仓库身份：git common dir 的 realpath 绝对路径；非 git 目录退化为目录自身 realpath。

    同一仓库的主/linked worktree 归一到同一身份。注册表去重与 eo-sync 簿记 hash8
    必须同源消费本函数，不得各写等价实现。
    """
    base = Path(path)
    common = run_git(["rev-parse", "--git-common-dir"], cwd=str(base)).strip()
    if common:
        cp = Path(common)
        return str(cp.resolve()) if cp.is_absolute() else str((base / cp).resolve())
    return str(base.resolve())


def run_git(args, cwd=None):
    try:
        res = subprocess.run(
            ["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=15
        )
    except Exception:
        return ""
    if res.returncode != 0:
        return ""
    return res.stdout


def _parse_worktree_porcelain(out):
    worktrees = []
    cur = {}
    for line in out.splitlines():
        if not line.strip():
            if cur:
                worktrees.append(cur)
                cur = {}
            continue
        if line.startswith("worktree "):
            cur = {"path": line[len("worktree "):].strip()}
        elif line.startswith("branch "):
            ref = line[len("branch "):].strip()
            cur["branch"] = ref[len("refs/heads/"):] if ref.startswith("refs/heads/") else ref
        elif line.startswith("detached"):
            cur["branch"] = None
    if cur:
        worktrees.append(cur)
    return worktrees


def list_worktrees_status(anchor_dir):
    """同一次枚举返回 (worktrees, enum_ok)。enum_ok=False 仅当这是 git 仓库却枚举不出 worktree
    （落到单目录 fallback，可能漏扫其它 worktree 的内容 → 快照不可证完整）；非 git 仓库单目录即完整。
    worktrees 与 enum_ok 同源同时刻，供调用方把快照与完整性绑定为原子结果。"""
    out = run_git(["worktree", "list", "--porcelain"], cwd=str(anchor_dir))
    worktrees = _parse_worktree_porcelain(out)
    if not worktrees:
        # out 为空：区分「非 git 仓库」（合法单目录、完整）与「git 仓库但枚举失败」（降级）
        is_repo = run_git(["rev-parse", "--is-inside-work-tree"], cwd=str(anchor_dir)).strip() == "true"
        return [{"path": str(anchor_dir), "branch": None}], (not is_repo)
    for wt in worktrees:
        branch = run_git(["branch", "--show-current"], cwd=wt["path"]).strip()
        wt["branch"] = branch or wt.get("branch")
    return worktrees, True


def list_worktrees(anchor_dir):
    worktrees, _ = list_worktrees_status(anchor_dir)
    return worktrees
