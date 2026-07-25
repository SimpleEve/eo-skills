""".eo-project.json 定位与加载。必填字段与路径约束的权威口径见 eo-project-init/references/config.md。"""

import json
import sys
from pathlib import Path


class ConfigError(Exception):
    """配置定位/解析失败；携带文件路径与原因，是否退出进程由 CLI 入口决定。"""

    def __init__(self, message, path=None):
        super().__init__(message)
        self.path = path


def find_project_config(start):
    cur = start.resolve()
    while True:
        candidate = cur / ".eo-project.json"
        if candidate.is_file():
            return candidate
        if cur.parent == cur:
            return None
        cur = cur.parent


def _load_json_object(path, label):
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ConfigError(f"{label} 解析失败：{path}（{e}）", path=path)
    if not isinstance(raw, dict):
        raise ConfigError(f"{label} 内容不是一个 JSON 对象：{path}", path=path)
    return raw


def _normalize_project_root(project_root, path):
    """v1 遗留形态：project_root 写成相对 repo root 的路径（常见是指向 vault 的软链）。
    解析得出已存在的目录才归一化为其 realpath，否则返回 None 交由校验拒绝。
    绝对路径不走本函数——既有项目的解析结果不因本归一化而改变。"""
    try:
        resolved = (path.parent / project_root).resolve()
        return resolved if resolved.is_dir() else None
    except (OSError, RuntimeError, ValueError):
        # 成环软链在 CPython 抛 RuntimeError，含 NUL 的路径抛 ValueError——都不是 OSError
        return None


def _validate_merged(raw, path):
    problems = []
    for field in ("project_name", "mode", "project_root", "doc_root"):
        value = raw.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"必填字段 {field} 缺失或不是非空字符串")
    mode = raw.get("mode")
    if isinstance(mode, str) and mode.strip() and mode not in ("vault", "local"):
        problems.append(f"mode 必须是 vault 或 local（当前 {mode!r}）")
    project_root = raw.get("project_root")
    if (isinstance(project_root, str) and project_root.strip()
            and not Path(project_root).is_absolute() and _normalize_project_root(project_root, path) is None):
        problems.append(
            f"project_root 必须是绝对路径（当前 {project_root!r}；"
            f"按 repo root {path.parent} 解析后也不是已存在的目录）"
        )
    doc_root = raw.get("doc_root")
    if isinstance(doc_root, str) and doc_root.strip() and Path(doc_root).is_absolute():
        problems.append(f"doc_root 必须是相对 repo root 的路径（当前 {doc_root!r}）")
    sync = raw.get("sync")
    if sync is not None and not isinstance(sync, dict):
        problems.append(f"sync 段必须是对象（当前 {type(sync).__name__}）")
    if problems:
        raise ConfigError(
            f".eo-project.json 配置校验失败（含 local 覆盖的合并结果）：{path}（{'；'.join(problems)}）",
            path=path,
        )


def load_project_config(path):
    raw = _load_json_object(path, ".eo-project.json")
    local_path = path.parent / ".eo-project.local.json"
    if local_path.is_file():
        # 顶层字段整体覆盖（local 优先）；必填校验看合并结果，单个文件不要求自包含
        raw = {**raw, **_load_json_object(local_path, ".eo-project.local.json")}
    _validate_merged(raw, path)
    project_root = raw["project_root"]
    if not Path(project_root).is_absolute():
        normalized = _normalize_project_root(project_root, path)
        if normalized is None:
            # 校验与取值之间目标消失（同步盘上并非纯理论）——绝不把 None 当路径传给下游
            raise ConfigError(
                f"project_root 归一化失败：{project_root!r} 按 repo root {path.parent} 解析不到已存在的目录",
                path=path,
            )
        print(f"⚠ project_root 是相对路径 {project_root!r}，已按 repo root 解析为 {normalized}；"
              f"建议重跑 /eo-project-init 固化为绝对路径", file=sys.stderr)
        project_root = str(normalized)
    merged = {
        "project_name": raw["project_name"],
        "mode": raw["mode"],
        "project_root": project_root,
        "doc_root": raw["doc_root"],
        "board": raw.get("board") if isinstance(raw.get("board"), dict) else {},
        "github": raw.get("github") if isinstance(raw.get("github"), dict) else {},
        "config_path": path,
        "repo_root": path.parent,
    }
    # sync 段的键存在性用 `"sync" in merged` 判定：缺席（键不在）→ 走 board/github 兼容映射；
    # 键存在（含显式 null / 空 {} / dict）→ 完全以其为准。仅原样透传值（类型已在 _validate 校验，null 合法）。
    if "sync" in raw:
        merged["sync"] = raw["sync"]
    return merged
