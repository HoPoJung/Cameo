"""
ZIP 前處理：解壓縮，萃取各類文件文字，建立索引
用法：python scripts/preprocess_zip.py data/zip/
需要：pip install pdfplumber python-docx openpyxl pandas tabulate
"""
import sys
import zipfile
import shutil
from pathlib import Path

try:
    import fitz  # pymupdf
    import docx
    import pandas as pd
    from tabulate import tabulate
except ImportError:
    print("請先執行：pip install pymupdf python-docx openpyxl pandas tabulate")
    sys.exit(1)


def extract_text_from_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    try:
        if suffix == ".pdf":
            doc = fitz.open(str(file_path))
            text = "\n\n".join(page.get_text() for page in doc).strip()
            doc.close()
            return text
        elif suffix in (".docx", ".doc"):
            doc = docx.Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs).strip()
        elif suffix in (".txt", ".md", ".csv"):
            return file_path.read_text(encoding="utf-8", errors="replace").strip()
        elif suffix in (".xls", ".xlsx"):
            dfs = pd.read_excel(file_path, sheet_name=None, dtype=str)
            parts = []
            for name, df in dfs.items():
                df = df.dropna(how="all").fillna("")
                parts.append(f"### 工作表：{name}\n{tabulate(df.head(200), headers='keys', tablefmt='pipe', showindex=False)}")
            return "\n\n".join(parts)
        else:
            return f"[不支援的格式：{suffix}]"
    except Exception as e:
        return f"[讀取失敗：{e}]"


def process_zip(zip_path: Path, out_dir: Path):
    doc_out = out_dir / zip_path.stem
    doc_out.mkdir(parents=True, exist_ok=True)

    extract_dir = Path(f"/tmp/cameo_zip_{zip_path.stem}")
    if extract_dir.exists():
        shutil.rmtree(extract_dir)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    all_files = sorted(extract_dir.rglob("*"))
    docs = [f for f in all_files if f.is_file()]

    index_lines = [f"# {zip_path.name} — 文件索引", f"\n共 {len(docs)} 份文件\n"]
    for i, doc in enumerate(docs, 1):
        rel = doc.relative_to(extract_dir)
        index_lines.append(f"{i:03d}. `{rel}` ({doc.stat().st_size:,} bytes)")

    index_file = out_dir / f"{zip_path.stem}_index.md"
    index_file.write_text("\n".join(index_lines), encoding="utf-8")
    print(f"✓ 索引：{index_file} ({len(docs)} 份文件)")

    for doc in docs:
        rel = doc.relative_to(extract_dir)
        out_md = doc_out / (str(rel).replace("/", "_").replace("\\", "_") + ".md")
        text = extract_text_from_file(doc)
        header = f"# {rel}\n\n"
        out_md.write_text(header + text, encoding="utf-8")

    print(f"✓ 文件內容：{doc_out}/")
    shutil.rmtree(extract_dir, ignore_errors=True)


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/zip")
    out = Path("skills/cameo-interview/references/zip")

    zips = list(src.glob("*.zip"))
    if not zips:
        print(f"找不到 ZIP 檔案：{src}")
        sys.exit(1)

    for z in zips:
        process_zip(z, out)

    print(f"\n完成。輸出位置：{out}/")


if __name__ == "__main__":
    main()
