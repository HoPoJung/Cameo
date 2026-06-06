"""
技能包問答腳本 — 搭配 NCHC Gemma 4 31B
用法：
  python scripts/ask.py "你的問題" [--source pdf|wav|xls|zip|all]
  python scripts/ask.py --validate          # 跑 20 題自驗
環境變數：
  NCHC_API_KEY=sk-...  （或直接在下方設定 API_KEY）
"""
import sys
import os
import json
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("請先執行：pip install requests")
    sys.exit(1)

API_URL = "https://portal.genai.nchc.org.tw/api/v1/chat/completions"
API_KEY = os.environ.get("NCHC_API_KEY", "sk-9h2h5cqWFN0cptcDdixamg")
MODEL = "gemma-4-31B-it"
REFS_DIR = Path("skills/cameo-interview/references")
QA_DIR = Path("skills/cameo-interview/qa")


def load_references(source: str = "all") -> str:
    sources = ["pdf", "wav", "xls", "zip"] if source == "all" else [source]
    parts = []
    for src in sources:
        src_dir = REFS_DIR / src
        if not src_dir.exists():
            continue
        files = sorted(src_dir.rglob("*.md"))
        for f in files:
            content = f.read_text(encoding="utf-8")
            parts.append(f"=== 來源：{f.relative_to(REFS_DIR)} ===\n{content}")
    return "\n\n".join(parts)


def ask(question: str, source: str = "all") -> str:
    refs = load_references(source)
    if not refs:
        return "錯誤：找不到任何參考資料。請先執行前處理腳本。"

    system_prompt = """你是一個精確的資料分析助理。
你只能根據提供的參考資料來回答問題，不能憑空推測。
如果資料中找不到答案，請明確說明「資料中未提及」。
請用繁體中文回答，回答要簡潔精確，並引用來源段落。"""

    user_prompt = f"""以下是參考資料：

{refs}

---

問題：{question}"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
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
        print(f"找不到 QA 檔案：{qa_file}，請先執行 generate_qa.py")
        sys.exit(1)

    qa_pairs = json.loads(qa_file.read_text(encoding="utf-8"))
    results = []
    passed = 0

    print(f"開始驗證 {len(qa_pairs)} 題...\n")
    for i, item in enumerate(qa_pairs, 1):
        print(f"[{i:02d}/{len(qa_pairs)}] {item['source'].upper()} | Q: {item['question'][:60]}...")
        answer = ask(item["question"], source=item["source"])
        ok = item.get("expected_keyword", "").lower() in answer.lower() if item.get("expected_keyword") else True
        status = "✓" if ok else "✗"
        if ok:
            passed += 1
        print(f"  {status} A: {answer[:120]}...\n")
        results.append({**item, "actual_answer": answer, "passed": ok})

    print(f"\n結果：{passed}/{len(qa_pairs)} 通過")
    results_file = QA_DIR / "validation_results.json"
    results_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"詳細結果儲存於：{results_file}")


def main():
    parser = argparse.ArgumentParser(description="Cameo 技能包問答")
    parser.add_argument("question", nargs="?", help="問題內容")
    parser.add_argument("--source", default="all", choices=["pdf", "wav", "xls", "zip", "all"])
    parser.add_argument("--validate", action="store_true", help="執行 20 題自驗")
    args = parser.parse_args()

    if args.validate:
        validate()
    elif args.question:
        print(ask(args.question, source=args.source))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
