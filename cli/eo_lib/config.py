""".eo-project.json 定位与加载。"""

import json


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


def load_project_config(path):
    raw = _load_json_object(path, ".eo-project.json")
    local_path = path.parent / ".eo-project.local.json"
    if local_path.is_file():
        # 顶层字段整体覆盖（local 优先），覆盖后再做缺省填充
        raw = {**raw, **_load_json_object(local_path, ".eo-project.local.json")}
    return {
        "project_name": raw.get("project_name") or path.parent.name,
        "mode": raw.get("mode") or "local",
        "project_root": raw.get("project_root"),
        "doc_root": raw.get("doc_root") or "eo-doc",
        "board": raw.get("board") if isinstance(raw.get("board"), dict) else {},
        "github": raw.get("github") if isinstance(raw.get("github"), dict) else {},
        "config_path": path,
        "repo_root": path.parent,
    }
