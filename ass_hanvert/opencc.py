import re
from typing import Literal

from opencc import OpenCC

from .converter import Converter, Direction

_cc_cache: dict[str, OpenCC] = {}
_repeat_pattern = re.compile(r"([\u4e00-\u9fa5])(\1*)(?=(…{1,2}|\.{3,6}\s?)\1)")
_restore_pattern = re.compile(r"\[:Repeat([\u4e00-\u9fa5])(\1*)](…{1,2}|\.{3,6}\s?)(.)")


def get_cc(config: str):
    if config not in _cc_cache:
        _cc_cache[config] = OpenCC(config)
    return _cc_cache[config]


class _OpenCCS2T(Converter):
    direction: Direction = Direction.S2T
    max_length: int = 30000

    def __init__(
        self,
        config: Literal[
            "s2t.json",
            "s2hk.json",
            "s2tw.json",
            "s2twp.json",
        ]
        | str = "s2t.json",
    ) -> None:
        super().__init__()
        self.config = config

    def _do_convert(self, text: str) -> str:
        cc = get_cc(self.config)
        text = _repeat_pattern.sub(r"[:Repeat\1\2]", text)
        text = cc.convert(text)
        text = _restore_pattern.sub(
            lambda m: f"{m.group(4) * (len(m.group(2)) + 1)}{m.group(3)}{m.group(4)}",
            text,
        )
        return cc.convert(text)


class _OpenCCT2S(Converter):
    direction: Direction = Direction.T2S
    max_length: int = 30000

    def __init__(
        self,
        config: Literal[
            "t2s.json",
            "hk2s.json",
            "tw2s.json",
        ]
        | str = "t2s.json",
    ) -> None:
        super().__init__()
        self.config = config

    def _do_convert(self, text: str) -> str:
        cc = get_cc(self.config)
        text = _repeat_pattern.sub(r"[:Repeat\1\2]", text)
        text = cc.convert(text)
        text = _restore_pattern.sub(
            lambda m: f"{m.group(4) * (len(m.group(2)) + 1)}{m.group(3)}{m.group(4)}",
            text,
        )
        return cc.convert(text)


class OpenCCConverter:
    Traditional: Converter = _OpenCCS2T("s2t.json")
    HongKong: Converter = _OpenCCS2T("s2hk.json")
    Taiwan: Converter = _OpenCCS2T("s2tw.json")
    TaiwanIdiom: Converter = _OpenCCS2T("s2twp.json")
    Simplified: Converter = _OpenCCT2S("t2s.json")
    HongKongToSimplified: Converter = _OpenCCT2S("hk2s.json")
    TaiwanToSimplified: Converter = _OpenCCT2S("tw2s.json")
