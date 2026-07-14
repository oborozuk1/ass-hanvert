# ass-hanvert

简易 ASS 字幕简繁体转换工具

## 关于

### 动机

目前主流的繁转换工具（如繁化姬）虽然转换精度尚可，且能检测字幕格式进行智能转换，但在处理带有标签的字幕时会出错。例如，`苹{\k}果` 会被错误地转换为 `苹{\k}果`，而正确的结果应该是 `蘋{\k}果`。

而 OpenCC 则不支持识别字幕格式，容易造成不必要的转换（如转换到字体名称或日语文字等问题）。

本项目旨在通过 Python 实现 ASS 字幕转换，支持多种转换器，以解决上述问题。

### 功能特性

1. 跳过日文字幕（通过样式名识别，暂不支持 `\r`）
2. 跳过非中文文本
3. 转换时忽略标签和换行符，转换完成后恢复原始格式
4. 转换前后长度发生变化时显示警告
5. 内置多种转换器（见下方列表）
6. 转换结果缓存，减少重复工作

## 安装

```bash
pip install ass-hanvert
```

## 使用方法

### 命令行（CLI）

```bash
# 基本用法 - 转换单个文件（默认：简转繁，繁化姬-台湾）
ass-hanvert input.ass

# 指定转换器
ass-hanvert -c OpenCC-TW input.ass

# 繁转简转换
ass-hanvert -c OpenCC-S input.ass

# 批量处理多个文件
ass-hanvert input1.ass input2.ass

# 使用缓存目录（省去重复转换）
ass-hanvert --cache ./cache input.ass

# 自定义输出文件后缀
ass-hanvert --suffix traditional input.ass

# 完整示例：指定转换器、参考转换器、字体名称映射及缓存
ass-hanvert -c FHJ-TW --ref-converter OpenCC-S --font-mapping fonts.json --cache ./cache input.ass
```

参数说明：

| 参数 | 说明                        | 默认值 |
|------|---------------------------|--------|
| `files` | 要转换的 ASS 字幕文件（支持多个文件和通配符） | 必填 |
| `-c, --converter` | 转换器名称，见下方列表               | FHJ-TW |
| `--ref-converter` | 参考转换器，若省略则根据主转换器方向自动选择    | 自动 |
| `--suffix` | 输出文件后缀，插入在 `.ass` 之前      | `cht`（简转繁）/ `chs`（繁转简） |
| `--cache` | 缓存目录路径                    | 无 |
| `--no-skip-comment` | 转换时不跳过注释行                 | 跳过 |
| `--no-deduplicate` | 转换时不去重                    | 去重 |
| `--no-sort` | 转换时不对事件排序                 | 按开始时间排序 |
| `--font-mapping` | 字体名称映射 JSON 文件路径          | 无 |
| `--pre-replace` | 前置替换列表 JSON 文件路径          | 无 |
| `--post-replace` | 后置替换列表 JSON 文件路径          | 无 |
| `--protected-patterns` | 保护模式 JSON 文件路径（正则表达式列表）   | 无 |

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
convert_ass(doc, converter=OpenCCConverter.Simplified)

# 保存
doc.save("output.cht.ass")
```

## 致谢

- [繁化姬 API](http://zhconvert.org/)
- [OpenCC](https://github.com/BYVoid/OpenCC)
