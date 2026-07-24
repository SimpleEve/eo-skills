"""eo 文件契约的共享解析库：配置加载 / git 封装 / frontmatter 解析 / change 扫描。

只用标准库。库内不终止进程——配置/解析失败抛 ConfigError，由 CLI 入口捕获退出。
"""

from .config import ConfigError, find_project_config, load_project_config
from .freshness import compute_freshness_key
from .gitio import run_git, list_worktrees
from .frontmatter import (
    split_frontmatter,
    parse_yaml_subset,
    parse_yaml_scalar,
    unquote,
    upsert_frontmatter_fields,
)
from .changes import (
    CHANGE_STATUS_ORDER,
    split_body_sections,
    strip_trailing_paren,
    parse_intent,
    parse_ac_section,
    parse_todo_section,
    parse_oq_section,
    parse_change_file,
    scan_all_changes,
    scan_changes_grouped,
    pick_change_winner,
    resolve_writeback_path,
    status_rank,
    count_ac,
    count_todo,
)

__all__ = [
    "ConfigError",
    "find_project_config",
    "load_project_config",
    "compute_freshness_key",
    "run_git",
    "list_worktrees",
    "split_frontmatter",
    "parse_yaml_subset",
    "parse_yaml_scalar",
    "unquote",
    "upsert_frontmatter_fields",
    "CHANGE_STATUS_ORDER",
    "split_body_sections",
    "strip_trailing_paren",
    "parse_intent",
    "parse_ac_section",
    "parse_todo_section",
    "parse_oq_section",
    "parse_change_file",
    "scan_all_changes",
    "scan_changes_grouped",
    "pick_change_winner",
    "resolve_writeback_path",
    "status_rank",
    "count_ac",
    "count_todo",
]
