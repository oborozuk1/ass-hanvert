import time
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
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 15.0,
    ) -> None:
        super().__init__()
        self.converter_type = converter_type
        self.url = url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        if direction is not None:
            self.direction = direction

    def _do_convert(self, text: str) -> str:
        import requests

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    self.url,
                    data={"text": text, "converter": self.converter_type},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                if data["code"] != 0:
                    raise RuntimeError(f"Fanhuaji API Error: {data['msg']}")
                return data["data"]["text"]
            except (requests.ConnectionError, requests.Timeout) as e:
                last_error = e
            except requests.HTTPError as e:
                if e.response is not None and 500 <= e.response.status_code < 600:
                    last_error = e
                else:
                    raise
            if attempt < self.max_retries:
                time.sleep(self.retry_delay * (2**attempt))
        raise last_error


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
