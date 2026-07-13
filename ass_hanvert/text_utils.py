import re


def replace_text(text: str, replace_map: dict[str, str]) -> str:
    for old, new in replace_map.items():
        text = text.replace(old, new)
    return text


def protect_patterns(text: str, patterns: list[str]) -> tuple[str, dict[str, str]]:
    protected: dict[str, str] = {}
    i = 0
    for pattern in patterns:

        def _replace(m: re.Match) -> str:
            nonlocal i
            if m.group(0) not in protected:
                i += 1
                protected[m.group(0)] = f"_※{i}_"
            return protected[m.group(0)]

        text = re.sub(pattern, _replace, text)
    return text, protected


def restore_protected(text: str, protected: dict[str, str]) -> str:
    for original, marker in protected.items():
        text = text.replace(marker, original)
    return text


def split_by_length(text: str, max_length: int) -> list[str]:
    lines = text.splitlines()
    result: list[str] = []
    current: list[str] = []
    length = 0

    for line in lines:
        line_length = len(line)
        if line_length > max_length:
            if current:
                result.append("\n".join(current))
            result.append(line)
            current = []
            length = 0
            continue

        new_length = length + line_length + (1 if current else 0)
        if new_length > max_length and current:
            result.append("\n".join(current))
            current = [line]
            length = line_length
        else:
            current.append(line)
            length = new_length

    if current:
        result.append("\n".join(current))

    return result
