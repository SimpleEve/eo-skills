""".eo-project.json 定位与加载。必填字段与路径约束的权威口径见 eo-project-init/references/config.md。"""

import json
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
    if isinstance(project_root, str) and project_root.strip() and not Path(project_root).is_absolute():
        problems.append(f"project_root 必须是绝对路径（当前 {project_root!r}）")
    doc_root = raw.get("doc_root")
    if isinstance(doc_root, str) and doc_root.strip() and Path(doc_root).is_absolute():
        problems.append(f"doc_root 必须是相对 repo root 的路径（当前 {doc_root!r}）")
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
    return {
        "project_name": raw["project_name"],
        "mode": raw["mode"],
        "project_root": raw["project_root"],
        "doc_root": raw["doc_root"],
        "board": raw.get("board") if isinstance(raw.get("board"), dict) else {},
        "github": raw.get("github") if isinstance(raw.get("github"), dict) else {},
        "config_path": path,
        "repo_root": path.parent,
    }
