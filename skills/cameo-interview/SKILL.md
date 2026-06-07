# skill: cameo-interview

name: cameo-interview
version: "1.0"
description: >
  針對卡米爾提供的四份政府資料（偵查卷宗 PDF、廣播 WAV、人口統計 XLS、公文 ZIP）
  進行問答的技能包。使用向量搜尋（chromadb + sentence-transformers）注入最相關段落。

model: gemma-4-31B-it
api_base: https://portal.genai.nchc.org.tw/api/v1

system_prompt: |
  你是一個精確的政府資料分析助理。
  你只能根據提供的參考資料來回答問題，不能憑空推測。
  如果資料中找不到答案，請明確說明「資料中未提及」。
  請用繁體中文回答，回答要簡潔精確，並引用來源。

retrieval:
  engine: chromadb
  embedding_model: all-MiniLM-L6-v2  # chromadb DefaultEmbeddingFunction (ONNX)
  index_path: skills/cameo-interview/chroma_index
  chunk_size: 600
  overlap: 80
  top_k: 5
  fallback: fulltext

sources:
  - id: pdf
    path: skills/cameo-interview/references/pdf/
    description: 偵查卷宗掃描件（9頁，OCR 提取）
  - id: wav
    path: skills/cameo-interview/references/wav/
    description: 廣播音頻逐字稿（Whisper medium 轉錄，含時間戳）
  - id: xls
    path: skills/cameo-interview/references/xls/
    description: 縣市人口統計（25 縣市，12 年齡組別，xlrd 解析）
  - id: zip
    path: skills/cameo-interview/references/zip/
    description: 100 份政府公文（zipfile + PyMuPDF 萃取，附索引）

qa_pairs: skills/cameo-interview/qa/all_qa.json
