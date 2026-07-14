# ass-hanvert

簡易 ASS 字幕簡繁體轉換工具

## 關於

### 動機

目前主流的繁轉換工具（如繁化姬）雖然轉換精度尚可，且能偵測字幕格式進行智慧轉換，但在處理帶有標籤的字幕時會出錯。例如，`苹{\k}果` 會被錯誤地轉換為 `苹{\k}果`，而正確的結果應該是 `蘋{\k}果`。

而 OpenCC 則不支援識別字幕格式，容易造成不必要的轉換（如轉換到字型名稱或日語文字等問題）。

本專案旨在透過 Python 實現 ASS 字幕轉換，支援多種轉換器，以解決上述問題。

### 功能特性

1. 跳過日文字幕（透過樣式名稱識別，可自訂）
2. 跳過非中文文字
3. 轉換時忽略標籤和換行符號，轉換完成後恢復原始格式
4. 轉換前後長度發生變化時顯示警告
5. 內建多種轉換器（見下方列表）
6. 轉換結果快取，減少重複工作
7. 支援透過 Effect 欄位標記跳過特定行

## 安裝

```bash
pip install ass-hanvert
pip install "ass-hanvert[openai]"  # 如果希望使用 OpenAIConverter
```

## 使用方法

### 命令列（CLI）

```bash
# 基本用法 - 轉換單一/多個檔案（預設：簡轉繁，繁化姬-台灣）
ass-hanvert input1.ass input2.ass

# 轉換整個目錄下的所有 .ass 檔案，輸出到指定目錄
ass-hanvert --output-dir ./output ./subtitles/

# 指定轉換器
ass-hanvert -c OpenCC-TW input.ass

# 使用快取目錄（省去重複轉換）
ass-hanvert --cache ./cache input.ass

# 自訂輸出檔案後綴
ass-hanvert --suffix traditional input.ass

# 完整範例：指定轉換器、參考轉換器、字型名稱映射及快取
ass-hanvert -c FHJ-TW --ref-converter OpenCC-T --font-mapping fonts.json --cache ./cache input.ass
```

參數說明：

| 參數 | 說明                         | 預設值 |
|------|----------------------------|--------|
| `files` | 要轉換的 ASS 字幕檔案、目錄或萬用字元模式（支援多個） | 必填 |
| `-c, --converter` | 轉換器名稱，見下方列表                | FHJ-TW |
| `--ref-converter` | 參考轉換器，若省略則根據主轉換器方向自動選擇     | 自動 |
| `--suffix` | 輸出檔案後綴，插入在 `.ass` 之前       | `cht`（簡轉繁）/ `chs`（繁轉簡） |
| `--output-dir` | 輸出目錄，不指定則輸出到各源檔案旁     | 源檔案旁 |
| `--cache` | 快取目錄路徑                     | 無 |
| `--no-skip-comment` | 轉換時不跳過註解行                 | 跳過 |
| `--no-deduplicate` | 轉換時不去重                       | 去重 |
| `--no-sort` | 轉換時不對事件排序                    | 依開始時間排序 |
| `--font-mapping` | 字型名稱映射 JSON 檔案路徑           | 無 |
| `--pre-replace` | 前置替換列表 JSON 檔案路徑          | 無 |
| `--post-replace` | 後置替換列表 JSON 檔案路徑          | 無 |
| `--protected-patterns` | 保護模式 JSON 檔案路徑（正則表達式列表）   | 無 |
| `--skip-styles` | 跳過的樣式名子字串（逗號分隔）       | `JP,JA` |
| `--skip-styles-exact` | 跳過的精確樣式名（逗號分隔）          | 無 |
| `--no-skip-inline-styles` | 不跳過行內覆蓋樣式（`\r` 標籤切換的樣式） | 跳過 |

內建轉換器：

**簡轉繁：**

| 名稱 | 說明 |
|------|------|
| FHJ-T | 繁化姬 - 繁體 |
| FHJ-HK | 繁化姬 - 香港 |
| FHJ-TW | 繁化姬 - 台灣 |
| FHJ-WT | 繁化姬 - 維基繁體 |
| OpenCC-T | OpenCC - 繁體 |
| OpenCC-HK | OpenCC - 香港 |
| OpenCC-TW | OpenCC - 台灣 |
| OpenCC-TWP | OpenCC - 台灣（含台灣常用語） |

**繁轉簡：**

| 名稱 | 說明 |
|------|------|
| FHJ-S | 繁化姬 - 簡體 |
| FHJ-CH | 繁化姬 - 大陸 |
| FHJ-WS | 繁化姬 - 維基簡體 |
| OpenCC-S | OpenCC - 簡體 |
| OpenCC-HKS | OpenCC - 香港轉簡體 |
| OpenCC-TWS | OpenCC - 台灣轉簡體 |

### Python API

```python
from light_ass import Document
from ass_hanvert import convert_ass

# 載入字幕
doc = Document.load("input.ass")

# 轉換（預設：繁化姬台灣）
convert_ass(doc)

# 或指定轉換器（簡轉繁）
from ass_hanvert import OpenCCConverter

stats = convert_ass(doc, converter=OpenCCConverter.Taiwan)
print(stats)

# 繁轉簡
convert_ass(doc, converter=OpenCCConverter.Simplified)

# 儲存
doc.save("output.cht.ass")
```

#### 跳過特定行

可透過以下方式自訂跳過哪些行：

**樣式名稱**

預設跳過樣式名稱包含 `JP` 或 `JA` 的行。可透過 `skip_styles` 自訂，也可用 `skip_styles_exact` 做精確匹配：

```python
# 自訂子字串匹配
convert_ass(doc, skip_styles=("JP", "JA", "EN"))

# 僅精確匹配樣式名稱（不做子字串匹配）
convert_ass(doc, skip_styles=(), skip_styles_exact=("JP", "JA"))

# 兩者可同時使用
convert_ass(doc, skip_styles=("JP",), skip_styles_exact=("EN-Lit",))
```

**Effect 欄位標記**

在 ASS 檔案中給行的 Effect 欄位填入 `Hanvert: Skip` 即可跳過該行（子字串匹配，可與其他 Effect 共存）：

```
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,Hanvert: Skip,這段不會被轉換
Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,Karaoke; Hanvert: Skip,可與其他 Effect 共存
```

## 致謝

- [繁化姬 API](http://zhconvert.org/)
- [OpenCC](https://github.com/BYVoid/OpenCC)
