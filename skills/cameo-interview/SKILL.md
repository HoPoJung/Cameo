# 技能：卡米爾面試 — 政府資料問答

## 技能描述

針對卡米爾提供的政府領域資料（偵查卷宗、廣播音頻、人口統計、公文集），
以 Gemma 4 31B 模型透過 NCHC API 進行問答的技能包。

## 框架

**Harness：Hermes Agent**
API 端點：`https://portal.genai.nchc.org.tw/api/v1/chat/completions`
模型：`gemma-4-31B-it`

## 資料來源

| 資料夾 | 類型 | 描述 |
|--------|------|------|
| `references/pdf/` | PDF 卷宗 | 偵查卷宗，OCR 提取後按頁分段 |
| `references/wav/` | WAV 音頻 | 廣播音頻，Whisper 轉錄逐字稿 |
| `references/xls/` | XLS 統計 | 人口統計資料，結構化表格 + 摘要 |
| `references/zip/` | ZIP 公文 | 100 份公文，解壓縮 + 文字萃取 + 索引 |

## 問答規則

1. **只能根據 references/ 內的資料回答**，不能憑空推測
2. 若資料中找不到明確答案，回答「資料中未提及」
3. 回答要引用來源段落
4. 使用繁體中文回應

## System Prompt

```
你是一個精確的政府資料分析助理。
你只能根據提供的參考資料來回答問題，不能憑空推測。
如果資料中找不到答案，請明確說明「資料中未提及」。
請用繁體中文回答，回答要簡潔精確，並引用來源段落。
```

## 目錄結構

```
skills/cameo-interview/
├── SKILL.md              # 本文件
├── references/
│   ├── pdf/              # PDF 前處理輸出（.md 檔）
│   ├── wav/              # WAV 轉錄輸出（.md 檔）
│   ├── xls/              # XLS 結構化輸出（.md 檔）
│   └── zip/              # ZIP 解壓縮輸出（.md 檔）
└── qa/
    ├── pdf_qa.json       # PDF 的 5 題 QA
    ├── wav_qa.json       # WAV 的 5 題 QA
    ├── xls_qa.json       # XLS 的 5 題 QA
    ├── zip_qa.json       # ZIP 的 5 題 QA
    ├── all_qa.json       # 全部 20 題合併
    └── validation_results.json  # 驗證結果
```

## 使用方式

```bash
# 前處理（資料上傳後執行）
python scripts/preprocess_pdf.py data/pdf/
python scripts/preprocess_wav.py data/wav/
python scripts/preprocess_xls.py data/xls/
python scripts/preprocess_zip.py data/zip/

# 自動出題
python scripts/generate_qa.py

# 自驗 20 題
python scripts/ask.py --validate

# 單題問答
python scripts/ask.py "問題內容" --source pdf
python scripts/ask.py "問題內容" --source all
```
