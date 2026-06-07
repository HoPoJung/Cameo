"""
對 Railway 部署的 Hermes Agent 跑 20 題自驗
用法：python scripts/validate_railway.py [--url https://xxx.railway.app]
"""
import sys
import json
import time
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("請先執行：pip install requests")
    sys.exit(1)

QA_FILE      = Path("skills/cameo-interview/qa/all_qa.json")
DEFAULT_URL  = "https://cameo-production.up.railway.app"
SLEEP_SECS   = 3   # 避免 429 Too Many Requests


def kw_match(keyword: str, answer: str) -> bool:
    """關鍵字比對，忽略空格差異（例如「12萬」vs「12 萬」）。"""
    kw_norm  = keyword.lower().replace(" ", "").replace(" ", "")
    ans_norm = answer.lower().replace(" ", "").replace(" ", "")
    return kw_norm in ans_norm


def run(base_url: str):
    qa_pairs = json.loads(QA_FILE.read_text(encoding="utf-8"))
    passed, failed, skipped = [], [], []

    print(f"目標：{base_url}/ask")
    print(f"題數：{len(qa_pairs)} 題  |  間隔：{SLEEP_SECS}s\n")
    print("=" * 70)

    for i, item in enumerate(qa_pairs):
        qid = item["id"]
        src = item["source"]
        q   = item["question"]
        kw  = item.get("expected_keyword", "")

        if item.get("status") == "pending_transcription":
            print(f"[SKIP] {qid} | {q[:50]}...")
            skipped.append(qid)
            continue

        if i > 0:
            time.sleep(SLEEP_SECS)

        print(f"[{qid}] {q[:55]}...")

        try:
            resp = requests.post(
                f"{base_url}/ask",
                json={"question": q, "source": src},
                timeout=90,
            )
            resp.raise_for_status()
            data   = resp.json()
            answer = data.get("answer", "")
            method = data.get("retrieval", "?")
        except Exception as e:
            print(f"  ✗ 請求失敗：{e}\n")
            failed.append({"id": qid, "reason": str(e)})
            continue

        ok   = kw_match(kw, answer) if kw and kw != "待補充" else True
        mark = "✓" if ok else "✗"
        print(f"  {mark} [{method}] 關鍵字「{kw}」{'找到' if ok else '未找到'}")
        print(f"    答案節錄：{answer[:120]}...")
        print()

        entry = {**item, "actual_answer": answer, "retrieval": method, "passed": ok}
        (passed if ok else failed).append(entry)

    print("=" * 70)
    total = len(passed) + len(failed)
    print(f"結果：{len(passed)}/{total} 通過  |  跳過 {len(skipped)} 題")

    if failed:
        print("\n失敗題目：")
        for f in failed:
            fid = f.get("id") or f.get("reason", "?")
            print(f"  ✗ {fid}")

    out = Path("skills/cameo-interview/qa/railway_validation.json")
    out.write_text(
        json.dumps(passed + failed, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n詳細結果已存至：{out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    args = parser.parse_args()
    run(args.url.rstrip("/"))
