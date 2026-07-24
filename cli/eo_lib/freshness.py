"""--serve 缓存的新鲜度键计算。

契约：键必须闭合 build_data 的全部动态输入——各 worktree (路径, 分支, HEAD) 三元组、
refs 指纹（覆盖 git log --all 类统计）、changes 目录树 max-mtime、backlog / roadmap
数据源 mtime、当天日期（覆盖停滞天数 / 当月边界等日期派生字段）。
build_data 引入新动态输入时，键成分必须同步扩展，否则缓存对其永久陈旧。
"""

import hashlib
from datetime import date
from pathlib import Path

from .gitio import run_git, list_worktrees


def _tree_max_mtime(root):
    if not root.is_dir():
        return None
    latest = root.stat().st_mtime
    for p in root.rglob("*"):
        try:
            m = p.stat().st_mtime
        except OSError:
            continue
        if m > latest:
            latest = m
    return latest


def _file_mtime(path):
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def compute_freshness_key(cfg):
    anchor = cfg["repo_root"]
    worktrees = list_worktrees(anchor)

    triples = []
    changes_mtimes = []
    for wt in worktrees:
        head = run_git(["rev-parse", "HEAD"], cwd=wt["path"]).strip()
        triples.append((wt["path"], wt.get("branch"), head))
        changes_mtimes.append(
            (wt["path"], _tree_max_mtime(Path(wt["path"]) / cfg["doc_root"] / "changes"))
        )

    refs_digest = hashlib.sha256(
        run_git(["for-each-ref"], cwd=str(anchor)).encode("utf-8")
    ).hexdigest()

    if cfg["mode"] == "vault" and cfg.get("project_root"):
        source_roots = [Path(cfg["project_root"])]
    else:
        source_roots = [Path(wt["path"]) / ".eo-project" for wt in worktrees]
    sources = [
        (str(root), _tree_max_mtime(root / "backlog"), _file_mtime(root / "roadmap.md"))
        for root in source_roots
    ]

    return (
        date.today().isoformat(),
        tuple(sorted(triples, key=lambda t: t[0])),
        refs_digest,
        tuple(sorted(changes_mtimes, key=lambda t: t[0])),
        tuple(sorted(sources, key=lambda t: t[0])),
    )
