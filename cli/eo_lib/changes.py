"""change.md 正文解析、change 目录扫描与 AC/TODO 计数。"""

import hashlib
import re
from pathlib import Path

from .freshness import tree_max_mtime
from .frontmatter import split_frontmatter
from .gitio import run_git

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


def status_rank(rec):
    try:
        return CHANGE_STATUS_ORDER.index(rec["status"])
    except ValueError:
        return -1


def scan_changes_grouped(cfg, worktrees, warnings):
    """扫描全部 worktree 的 change，按 id 分组返回 {id: [rec, ...]}（未去重，保留各 worktree 候选）。"""
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
    return by_id


def pick_change_winner(recs):
    """同 id 多候选取状态最高者（单条直接返回）。"""
    return recs[0] if len(recs) == 1 else max(recs, key=status_rank)


def group_changes_by_divergence(recs):
    """同 id 候选按 change.md 内容 sha256 分组：实质分叉（>1 组）返回多组，内容一致副本合并为一组。
    与 resolve_change 的整文件 hash 比较同源（读取失败归入 None 桶，不阻断其余分组）。
    """
    if len(recs) <= 1:
        return [list(recs)]
    groups = {}
    order = []
    for r in recs:
        try:
            digest = hashlib.sha256(Path(r["path"]).read_bytes()).hexdigest()
        except Exception:
            digest = None
        if digest not in groups:
            groups[digest] = []
            order.append(digest)
        groups[digest].append(r)
    return [groups[d] for d in order]


def _change_activity_epoch(rec, doc_root):
    """change 目录的动静尺子：本 worktree HEAD 末次提交 + 目录树 max-mtime 取大（epoch 秒）。

    不用 ``git log --all``：其它分支的新提交不能记到未回拉副本上。
    """
    rel_dir = str(Path(doc_root) / "changes" / rec["dirname"])
    stamps = []
    out = run_git(["log", "-1", "--format=%ct", "--", rel_dir], cwd=rec["worktree"]).strip()
    if out.isdigit():
        stamps.append(int(out))
    mtime = tree_max_mtime(Path(rec["worktree"]) / rel_dir)
    if mtime:
        stamps.append(mtime)
    return max(stamps) if stamps else 0


def _change_recency_key(rec, doc_root):
    """出卡平手键：活动更新 → 状态更高 → 路径字典序（降序，与折叠排序同源）。"""
    return (_change_activity_epoch(rec, doc_root), status_rank(rec), rec["path"])


def _stale_behind_latest(recs, doc_root):
    """相对「最近活动」最新的那份：状态更低且动静更旧的视为过期遗留（未回拉），过滤。

    不能拿 main worktree 当状态门槛：主目录常是最老、未跟上的那份，门槛会把
    正在改的新 worktree（状态暂时更低或正文更新）误杀掉，出卡变成「新 PWD + 旧正文」。
    """
    if len(recs) <= 1:
        return list(recs)
    latest = max(recs, key=lambda r: _change_recency_key(r, doc_root))
    latest_epoch = _change_activity_epoch(latest, doc_root)
    latest_rank = status_rank(latest)
    keep = []
    for rec in recs:
        if rec is latest:
            keep.append(rec)
            continue
        if status_rank(rec) < latest_rank and _change_activity_epoch(rec, doc_root) < latest_epoch:
            continue
        keep.append(rec)
    return keep


def scan_all_changes_split(cfg, worktrees, warnings, base_worktree=None):
    """scan_all_changes 的分叉感知变体：同 id 折叠为一张卡。
    内容一致副本合并为单卡、无标记，代表按最近活动选取（与分叉出卡同一把尺）；
    实质分叉时由最近活动最新的变体出卡，其余变体代表收进 ``forks`` 并置 ``diverged``。
    过期判定相对最近活动最新的那份：状态更低且动静更旧的副本先过滤，不进 forks。
    base_worktree 保留给调用方兼容，不再作为状态门槛。
    """
    by_id = scan_changes_grouped(cfg, worktrees, warnings)
    cards = []
    doc_root = cfg["doc_root"]
    for recs in by_id.values():
        pool = _stale_behind_latest(recs, doc_root)
        groups = group_changes_by_divergence(pool)
        keys = {}

        def key_of(r):
            k = id(r)
            if k not in keys:
                keys[k] = _change_recency_key(r, doc_root)
            return keys[k]

        if len(groups) == 1:
            cards.append(max(groups[0], key=key_of))
            continue

        reps = [max(g, key=key_of) for g in groups]
        reps.sort(key=key_of, reverse=True)
        card = reps[0]
        card["diverged"] = True
        card["forks"] = reps[1:]
        cards.append(card)

    seq_map = {}
    for c in cards:
        if c.get("seq") is not None:
            seq_map.setdefault(c["seq"], set()).add(c["id"])
    for seq, ids in sorted(seq_map.items(), key=lambda kv: str(kv[0])):
        if len(ids) > 1:
            warnings.append(f"撞号：seq #{seq} 同时被 {', '.join(sorted(ids))} 占用")

    return cards


def scan_all_changes(cfg, worktrees, warnings):
    by_id = scan_changes_grouped(cfg, worktrees, warnings)
    winners = [pick_change_winner(recs) for recs in by_id.values()]

    seq_map = {}
    for w in winners:
        if w.get("seq") is not None:
            seq_map.setdefault(w["seq"], set()).add(w["id"])
    for seq, ids in sorted(seq_map.items(), key=lambda kv: str(kv[0])):
        if len(ids) > 1:
            warnings.append(f"撞号：seq #{seq} 同时被 {', '.join(sorted(ids))} 占用")

    return winners


def resolve_change(recs, origin_worktree):
    """多 worktree 候选消歧的权威选择：返回 (权威 rec, None) 或 (None, [候选路径...]) 表示内容分叉 fail-closed。

    一次性应用：最高状态 → 发起 run 的 worktree 内那份 → 同内容任取（路径稳定排序）→ 内容分叉拒绝。
    计划快照与身份回写落点共用同一结果，杜绝 plan 后重新推导落点导致的两套选择错位。
    """
    if not recs:
        return None, []
    top = max(status_rank(r) for r in recs)
    cands = [r for r in recs if status_rank(r) == top]
    if len(cands) == 1:
        return cands[0], None

    pool = cands
    if origin_worktree:
        ow = str(Path(origin_worktree).resolve())
        origin_cands = [c for c in cands if str(Path(c["worktree"]).resolve()) == ow]
        if origin_cands:
            pool = origin_cands
    if len(pool) == 1:
        return pool[0], None

    hashes = {}
    for c in pool:
        try:
            digest = hashlib.sha256(Path(c["path"]).read_bytes()).hexdigest()
        except Exception:
            digest = None
        hashes.setdefault(digest, []).append(c)
    if len(hashes) == 1 and None not in hashes:
        return sorted(pool, key=lambda c: c["path"])[0], None
    return None, sorted(c["path"] for c in cands)


def resolve_writeback_path(recs, origin_worktree):
    """resolve_change 的路径视图：返回 (目标 change.md 路径, None) 或 (None, [候选路径...])。"""
    rec, cands = resolve_change(recs, origin_worktree)
    return (rec["path"] if rec else None), cands


def count_ac(ac_items):
    return sum(1 for a in ac_items if a["done"]), len(ac_items)


def count_todo(todo_batches):
    items = [it for b in (todo_batches or []) for it in b["items"]]
    return sum(1 for t in items if t["done"]), len(items)
