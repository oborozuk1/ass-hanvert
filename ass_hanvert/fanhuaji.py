from typing import Literal

from .converter import Converter, Direction

FANHUAJI_API_URL = "https://api.zhconvert.org/convert"


class FanhuajiConverterBase(Converter):
    def __init__(
        self,
        converter_type: Literal["Traditional", "Hongkong", "Taiwan", "WikiTraditional", "Simplified"]
        | str = "Traditional",
        url: str = FANHUAJI_API_URL,
        direction: Direction | None = None,
    ) -> None:
        super().__init__()
        self.converter_type = converter_type
        self.url = url
        if direction is not None:
            self.direction = direction

    def _do_convert(self, text: str) -> str:
        import requests

        response = requests.post(self.url, data={"text": text, "converter": self.converter_type})
        response.raise_for_status()
        data = response.json()
        if data["code"] != 0:
            raise RuntimeError(f"Fanhuaji API Error: {data['msg']}")
        return data["data"]["text"]


class _FanhuajiS2T(FanhuajiConverterBase):
    direction: Direction = Direction.S2T


class _FanhuajiT2S(FanhuajiConverterBase):
    direction: Direction = Direction.T2S


class FanhuajiConverter:
    Traditional: Converter = _FanhuajiS2T("Traditional")
    Hongkong: Converter = _FanhuajiS2T("Hongkong")
    Taiwan: Converter = _FanhuajiS2T("Taiwan")
    WikiTraditional: Converter = _FanhuajiS2T("WikiTraditional")
    Simplified: Converter = _FanhuajiT2S("Simplified")
    China: Converter = _FanhuajiT2S("China")
    WikiSimplified: Converter = _FanhuajiT2S("WikiSimplified")
