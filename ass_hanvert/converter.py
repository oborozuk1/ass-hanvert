from abc import ABC, abstractmethod
from enum import StrEnum

from .text_utils import protect_patterns, replace_text, restore_protected, split_by_length


class Direction(StrEnum):
    S2T = "s2t"
    T2S = "t2s"


class Converter(ABC):
    direction: Direction

    def __init__(self) -> None:
        self.pre_replace: dict[str, str] = {}
        self.post_replace: dict[str, str] = {}
        self.protected_patterns: list[str] = []
        self.max_length: int = 15000

    @abstractmethod
    def _do_convert(self, text: str) -> str: ...

    def convert(
        self,
        text: str,
        pre_replace: dict[str, str] | None = None,
        post_replace: dict[str, str] | None = None,
        protected_patterns: list[str] | None = None,
        max_length: int | None = None,
    ) -> str:
        if text == "":
            return text

        _pre = pre_replace if pre_replace is not None else self.pre_replace
        _post = post_replace if post_replace is not None else self.post_replace
        _protected = protected_patterns if protected_patterns is not None else self.protected_patterns
        _max = max_length if max_length is not None else self.max_length

        parts = split_by_length(text, _max) if self.max_length > 0 else [text]
        return "\n".join(self._convert_part(part, _pre, _post, _protected) for part in parts)

    def _convert_part(
        self,
        text: str,
        pre_replace: dict[str, str],
        post_replace: dict[str, str],
        protected_patterns: list[str],
    ) -> str:
        text = replace_text(text, pre_replace)
        text, protected = protect_patterns(text, protected_patterns)
        text = self._do_convert(text)
        text = replace_text(text, post_replace)
        text = restore_protected(text, protected)
        return text
