"""
XLS 前處理：讀取所有工作表，轉成 Markdown 表格 + 統計摘要
用法：python scripts/preprocess_xls.py data/xls/
需要：pip install openpyxl pandas tabulate
"""
import sys
from pathlib import Path

try:
    import pandas as pd
    from tabulate import tabulate
except ImportError:
    print("請先執行：pip install openpyxl pandas tabulate")
    sys.exit(1)


def summarize_df(df: pd.DataFrame) -> str:
    lines = [f"- 總列數：{len(df)}", f"- 欄位：{', '.join(df.columns.astype(str))}"]
    for col in df.select_dtypes(include="number").columns:
        lines.append(
            f"- {col}：最小={df[col].min():.2f}, 最大={df[col].max():.2f}, "
            f"平均={df[col].mean():.2f}, 總和={df[col].sum():.2f}"
        )
    for col in df.select_dtypes(exclude="number").columns:
        top = df[col].value_counts().head(5)
        lines.append(f"- {col} 前5名：{dict(top)}")
    return "\n".join(lines)


def process_xls(xls_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (xls_path.stem + ".md")

    sheets = pd.read_excel(xls_path, sheet_name=None, dtype=str)
    sections = [f"# {xls_path.name}"]

    for sheet_name, df in sheets.items():
        df = df.dropna(how="all").fillna("")
        sections.append(f"\n## 工作表：{sheet_name}")
        sections.append(f"\n### 資料摘要\n\n{summarize_df(df.infer_objects())}")

        # Full table (cap at 500 rows to keep context manageable)
        if len(df) > 500:
            sections.append(f"\n### 完整資料（前 500 列，共 {len(df)} 列）\n")
            table_df = df.head(500)
        else:
            sections.append(f"\n### 完整資料（共 {len(df)} 列）\n")
            table_df = df

        sections.append(tabulate(table_df, headers="keys", tablefmt="pipe", showindex=False))

    content = "\n\n".join(sections)
    out_file.write_text(content, encoding="utf-8")
    print(f"✓ {xls_path.name} → {out_file} ({len(sheets)} 個工作表)")
    return out_file


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/xls")
    out = Path("skills/cameo-interview/references/xls")

    files = list(src.glob("*.xls")) + list(src.glob("*.xlsx")) + list(src.glob("*.csv"))
    if not files:
        print(f"找不到試算表檔案：{src}")
        sys.exit(1)

    for f in files:
        process_xls(f, out)

    print(f"\n完成。輸出位置：{out}/")


if __name__ == "__main__":
    main()
