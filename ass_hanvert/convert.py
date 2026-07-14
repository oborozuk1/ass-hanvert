from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass

from diff_match_patch import diff_match_patch
from light_ass import Dialog, Document, TagParser
from light_ass.curly.parser import ParsedLine, TextNode
from light_ass.curly.tags import DrawingBaselineOffsetTag, DrawingModeTag, PositionTag, ResetStyleTag, FontNameTag

from .converter import Converter, Direction
from .fanhuaji import FanhuajiConverter
from .opencc import OpenCCConverter

_CJK_RE = re.compile(r"[\u4e00-\u9fa5]")

tag_parser = TagParser([DrawingModeTag, DrawingBaselineOffsetTag, PositionTag, FontNameTag, ResetStyleTag])

_DMP = diff_match_patch()


@dataclass
class Line:
    event: Dialog
    segments: ParsedLine
    original_text: str | None = None
    nodes_to_convert: list[TextNode] | None = None
    converted_text: str | None = None
    ref_text: str | None = None
    need_verify: bool = False
    dup_lines: list[Line] | None = None

    @classmethod
    def from_event(cls, event: Dialog) -> Line:
        segments = event.parse_tags(tag_parser, parse_escape_nodes=True)
        return cls(
            event=event,
            segments=segments,
        )


def collect_nodes(
    line: Line,
    skip_styles: Iterable[str] = ("JP", "JA"),
    skip_styles_exact: Iterable[str] = (),
):
    current_style = line.event.style
    nodes = []
    for node in line.segments:
        if isinstance(node, ResetStyleTag):
            current_style = node.value or line.event.style
        elif isinstance(node, TextNode):
            if not node.text:
                continue
            if any(tok in current_style for tok in skip_styles):
                continue
            if any(current_style == tok for tok in skip_styles_exact):
                continue
            nodes.append(node)
    line.nodes_to_convert = nodes
    line.original_text = "".join(node.text for node in nodes)


def collect_lines(
    lines: list[Line],
    skip_comment: bool = True,
    skip_styles: Iterable[str] = ("JP", "JA"),
    skip_styles_exact: Iterable[str] = (),
) -> list[Line]:
    result = []
    for line in lines:
        if "Hanvert: Skip" in line.event.effect:
            continue
        if skip_comment and line.event.comment:
            continue
        if not _CJK_RE.search(line.event.text_stripped):
            continue
        collect_nodes(line, skip_styles, skip_styles_exact)
        if line.nodes_to_convert:
            result.append(line)
    return result


def deduplicated_lines(lines: list[Line]) -> None:
    result = []
    dup_lines = []
    prev_line: Line | None = None
    for line in lines:
        if prev_line and line.original_text == prev_line.original_text:
            dup_lines.append(line)
            continue
        result.append(line)
        if prev_line and dup_lines:
            prev_line.dup_lines = dup_lines
            dup_lines = []
        prev_line = line
    if dup_lines:
        prev_line.dup_lines = dup_lines
    lines[:] = result


def convert_lines(
    lines: list[Line],
    converter: Converter,
    pre_replace: dict[str, str] | None = None,
    post_replace: dict[str, str] | None = None,
    protected_patterns: list[str] | None = None,
) -> None:
    lines_to_convert = [line for line in lines if line.converted_text is None]
    all_text = "\n".join(line.original_text for line in lines_to_convert)
    converted_texts = converter.convert(all_text, pre_replace, post_replace, protected_patterns).splitlines()
    for line, converted in zip(lines_to_convert, converted_texts, strict=True):
        line.converted_text = converted


def add_ref_text(
    lines: list[Line],
    converter: Converter,
    pre_replace: dict[str, str] | None = None,
    post_replace: dict[str, str] | None = None,
    protected_patterns: list[str] | None = None,
) -> None:
    ref_lines = []
    for line in lines:
        if len(line.nodes_to_convert) > 1:
            ref_lines.append(line)
        else:
            line.ref_text = line.converted_text
    all_text = "\n".join(line.original_text for line in ref_lines)
    converted_ref_texts = converter.convert(all_text, pre_replace, post_replace, protected_patterns).splitlines()
    for line, converted in zip(ref_lines, converted_ref_texts, strict=True):
        line.ref_text = converted


def align_whitespace(str_a: str, str_b: str) -> str:
    lead_part = str_b[: -len(str_b.lstrip())]
    trail_part = str_b[len(str_b.rstrip()) :]
    return lead_part + str_a.strip() + trail_part


def _dmp_opcodes(a: str, b: str):
    diffs = _DMP.diff_main(a, b)
    _DMP.diff_cleanupSemantic(diffs)

    i = 0
    j = 0
    pending_delete = None
    for op, text in diffs:
        n = len(text)
        if op == 0:
            if pending_delete is not None:
                di1, di2 = pending_delete
                yield "delete", di1, di2, j, j
                pending_delete = None
            yield "equal", i, i + n, j, j + n
            i += n
            j += n
        elif op == -1:
            if pending_delete is None:
                pending_delete = (i, i + n)
            else:
                pending_delete = (pending_delete[0], pending_delete[1] + n)
            i += n
        else:
            if pending_delete is not None:
                di1, di2 = pending_delete
                yield "replace", di1, di2, j, j + n
                pending_delete = None
                j += n
            else:
                yield "insert", i, i, j, j + n
                j += n

    if pending_delete is not None:
        di1, di2 = pending_delete
        yield "delete", di1, di2, j, j


