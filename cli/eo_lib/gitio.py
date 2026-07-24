"""git 子进程封装。失败一律返回空串，调用方按缺数据降级。"""

import subprocess


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


def list_worktrees(anchor_dir):
    out = run_git(["worktree", "list", "--porcelain"], cwd=str(anchor_dir))
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
    if not worktrees:
        # 非 git 仓库或 git 不可用：退化为把当前目录当唯一 worktree
        return [{"path": str(anchor_dir), "branch": None}]
    for wt in worktrees:
        branch = run_git(["branch", "--show-current"], cwd=wt["path"]).strip()
        wt["branch"] = branch or wt.get("branch")
    return worktrees
