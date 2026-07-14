import argparse
import glob
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


def make_output_path(input_path: Path, suffix: str, output_dir: Path | None = None) -> Path:
    path = input_path.with_name(f"{input_path.stem}.{suffix}.ass")
    if output_dir is not None:
        path = output_dir / path.name
    return path


def expand_files(patterns: list[str]) -> list[Path]:
    result: list[Path] = []
    for pattern in patterns:
        p = Path(pattern)
        if p.is_dir():
            result.extend(sorted(p.glob("*.ass")))
        elif "*" in pattern or "?" in pattern or "[" in pattern:
            result.extend(Path(m) for m in sorted(glob.glob(pattern)))
        else:
            result.append(p)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ASS subtitle Chinese conversion tool",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="ASS subtitle file(s), directories, or glob patterns to convert",
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
        "--output-dir",
        default=None,
        help="Output directory (default: alongside each input file)",
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
    parser.add_argument(
        "--skip-styles",
        default="JP,JA",
        help="Comma-separated style substrings to skip (default: JP,JA)",
    )
    parser.add_argument(
        "--skip-styles-exact",
        default="",
        help="Comma-separated exact style names to skip (default: none)",
    )
    parser.add_argument(
        "--no-skip-inline-styles",
        action="store_true",
        help="Do not skip inline override styles",
    )

    args = parser.parse_args()

    converter = CONVERTER_MAP[args.converter]
    ref_converter = CONVERTER_MAP[args.ref_converter] if args.ref_converter else None
    font_mapping = load_json(args.font_mapping)
    pre_replace = load_json(args.pre_replace)
    post_replace = load_json(args.post_replace)
    protected_patterns = load_json(args.protected_patterns)
    skip_styles = [s for s in args.skip_styles.split(",") if s] if args.skip_styles else ()
    skip_styles_exact = [s for s in args.skip_styles_exact.split(",") if s] if args.skip_styles_exact else ()

    if args.suffix is not None:
        suffix = args.suffix
    elif converter.direction == "s2t":
        suffix = "cht"
    else:
        suffix = "chs"

    output_dir = Path(args.output_dir) if args.output_dir else None
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    input_files = expand_files(args.files)
    if not input_files:
        print("Error: no input files found", file=sys.stderr)
        sys.exit(1)

    for input_path in input_files:
        if not input_path.exists():
            print(f"Error: file not found - {input_path}", file=sys.stderr)
            continue

        output_path = make_output_path(input_path, suffix, output_dir)

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
            skip_styles=skip_styles,
            skip_styles_exact=skip_styles_exact,
            skip_inline_styles=not args.no_skip_inline_styles,
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
