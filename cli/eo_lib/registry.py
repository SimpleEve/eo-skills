"""用户级项目注册表：`${EO_HOME:-$HOME/.eo}/projects.json`。

schema v1：`{"version": 1, "projects": [{"name", "path", "registered_at"}]}`。
去重键 = gitio.repo_identity（与 eo-sync 簿记 hash8 同源）；`name` 不是唯一键，
同名项目合法共存。顶层与条目级未知字段读写 round-trip 原样保留（前向兼容）；
文件缺失视为空表，损坏 JSON 抛 ConfigError 不静默清空。写入走临时文件 + rename 原子落盘。
"""

import json
import os
from datetime import date
from pathlib import Path

from .config import ConfigError
from .gitio import repo_identity


def registry_path():
    home = os.environ.get("EO_HOME")
    base = Path(home) if home else Path.home() / ".eo"
    return base / "projects.json"


def load_registry(path=None):
    path = path or registry_path()
    if not path.is_file():
        return {"version": 1, "projects": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        raise ConfigError(f"项目注册表损坏（非法 JSON）：{path}（{e}）", path=path)
    except OSError as e:
        raise ConfigError(f"项目注册表读取失败：{path}（{e}）", path=path)
    if not isinstance(data, dict):
        raise ConfigError(f"项目注册表内容不是 JSON 对象：{path}", path=path)
    if "projects" in data and not isinstance(data["projects"], list):
        raise ConfigError(f"项目注册表 projects 字段不是列表：{path}", path=path)
    data.setdefault("version", 1)
    data.setdefault("projects", [])
    return data


def save_registry(data, path=None):
    path = path or registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(path))


def entry_path(entry):
    """条目的合法 path（非空字符串），结构性坏条目返回 None——消费方据此行内隔离，不得直接 Path()。"""
    if not isinstance(entry, dict):
        return None
    path = entry.get("path")
    return path if isinstance(path, str) and path else None


def _entry_identity(entry):
    path = entry_path(entry)
    return repo_identity(path) if path else None


def register_project(project_dir, name, today=None, path=None):
    """按 repo identity 幂等注册。返回 {"action": "created"|"updated", "entry", "same_name"}。

    已注册（含从另一 worktree）→ 就地更新 name/registered_at（条目级未知字段保留，
    path 保持首次注册值）；same_name 列出身份不同但同名的既有条目（合法共存，仅供提示）。
    """
    data = load_registry(path)
    ident = repo_identity(project_dir)
    today = today or date.today().isoformat()
    matched = None
    same_name = []
    for entry in data["projects"]:
        if _entry_identity(entry) == ident:
            matched = entry
        elif isinstance(entry, dict) and entry.get("name") == name:
            same_name.append(entry)
    if matched is not None:
        matched["name"] = name
        matched["registered_at"] = today
        action = "updated"
        entry = matched
    else:
        entry = {"name": name, "path": str(Path(project_dir).resolve()), "registered_at": today}
        data["projects"].append(entry)
        action = "created"
    save_registry(data, path)
    return {"action": action, "entry": entry, "same_name": same_name}


def unregister_project(project_dir, path=None):
    """按 repo identity 移除注册条目。返回被移除的条目，未命中返回 None。"""
    data = load_registry(path)
    ident = repo_identity(project_dir)
    for i, entry in enumerate(data["projects"]):
        if _entry_identity(entry) == ident:
            removed = data["projects"].pop(i)
            save_registry(data, path)
            return removed
    return None


def find_by_name(data, name):
    """按注册名查条目，返回全部命中（可能多项——同名合法共存，调用方自行处理歧义）。"""
    return [e for e in data.get("projects", []) if isinstance(e, dict) and e.get("name") == name]