def _regroup(line: Line, converted_text: str, ref_text: str) -> bool:
    if len(line.original_text) != len(ref_text):
        raise ValueError("original_text and ref_text must have the same length")

    length_changed = False
    opcodes = list(_dmp_opcodes(ref_text, converted_text))

    i = 0
    pos = 0
    for segment in line.nodes_to_convert:
        max_pos = pos + len(segment.text)
        texts = []
        while pos < max_pos:
            tag, i1, i2, j1, j2 = opcodes[i]
            if i1 < pos:
                j1 = j1 + (pos - i1)
                i1 = pos
            if i2 > max_pos:
                j2 = j1 + (max_pos - pos)
                i2 = max_pos
            else:
                i += 1
            length_changed |= i2 - i1 != j2 - j1
            if tag != "delete":
                texts.append(converted_text[j1:j2])
            pos += i2 - i1
        segment.text = "".join(texts)

    return length_changed


def regroup(line: Line, converted_text: str, ref_text: str) -> None:
    if len(line.segments) == 1:
        line.event.text = converted_text
        return

    event = line.event
    length_changed = _regroup(line, converted_text, ref_text)
    event.text = line.segments.to_ass()
    if length_changed:
        if event.effect:
            event.effect += "; Hanvert: Len diff"
        else:
            event.effect = "Hanvert: Len diff"


def apply_conversions(lines: list[Line]) -> None:
    for line in lines:
        converted_text = align_whitespace(line.converted_text, line.original_text)
        regroup(line, converted_text, line.ref_text)
        if line.dup_lines:
            for dup_line in line.dup_lines:
                regroup(dup_line, converted_text, line.ref_text)


def apply_font_mapping(document: Document, lines: list[Line], font_mapping: dict[str, str]) -> None:
    font_mapping |= {f"@{old}": new for old, new in font_mapping.items()}
    for style in document.styles.values():
        if style.fontname in font_mapping:
            style.fontname = font_mapping[style.fontname]

    for line in lines:
        changed = False
        for tag in line.segments.parts:
            if not isinstance(tag, FontNameTag) or not tag.value:
                continue
            val = tag.value
            if val in font_mapping:
                tag.value = font_mapping[val]
                changed = True
        if changed:
            line.event.text = line.segments.to_ass()


def get_md5(obj: dict) -> str:
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def restore_cache(lines: list[Line], path: str, md5: str) -> None:
    if not os.path.exists(path):
        return

    cache_texts = []
    cache_converted = []
    md5_found = False
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            if line.startswith("#"):
                key, sep, value = line[1:].partition(":")
                if sep and key.strip() == "config md5":
                    if value.strip() == md5:
                        md5_found = True
                    else:
                        return
                continue
            if not md5_found:
                return
            text, _, converted = line.partition("\t")
            cache_texts.append(text)
            cache_converted.append(converted)

    texts = [line.original_text for line in lines]
    a = _DMP.diff_linesToChars("\n".join(texts), "\n".join(cache_texts))
    diffs = _DMP.diff_main(a[0], a[1], False)
    texts_pos = 0
    cache_pos = 0
    for op, text in diffs:
        n = len(text)
        if op == 0:
            for i in range(n):
                lines[texts_pos + i].converted_text = cache_converted[cache_pos + i]
            texts_pos += n
            cache_pos += n
        elif op == 1:
            cache_pos += n
        elif op == -1:
            texts_pos += n


def write_cache(lines: list[Line], path: str, md5: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# config md5: {md5}\n")
        f.write("".join(f"{line.original_text}\t{line.converted_text}\n" for line in lines))


def resolve_converter(
    converter: Converter | None = None,
    ref_converter: Converter | None = None,
) -> tuple[Converter, Converter]:
    if converter is None:
        converter = FanhuajiConverter.Taiwan
    if ref_converter is None:
        if converter.direction == Direction.T2S:
            ref_converter = OpenCCConverter.Simplified
        else:
            ref_converter = OpenCCConverter.Traditional
    elif converter.direction != ref_converter.direction:
        raise ValueError("converter and ref_converter must be the same direction")
    return converter, ref_converter


def convert_ass(
    document: Document,
    converter: Converter | None = None,
    ref_converter: Converter | None = None,
    *,
    skip_comment: bool = True,
    skip_styles: Iterable[str] = ("JP", "JA"),
    skip_styles_exact: Iterable[str] = (),
    deduplicate: bool = True,
    sort_events: bool = True,
    cache_path: str | None = None,
    alt_fonts: dict[str, str] | None = None,
    pre_replace: dict[str, str] | None = None,
    post_replace: dict[str, str] | None = None,
    protected_patterns: list[str] | None = None,
) -> None:
    converter, ref_converter = resolve_converter(converter, ref_converter)

    config = converter.__dict__ | {
        "pre_replace": pre_replace,
        "post_replace": post_replace,
        "protected_patterns": protected_patterns,
    }
    config_md5 = get_md5(config)

    events = [Line.from_event(event) for event in document.events]
    lines = collect_lines(events, skip_comment, skip_styles, skip_styles_exact)
    if sort_events:
        lines.sort(key=lambda line: (line.event.start, line.event.text_stripped))
    if deduplicate:
        deduplicated_lines(lines)

    if cache_path is not None:
        restore_cache(lines, cache_path, config_md5)

    convert_lines(lines, converter, pre_replace, post_replace, protected_patterns)
    add_ref_text(lines, ref_converter)
    apply_conversions(lines)

    if alt_fonts is not None:
        apply_font_mapping(document, events, alt_fonts)

    if cache_path is not None:
        write_cache(lines, cache_path, config_md5)
