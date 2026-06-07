from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from pathlib import Path
from typing import Literal

app = FastAPI(title="Hermes Agent — Cameo Interview")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Config ────────────────────────────────────────────────
NCHC_BASE_URL = os.environ.get("NCHC_BASE_URL", "https://portal.genai.nchc.org.tw/api/v1")
NCHC_API_KEY  = os.environ.get("NCHC_API_KEY", "")
MODEL         = os.environ.get("MODEL", "gemma-4-31B-it")
REFS_DIR      = Path(os.environ.get("REFS_DIR", "skills/cameo-interview/references"))

SYSTEM_PROMPT = """你是一個精確的政府資料分析助理。
你只能根據提供的參考資料來回答問題，不能憑空推測。
如果資料中找不到答案，請明確說明「資料中未提及」。
請用繁體中文回答，回答要簡潔精確，並引用來源。"""

# ── Reference loader ──────────────────────────────────────
def load_references(source: str = "all", max_chars: int = 12000) -> str:
    sources = ["pdf", "wav", "xls", "zip"] if source == "all" else [source]
    parts = []
    for src in sources:
        src_dir = REFS_DIR / src
        if not src_dir.exists():
            continue
        for f in sorted(src_dir.rglob("*.md")):
            content = f.read_text(encoding="utf-8")
            parts.append(f"=== 來源[{src.upper()}]：{f.name} ===\n{content}")
    combined = "\n\n".join(parts)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n...[資料截斷，已顯示前部分]"
    return combined

# ── Models ────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str
    source: Literal["all", "pdf", "wav", "xls", "zip"] = "all"
    max_tokens: int = 2048

class AskResponse(BaseModel):
    answer: str
    source_used: str
    model: str

# ── Routes ────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}

@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    if not NCHC_API_KEY:
        raise HTTPException(status_code=500, detail="NCHC_API_KEY not set")

    refs = load_references(req.source)
    if not refs:
        raise HTTPException(status_code=404, detail=f"No references found for source: {req.source}")

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"參考資料：\n\n{refs}\n\n---\n\n問題：{req.question}"},
        ],
        "max_tokens": req.max_tokens,
        "temperature": 0.1,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{NCHC_BASE_URL}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {NCHC_API_KEY}",
            },
            json=payload,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

    answer = resp.json()["choices"][0]["message"]["content"].strip()
    return AskResponse(answer=answer, source_used=req.source, model=MODEL)

@app.get("/sources")
def list_sources():
    result = {}
    for src in ["pdf", "wav", "xls", "zip"]:
        d = REFS_DIR / src
        result[src] = len(list(d.rglob("*.md"))) if d.exists() else 0
    return result
