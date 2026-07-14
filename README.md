# ass-hanvert

简易 ASS 字幕简繁体转换工具

## 关于

### 动机

目前主流的繁转换工具（如繁化姬）虽然转换精度尚可，且能检测字幕格式进行智能转换，但在处理带有标签的字幕时会出错。例如，`苹{\k}果` 会被错误地转换为 `苹{\k}果`，而正确的结果应该是 `蘋{\k}果`。

而 OpenCC 则不支持识别字幕格式，容易造成不必要的转换（如转换到字体名称或日语文字等问题）。

本项目旨在通过 Python 实现 ASS 字幕转换，支持多种转换器，以解决上述问题。

### 功能特性

1. 跳过日文字幕（通过样式名识别，可自定义）
2. 跳过非中文文本
3. 转换时忽略标签和换行符，转换完成后恢复原始格式
4. 转换前后长度发生变化时显示警告
5. 内置多种转换器（见下方列表）
6. 转换结果缓存，减少重复工作
7. 支持通过 Effect 字段标记跳过特定行

## 安装

```bash
pip install ass-hanvert
pip install "ass-hanvert[openai]"  # 如果希望使用 OpenAIConverter
```

## 使用方法

### 命令行（CLI）

```bash
# 基本用法 - 转换单个/多个文件（默认：简转繁，繁化姬-台湾）
ass-hanvert input1.ass input2.ass

# 转换整个目录下的所有 .ass 文件，输出到指定目录
ass-hanvert --output-dir ./output ./subtitles/

# 指定转换器
ass-hanvert -c OpenCC-TW input.ass

# 使用缓存目录（省去重复转换）
ass-hanvert --cache ./cache input.ass

# 自定义输出文件后缀
ass-hanvert --suffix traditional input.ass

# 完整示例：指定转换器、参考转换器、字体名称映射及缓存
ass-hanvert -c FHJ-TW --ref-converter OpenCC-T --font-mapping fonts.json --cache ./cache input.ass
```

参数说明：

| 参数 | 说明                        | 默认值 |
|------|---------------------------|--------|
| `files` | 要转换的 ASS 字幕文件、目录或通配符模式（支持多个） | 必填 |
| `-c, --converter` | 转换器名称，见下方列表               | FHJ-TW |
| `--ref-converter` | 参考转换器，若省略则根据主转换器方向自动选择    | 自动 |
| `--suffix` | 输出文件后缀，插入在 `.ass` 之前      | `cht`（简转繁）/ `chs`（繁转简） |
| `--output-dir` | 输出目录，不指定则输出到各源文件旁      | 源文件旁 |
| `--cache` | 缓存目录路径                    | 无 |
| `--no-skip-comment` | 转换时不跳过注释行                 | 跳过 |
| `--no-deduplicate` | 转换时不去重                    | 去重 |
| `--no-sort` | 转换时不对事件排序                 | 按开始时间排序 |
| `--font-mapping` | 字体名称映射 JSON 文件路径          | 无 |
| `--pre-replace` | 前置替换列表 JSON 文件路径          | 无 |
| `--post-replace` | 后置替换列表 JSON 文件路径          | 无 |
| `--protected-patterns` | 保护模式 JSON 文件路径（正则表达式列表）   | 无 |
| `--skip-styles` | 跳过的样式名子字符串（逗号分隔）       | `JP,JA` |
| `--skip-styles-exact` | 跳过的精确样式名（逗号分隔）          | 无 |
| `--no-skip-inline-styles` | 不跳过行内覆盖样式（`\r` 标签切换的样式） | 跳过 |

内置转换器：

**简转繁：**

| 名称 | 说明 |
|------|------|
| FHJ-T | 繁化姬 - 繁体 |
| FHJ-HK | 繁化姬 - 香港 |
| FHJ-TW | 繁化姬 - 台湾 |
| FHJ-WT | 繁化姬 - 维基繁体 |
| OpenCC-T | OpenCC - 繁体 |
| OpenCC-HK | OpenCC - 香港 |
| OpenCC-TW | OpenCC - 台湾 |
| OpenCC-TWP | OpenCC - 台湾（含台湾常用语） |

**繁转简：**

| 名称 | 说明 |
|------|------|
| FHJ-S | 繁化姬 - 简体 |
| FHJ-CH | 繁化姬 - 大陆 |
| FHJ-WS | 繁化姬 - 维基简体 |
| OpenCC-S | OpenCC - 简体 |
| OpenCC-HKS | OpenCC - 香港转简体 |
| OpenCC-TWS | OpenCC - 台湾转简体 |

### Python API

```python
from light_ass import Document
from ass_hanvert import convert_ass

# 加载字幕
doc = Document.load("input.ass")

# 转换（默认：繁化姬-台湾）
convert_ass(doc)

# 或指定转换器（简转繁）
from ass_hanvert import OpenCCConverter

convert_ass(doc, converter=OpenCCConverter.Taiwan)

# 繁转简
stats = convert_ass(doc, converter=OpenCCConverter.Simplified)
print(stats)

# 保存
doc.save("output.cht.ass")
```

#### 跳过特定行

可以通过以下方式自定义跳过哪些行：

**样式名**

默认跳过样式名包含 `JP` 或 `JA` 的行。可通过 `skip_styles` 自定义，也可用 `skip_styles_exact` 做精确匹配：

```python
# 自定义子字符串匹配
convert_ass(doc, skip_styles=("JP", "JA", "EN"))

# 仅精确匹配样式名（不做子字符串匹配）
convert_ass(doc, skip_styles=(), skip_styles_exact=("JP", "JA"))

# 两者可同时使用
convert_ass(doc, skip_styles=("JP",), skip_styles_exact=("EN-Lit",))
```

**Effect 字段标记**

在 ASS 文件中给行的 Effect 字段填入 `Hanvert: Skip` 即可跳过该行（子字符串匹配，可与其他 Effect 共存）：

```
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,Hanvert: Skip,这段不会被转换
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,Karaoke; Hanvert: Skip,可与其他 Effect 共存
```

## 致谢

- [繁化姬 API](http://zhconvert.org/)
- [OpenCC](https://github.com/BYVoid/OpenCC)
