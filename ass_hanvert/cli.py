import argparse
import json
import sys
from pathlib import Path

from light_ass import Document

from ass_hanvert import (
    Converter,
    FanhuajiConverter,
    OpenCCConverter,
    convert_ass,
)

CONVERTER_MAP: dict[str, Converter] = {
    "FHJ-T": FanhuajiConverter.Traditional,
    "FHJ-HK": FanhuajiConverter.Hongkong,
    "FHJ-TW": FanhuajiConverter.Taiwan,
    "FHJ-WT": FanhuajiConverter.WikiTraditional,
    "FHJ-S": FanhuajiConverter.Simplified,
    "FHJ-CH": FanhuajiConverter.China,
    "FHJ-WS": FanhuajiConverter.WikiSimplified,
    "OpenCC-T": OpenCCConverter.Traditional,
    "OpenCC-HK": OpenCCConverter.HongKong,
    "OpenCC-TW": OpenCCConverter.Taiwan,
    "OpenCC-TWP": OpenCCConverter.TaiwanIdiom,
    "OpenCC-S": OpenCCConverter.Simplified,
    "OpenCC-HKS": OpenCCConverter.HongKongToSimplified,
    "OpenCC-TWS": OpenCCConverter.TaiwanToSimplified,
}


def load_json(path: str | None) -> dict | list | None:
    if path is None:
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def make_output_path(input_path: Path, suffix: str) -> Path:
    return input_path.with_name(f"{input_path.stem}.{suffix}.ass")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ASS subtitle Chinese conversion tool",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="ASS subtitle file(s) to convert",
    )
    parser.add_argument(
        "-c",
        "--converter",
        choices=list(CONVERTER_MAP.keys()),
        default="FHJ-TW",
        help="Converter (default: FHJ-TW)",
    )
    parser.add_argument(
        "--ref-converter",
        choices=list(CONVERTER_MAP.keys()),
        default=None,
        help="Reference converter (default: auto-select based on main converter direction)",
    )
    parser.add_argument(
        "--suffix",
        default=None,
        help="Output file suffix inserted before .ass (default: cht for S2T, chs for T2S)",
    )
    parser.add_argument(
        "--cache",
        default=None,
        help="Cache directory path",
    )
    parser.add_argument(
        "--no-skip-comment",
        action="store_true",
        help="Do not skip comment lines",
    )
    parser.add_argument(
        "--no-deduplicate",
        action="store_true",
        help="Do not deduplicate",
    )
    parser.add_argument(
        "--no-sort",
        action="store_true",
        help="Do not sort events",
    )
    parser.add_argument(
        "--font-mapping",
        default=None,
        help="Font mapping JSON file path",
    )
    parser.add_argument(
        "--pre-replace",
        default=None,
        help="Pre-replace rules JSON file path",
    )
    parser.add_argument(
        "--post-replace",
        default=None,
        help="Post-replace rules JSON file path",
    )
    parser.add_argument(
        "--protected-patterns",
        default=None,
        help="Protected patterns JSON file path (list of regexes)",
    )

    args = parser.parse_args()

    converter = CONVERTER_MAP[args.converter]
    ref_converter = CONVERTER_MAP[args.ref_converter] if args.ref_converter else None
    font_mapping = load_json(args.font_mapping)
    pre_replace = load_json(args.pre_replace)
    post_replace = load_json(args.post_replace)
    protected_patterns = load_json(args.protected_patterns)

    if args.suffix is not None:
        suffix = args.suffix
    elif converter.direction == "s2t":
        suffix = "cht"
    else:
        suffix = "chs"

    for file_str in args.files:
        input_path = Path(file_str)
        if not input_path.exists():
            print(f"Error: file not found - {input_path}", file=sys.stderr)
            continue

        output_path = make_output_path(input_path, suffix)

        cache_path: str | None = None
        if args.cache is not None:
            cache_dir = Path(args.cache)
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path = str(cache_dir / f"{input_path.stem}.txt")

        doc = Document.load(str(input_path))
        convert_ass(
            doc,
            converter=converter,
            ref_converter=ref_converter,
            skip_comment=not args.no_skip_comment,
            deduplicate=not args.no_deduplicate,
            sort_events=not args.no_sort,
            cache_path=cache_path,
            alt_fonts=font_mapping,
            pre_replace=pre_replace,
            post_replace=post_replace,
            protected_patterns=protected_patterns,
        )
        doc.save(str(output_path))
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
