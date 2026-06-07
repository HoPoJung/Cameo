"""
技能包問答腳本（向量搜尋版）— 搭配 NCHC Gemma 4 31B
用法：
  python scripts/ask.py "你的問題" [--source pdf|wav|xls|zip|all]
  python scripts/ask.py --validate
環境變數：NCHC_API_KEY=sk-...
"""
import sys
import os
import json
import argparse
from pathlib import Path

try:
    import requests
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("請先執行：pip install requests chromadb sentence-transformers")
    sys.exit(1)

API_URL  = "https://portal.genai.nchc.org.tw/api/v1/chat/completions"
API_KEY  = os.environ.get("NCHC_API_KEY", "sk-9h2h5cqWFN0cptcDdixamg")
MODEL    = "gemma-4-31B-it"
IDX_DIR  = Path("skills/cameo-interview/chroma_index")
QA_DIR   = Path("skills/cameo-interview/qa")
TOP_K    = 5   # 每個 source 取最相關的 5 段

SYSTEM_PROMPT = """你是一個精確的政府資料分析助理。
你只能根據提供的參考資料來回答問題，不能憑空推測。
如果資料中找不到答案，請明確說明「資料中未提及」。
請用繁體中文回答，回答要簡潔精確，並引用來源。"""

ef = embedding_functions.DefaultEmbeddingFunction()   # all-MiniLM-L6-v2 ONNX


def get_client() -> chromadb.PersistentClient:
    if not IDX_DIR.exists():
        print("找不到向量索引，請先執行：python scripts/build_index.py")
        sys.exit(1)
    return chromadb.PersistentClient(path=str(IDX_DIR))


def vector_search(question: str, source: str = "all") -> str:
    """向量搜尋：只注入最相關的段落，不塞全文。"""
    client   = get_client()
    sources  = ["pdf", "wav", "xls", "zip"] if source == "all" else [source]
    snippets = []

    for src in sources:
        try:
            col     = client.get_collection(name=src, embedding_function=ef)
            results = col.query(query_texts=[question], n_results=TOP_K)
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                snippets.append(f"[{src.upper()}｜{meta['file']}]\n{doc}")
        except Exception:
            pass  # source 不存在時略過

    if not snippets:
        return ""
    return "\n\n---\n\n".join(snippets)


def ask(question: str, source: str = "all") -> str:
    context = vector_search(question, source)
    if not context:
        return "錯誤：找不到相關參考資料。請先執行 build_index.py。"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"參考資料：\n\n{context}\n\n---\n\n問題：{question}"},
        ],
        "max_tokens": 2048,
        "temperature": 0.1,
    }
    resp = requests.post(
        API_URL,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def validate():
    qa_file = QA_DIR / "all_qa.json"
    if not qa_file.exists():
        print(f"找不到 {qa_file}")
        sys.exit(1)

    qa_pairs = json.loads(qa_file.read_text(encoding="utf-8"))
    passed   = 0
    results  = []

    print(f"開始自驗 {len(qa_pairs)} 題（向量搜尋版）...\n")
    for i, item in enumerate(qa_pairs, 1):
        status_flag = item.get("status", "")
        if status_flag == "pending_transcription":
            print(f"[{i:02d}/{len(qa_pairs)}] 跳過（WAV 待轉錄）\n")
            continue

        print(f"[{i:02d}/{len(qa_pairs)}] {item['source'].upper()} | {item['question'][:55]}...")
        answer = ask(item["question"], source=item["source"])
        kw     = item.get("expected_keyword", "")
        ok     = kw.lower() in answer.lower() if kw and kw != "待補充" else True
        if ok:
            passed += 1
        print(f"  {'✓' if ok else '✗'} {answer[:100]}...\n")
        results.append({**item, "actual_answer": answer, "passed": ok})

    print(f"結果：{passed}/{len([r for r in results])} 通過")
    out = QA_DIR / "validation_results.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"詳細結果：{out}")


def main():
    parser = argparse.ArgumentParser(description="Cameo 技能包問答（向量搜尋版）")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--source", default="all",
                        choices=["pdf", "wav", "xls", "zip", "all"])
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if args.validate:
        validate()
    elif args.question:
        print(ask(args.question, source=args.source))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
