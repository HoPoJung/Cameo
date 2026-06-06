# Cameo 面試技能包

卡米爾 AI 專案經理面試實作題目。

## 快速開始

### Step 1：安裝依賴

```bash
pip install pdfplumber openai-whisper openpyxl pandas tabulate python-docx requests
```

### Step 2：上傳原始資料

把 Google Drive 的 4 個資料夾下載後放到：

```
data/
├── pdf/    ← 偵查卷宗 PDF
├── wav/    ← 廣播音頻 WAV
├── xls/    ← 人口統計 XLS
└── zip/    ← 公文 ZIP
```

### Step 3：前處理

```bash
python scripts/preprocess_pdf.py
python scripts/preprocess_wav.py   # 約 10-15 分鐘
python scripts/preprocess_xls.py
python scripts/preprocess_zip.py
```

### Step 4：自動出題 + 自驗

```bash
export NCHC_API_KEY=sk-9h2h5cqWFN0cptcDdixamg
python scripts/generate_qa.py
python scripts/ask.py --validate
```

### Step 5：互動問答

```bash
python scripts/ask.py "這份偵查卷宗涉及哪個案件？"
python scripts/ask.py "廣播中提到哪些地名？" --source wav
```

## 截止時間

- 6/7（日）中午 12:00：提交技能包 + 5 頁簡報
- 6/8（一）10:00：現場考試
- 6/8（一）11:00：簡報 + QA
