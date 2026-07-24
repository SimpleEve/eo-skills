"""change.md 正文解析、change 目录扫描与 AC/TODO 计数。"""

import re
from pathlib import Path

from .frontmatter import split_frontmatter

CHANGE_STATUS_ORDER = ["draft", "confirmed", "implementing", "reviewed", "archived"]

HEADING2_RE = re.compile(r"^##\s*(\d+)\.?\s*.*$")
HEADING3_RE = re.compile(r"^###\s*(.+?)\s*$")
CHECKBOX_RE = re.compile(r"^[-*]\s+\[([ xX])\]\s*(?:([A-Za-z]+-\d+)\s*)?(.*)$")


def split_body_sections(body_text):
    """按 `## ` 标题切分正文；返回 (标题前内容行, {编号: 内容行列表})。"""
    lines = body_text.splitlines()
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1
    if start < len(lines) and lines[start].lstrip().startswith("# ") and not lines[start].lstrip().startswith("##"):
        start += 1

    sections, preamble = {}, []
    cur_key, cur_lines = None, []

    def flush():
        if cur_key is None:
            preamble.extend(cur_lines)
        else:
            sections[cur_key] = cur_lines

    for line in lines[start:]:
        m = HEADING2_RE.match(line.strip())
        if m:
            flush()
            cur_key, cur_lines = m.group(1), []
            continue
        cur_lines.append(line)
    flush()
    return preamble, sections


def strip_trailing_paren(text):
    """摘掉行尾一组配对括号（全角/半角），返回 (正文, 括号内容 or None)。"""
    s = text.rstrip()
    for op, cl in (("（", "）"), ("(", ")")):
        if s.endswith(cl):
            depth = 0
            for i in range(len(s) - 1, -1, -1):
                if s[i] == cl:
                    depth += 1
                elif s[i] == op:
                    depth -= 1
                    if depth == 0:
                        return s[:i].rstrip(), s[i + 1: -1]
            break
    return s, None


def parse_intent(preamble, section1_lines):
    lines = section1_lines if section1_lines is not None else preamble
    text_lines, decisions = [], []
    in_decisions = False
    for line in lines:
        stripped = line.strip()
        if not in_decisions and "已钉决策" in stripped:
            in_decisions = True
            continue
        if in_decisions:
            if stripped[:1] in ("-", "*"):
                item_text = stripped[1:].strip()
                decisions.append({"text": item_text, "assume": "假设" in item_text})
                continue
            if not stripped:
                continue
            in_decisions = False
        text_lines.append(line)
    intent_text = "\n".join(text_lines).strip()
    intent_text = re.sub(r"^意图[:：]\s*", "", intent_text)
    return intent_text, decisions


def parse_ac_section(lines):
    items = []
    for line in lines:
        m = CHECKBOX_RE.match(line.strip())
        if not m:
            continue
        done = m.group(1).lower() == "x"
        code, rest = m.group(2), m.group(3).strip()
        text, paren = strip_trailing_paren(rest)
        note, manual = None, False
        if paren:
            if paren.startswith("人工"):
                manual, note = True, paren
            elif paren.startswith("验证") or paren.startswith("锁定"):
                note = paren
            else:
                text = rest  # 不认识的括注：原样并回正文，避免吞信息
        items.append({"code": code, "done": done, "text": text, "note": note, "manual": manual})
    return items


def parse_todo_section(lines):
    batches = []
    cur_batch = None
    for line in lines:
        stripped = line.strip()
        m3 = HEADING3_RE.match(stripped)
        if m3:
            cur_batch = {"batch": m3.group(1), "items": []}
            batches.append(cur_batch)
            continue
        mck = CHECKBOX_RE.match(stripped)
        if not mck:
            continue
        done, code, rest = mck.group(1).lower() == "x", mck.group(2), mck.group(3).strip()
        text, paren = strip_trailing_paren(rest)
        file_, ac_, crit = None, None, None
        if paren:
            for part in re.split("[；;]", paren):
                part = part.strip()
                if part.startswith("文件"):
                    file_ = re.sub(r"^文件[:：]\s*", "", part)
                elif part.startswith("对应"):
                    ac_ = part.replace("对应", "", 1).strip()
                elif part.startswith("完成判据"):
                    crit = re.sub(r"^完成判据[:：]\s*", "", part)
                elif part:
                    text = text + "（" + part + "）"
        item = {"code": code, "done": done, "text": text, "file": file_, "ac": ac_}
        if crit:
            item["criteria"] = crit
        if cur_batch is None:
            cur_batch = {"batch": "TODO", "items": []}
            batches.append(cur_batch)
        cur_batch["items"].append(item)
    return batches


