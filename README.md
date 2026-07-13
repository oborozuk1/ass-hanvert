# ass-hanvert

Simple ASS subtitle Simplified/Traditional Chinese conversion tool

## About

### Motivation

Popular conversion tools like Fanhuaji have decent accuracy and can detect subtitle formats for smart conversion, but they fail with karaoke-tagged subtitles. For example, `苹{\k}果` is incorrectly converted to `苹{\k}果` instead of the correct `蘋{\k}果`.

OpenCC, on the other hand, doesn't recognize subtitle formats, causing unwanted conversions (e.g., to fonts or Japanese text).

This project aims to solve these problems by implementing ASS subtitle conversion in Python, supporting multiple converters with good extensibility.

### Features

1. Skip Japanese subtitles (identified by style name, `\r` not yet supported)
2. Skip non-Chinese text
3. Ignore tags and line breaks during conversion, then restore original formatting
4. Display a warning if length changes before and after conversion
5. Multiple built-in converters (see list below)
6. Conversion result caching to reduce duplicate work

## Installation

```bash
pip install ass-hanvert
```

## Usage

### CLI

```bash
# Basic usage - convert a single file (default: S2T, Fanhuaji Taiwan)
ass-hanvert input.ass

# Specify converter
ass-hanvert -c OpenCC-TW input.ass

# T2S conversion
ass-hanvert -c OpenCC-S input.ass

# Batch process multiple files
ass-hanvert *.ass

# Use cache directory (speeds up repeated conversions)
ass-hanvert --cache ./cache input.ass

# Custom output file suffix
ass-hanvert --suffix traditional input.ass

# Full example: specify converter, reference converter, font mapping, and cache
ass-hanvert -c FHJ-TW --ref-converter OpenCC-S --font-mapping fonts.json --cache ./cache input.ass
```

Parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `files` | ASS subtitle file(s) to convert (supports multiple files and globs) | Required |
| `-c, --converter` | Converter name, see list below | FHJ-TW |
| `--ref-converter` | Reference converter, auto-selected based on main converter direction if omitted | Auto |
| `--suffix` | Output file suffix inserted before `.ass` | `cht` (S2T) / `chs` (T2S) |
| `--cache` | Cache directory path | None |
| `--no-skip-comment` | Do not skip comment lines | Skip |
| `--no-deduplicate` | Do not deduplicate | Deduplicate |
| `--no-sort` | Do not sort events | Sort by start time |
| `--font-mapping` | Font mapping JSON file path | None |
| `--pre-replace` | Pre-replace rules JSON file path | None |
| `--post-replace` | Post-replace rules JSON file path | None |
| `--protected-patterns` | Protected patterns JSON file path (list of regexes) | None |

Built-in converters:

**Simplified to Traditional:**

| Name | Description |
|------|-------------|
| FHJ-T | Fanhuaji - Traditional |
| FHJ-HK | Fanhuaji - Hong Kong |
| FHJ-TW | Fanhuaji - Taiwan |
| FHJ-WT | Fanhuaji - Wiki Traditional |
| OpenCC-T | OpenCC - Traditional |
| OpenCC-HK | OpenCC - Hong Kong |
| OpenCC-TW | OpenCC - Taiwan |
| OpenCC-TWP | OpenCC - Taiwan (with Taiwan-specific idioms) |

**Traditional to Simplified:**

| Name | Description |
|------|-------------|
| FHJ-S | Fanhuaji - Simplified |
| FHJ-CH | Fanhuaji - China |
| FHJ-WS | Fanhuaji - Wiki Simplified |
| OpenCC-S | OpenCC - Simplified |
| OpenCC-HKS | OpenCC - Hong Kong to Simplified |
| OpenCC-TWS | OpenCC - Taiwan to Simplified |

### Python API

```python
from light_ass import Document
from ass_hanvert import convert_ass

# Load subtitle
doc = Document.load("input.ass")

# Convert (default: Fanhuaji Taiwan)
convert_ass(doc)

# Or specify a converter (S2T)
from ass_hanvert import OpenCCConverter

convert_ass(doc, converter=OpenCCConverter.Taiwan)

# T2S
convert_ass(doc, converter=OpenCCConverter.Simplified)

# Save
doc.save("output.cht.ass")
```

## Credits

- [Fanhuaji API](http://zhconvert.org/)
- [OpenCC](https://github.com/BYVoid/OpenCC)
