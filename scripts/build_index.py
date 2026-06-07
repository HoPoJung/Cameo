"""
建立向量搜尋索引
用法：python scripts/build_index.py
需要：pip install chromadb sentence-transformers
"""
import sys
from pathlib import Path

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    print("請先執行：pip install chromadb sentence-transformers")
    sys.exit(1)

REFS_DIR   = Path("skills/cameo-interview/references")
INDEX_DIR  = Path("skills/cameo-interview/chroma_index")
CHUNK_SIZE = 600   # 每段約 600 字
OVERLAP    = 80    # 前後重疊，避免語意切斷

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i:i + size])
        i += size - overlap
    return [c for c in chunks if len(c.strip()) > 30]


def build():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(INDEX_DIR))

    # 每次重建前清空
    for col_name in ["pdf", "wav", "xls", "zip"]:
        try:
            client.delete_collection(col_name)
        except Exception:
            pass

    total = 0
    for source in ["pdf", "wav", "xls", "zip"]:
        src_dir = REFS_DIR / source
        if not src_dir.exists():
            print(f"  跳過 {source}：找不到 {src_dir}")
            continue

        col = client.create_collection(name=source, embedding_function=ef)
        docs, ids, metas = [], [], []

        for f in sorted(src_dir.rglob("*.md")):
            content = f.read_text(encoding="utf-8")
            for ci, chunk in enumerate(chunk_text(content)):
                docs.append(chunk)
                ids.append(f"{f.stem}__chunk{ci:04d}")
                metas.append({"source": source, "file": f.name, "chunk": ci})

        if docs:
            col.add(documents=docs, ids=ids, metadatas=metas)
            print(f"  ✓ {source}: {len(docs)} 個 chunks")
            total += len(docs)

    print(f"\n索引建立完成，共 {total} 個 chunks → {INDEX_DIR}/")


if __name__ == "__main__":
    build()
