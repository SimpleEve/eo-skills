"""frontmatter 手写简易 YAML 子集解析：标量 / 行内列表 / 行内注释，容错优先。"""

import re

FRONTMATTER_RE = re.compile(r"^---[ \t]*\n(.*?)\n---[ \t]*\n?", re.DOTALL)


def split_frontmatter(text):
    if text.startswith("﻿"):
        text = text[1:]
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    return parse_yaml_subset(m.group(1)), text[m.end():]


def parse_yaml_subset(text):
    data = {}
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            continue  # 容错：解析不了的行直接忽略，不让整份 frontmatter 崩掉
        key, _, value = line.partition(":")
        key = key.strip()
        if not key:
            continue
        data[key] = parse_yaml_scalar(value)
    return data


def parse_yaml_scalar(raw):
    value = raw.strip()
    if not value:
        return None
    if value[0] in "\"'":
        q = value[0]
        end = value.find(q, 1)
        return value[1:end] if end != -1 else value.strip(q)
    if value[0] == "[":
        end = value.find("]")
        inner = value[1:end] if end != -1 else value[1:]
        return [unquote(x.strip()) for x in inner.split(",")] if inner.strip() else []
    # 行内注释：# 前必须有空白才算注释，避免误伤内容本身
    m = re.search(r"\s#", value)
    if m:
        value = value[: m.start()].strip()
    if value in ("~", "null", "Null", "NULL", ""):
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def unquote(s):
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _format_scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return str(value)


def upsert_frontmatter_fields(text, updates):
    """在 frontmatter 内保序 upsert 标量字段。

    已存在的字段：原地替换冒号后的值，保留该行的缩进与行内注释；不存在的字段：以
    ``<key>: <value>`` 单行追加在关闭 ``---`` 之前。其余行的顺序、格式、注释一律原样保留。
    ``updates`` 为 ``{key: 标量值}``；``text`` 无合法 frontmatter 时原样返回。
    """
    if not updates:
        return text
    bom = ""
    body = text
    if body.startswith("﻿"):
        bom, body = "﻿", body[1:]
    m = FRONTMATTER_RE.match(body)
    if not m:
        return text
    fm_text = m.group(1)
    rest = body[m.end():]

    remaining = dict(updates)
    out_lines = []
    for line in fm_text.split("\n"):
        replaced = False
        for key in list(remaining):
            km = re.match(rf"^(\s*){re.escape(str(key))}(\s*):(.*)$", line)
            if not km:
                continue
            indent, after_colon = km.group(1), km.group(3)
            cm = re.search(r"\s+#.*$", after_colon)
            comment = after_colon[cm.start():] if cm else ""
            out_lines.append(f"{indent}{key}: {_format_scalar(remaining[key])}{comment}")
            del remaining[key]
            replaced = True
            break
        if not replaced:
            out_lines.append(line)

    for key, value in remaining.items():
        out_lines.append(f"{key}: {_format_scalar(value)}")

    return f"{bom}---\n" + "\n".join(out_lines) + "\n---\n" + rest