def parse_oq_section(lines):
    items = []
    for line in lines:
        stripped = line.strip()
        if stripped[:1] not in ("-", "*"):
            continue
        content = stripped[1:].strip()
        m = re.match(r"(OQ-\d+)\s*(.*)", content)
        items.append({"code": m.group(1), "text": m.group(2)} if m else {"code": None, "text": content})
    return items


def parse_change_file(path, worktree_path, dirname, warnings):
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        warnings.append(f"change 文件读取失败，已跳过：{path}（{e}）")
        return None
    fm, body = split_frontmatter(text)
    if fm is None:
        warnings.append(f"缺少 frontmatter，已跳过：{path}")
        return None

    cid = str(fm.get("id") or re.sub(r"^\d+-", "", dirname))
    status = fm.get("status") or "draft"
    if status == "done":
        status = "reviewed"  # 旧口径兼容
    tier = fm.get("tier") or "full"

    intent_text, decisions, ac_items, todo_batches, oq_items = "", [], [], None, []
    try:
        preamble, sections = split_body_sections(body)
        intent_text, decisions = parse_intent(preamble, sections.get("1"))
        ac_items = parse_ac_section(sections.get("2", []))
        if "3" in sections:
            todo_batches = parse_todo_section(sections["3"])
        oq_items = parse_oq_section(sections.get("8", []))
    except Exception as e:
        warnings.append(f"正文解析出错，已降级为仅 frontmatter：{path}（{e}）")

    return {
        "kind": "change",
        "id": cid,
        "seq": fm.get("seq"),
        "title": fm.get("title") or cid,
        "summary": fm.get("summary") or "",
        "status": status,
        "tier": tier,
        "type": fm.get("type") or "feature",
        "created": fm.get("created"),
        "base_commit": fm.get("base_commit"),
        "commits": fm.get("commits") or [],
        "issue": fm.get("issue"),
        "pr": fm.get("pr"),
        "test_lock_commit": fm.get("test_lock_commit"),
        "intent": intent_text,
        "decisions": decisions,
        "ac": ac_items,
        "todo": todo_batches,
        "oq": oq_items,
        "dirname": dirname,
        "worktree": str(worktree_path),
        "path": str(path),
    }


def scan_all_changes(cfg, worktrees, warnings):
    by_id = {}
    for wt in worktrees:
        changes_dir = Path(wt["path"]) / cfg["doc_root"] / "changes"
        if not changes_dir.is_dir():
            continue
        for child in sorted(changes_dir.iterdir()):
            cf = child / "change.md"
            if not child.is_dir() or not cf.is_file():
                continue
            rec = parse_change_file(cf, wt["path"], child.name, warnings)
            if rec is None:
                continue
            rec["branch"] = wt.get("branch")
            by_id.setdefault(rec["id"], []).append(rec)

    def status_rank(r):
        try:
            return CHANGE_STATUS_ORDER.index(r["status"])
        except ValueError:
            return -1

    winners = [recs[0] if len(recs) == 1 else max(recs, key=status_rank) for recs in by_id.values()]

    seq_map = {}
    for w in winners:
        if w.get("seq") is not None:
            seq_map.setdefault(w["seq"], set()).add(w["id"])
    for seq, ids in sorted(seq_map.items(), key=lambda kv: str(kv[0])):
        if len(ids) > 1:
            warnings.append(f"撞号：seq #{seq} 同时被 {', '.join(sorted(ids))} 占用")

    return winners


def count_ac(ac_items):
    return sum(1 for a in ac_items if a["done"]), len(ac_items)


def count_todo(todo_batches):
    items = [it for b in (todo_batches or []) for it in b["items"]]
    return sum(1 for t in items if t["done"]), len(items)
