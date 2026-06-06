"""
自動出題腳本：讀取 references，用大模型（可換成 Claude）自動出 5 題 + 答案
用法：python scripts/generate_qa.py [--source pdf|wav|xls|zip|all]
出題完成後會寫入 skills/cameo-interview/qa/all_qa.json
之後用 ask.py --validate 跑驗證
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


def load_source_content(source: str) -> str:
    src_dir = REFS_DIR / source
    if not src_dir.exists():
        return ""
    parts = []
    for f in sorted(src_dir.rglob("*.md")):
        parts.append(f.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def generate_qa_for_source(source: str) -> list[dict]:
    content = load_source_content(source)
    if not content:
        print(f"  跳過 {source}：找不到 references")
        return []

    # 截取前 8000 字避免 token 超限
    truncated = content[:8000] + ("..." if len(content) > 8000 else "")

    prompt = f"""以下是一份資料（來源類型：{source.upper()}）：

{truncated}

---

請根據上方資料，出 5 個具體且有明確答案的問題，並提供每題的標準答案與關鍵字。

請用以下 JSON 格式回覆（只回傳 JSON，不要其他文字）：
[
  {{
    "question": "問題內容",
    "answer": "完整答案",
    "expected_keyword": "驗證用關鍵字（答案中必須包含的詞）"
  }},
  ...
]"""

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
        "temperature": 0.3,
    }

    resp = requests.post(
        API_URL,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"].strip()

    # 去掉可能的 markdown code block
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    items = json.loads(raw)
    for item in items:
        item["source"] = source
    return items


def main():
    parser = argparse.ArgumentParser(description="自動出題")
    parser.add_argument("--source", default="all", choices=["pdf", "wav", "xls", "zip", "all"])
    args = parser.parse_args()

    QA_DIR.mkdir(parents=True, exist_ok=True)
    sources = ["pdf", "wav", "xls", "zip"] if args.source == "all" else [args.source]

    all_qa = []
    for src in sources:
        print(f"正在為 {src.upper()} 出題...")
        items = generate_qa_for_source(src)
        all_qa.extend(items)
        print(f"  ✓ 產生 {len(items)} 題")

        src_file = QA_DIR / f"{src}_qa.json"
        src_file.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    out_file = QA_DIR / "all_qa.json"
    out_file.write_text(json.dumps(all_qa, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n完成！共 {len(all_qa)} 題，儲存於 {out_file}")
    print("下一步：python scripts/ask.py --validate")


if __name__ == "__main__":
    main()
