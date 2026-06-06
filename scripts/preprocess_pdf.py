"""
PDF 前處理：提取文字，按頁分段，存成 references/pdf/
用法：python scripts/preprocess_pdf.py data/pdf/
"""
import sys
import re
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("請先執行：pip install pdfplumber")
    sys.exit(1)


def clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def process_pdf(pdf_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (pdf_path.stem + ".md")

    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"## 第 {i} 頁\n\n{clean_text(text)}")

    content = f"# {pdf_path.name}\n\n" + "\n\n---\n\n".join(pages)
    out_file.write_text(content, encoding="utf-8")
    print(f"✓ {pdf_path.name} → {out_file} ({len(pages)} 頁)")
    return out_file


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/pdf")
    out = Path("skills/cameo-interview/references/pdf")

    pdfs = list(src.glob("*.pdf"))
    if not pdfs:
        print(f"找不到 PDF 檔案：{src}")
        sys.exit(1)

    for p in pdfs:
        process_pdf(p, out)

    print(f"\n完成。輸出位置：{out}/")


if __name__ == "__main__":
    main()
