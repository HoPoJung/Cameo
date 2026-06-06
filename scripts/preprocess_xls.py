"""
XLS 前處理（修訂版）：正確解析人口統計複合表頭
結構：列0-1=空, 列2=大標, 列3=小標, 列4+=資料
每個縣市佔3列(計/男/女), 欄位為各年齡組
"""
import sys
from pathlib import Path
import xlrd

REFS_DIR = Path("skills/cameo-interview/references/xls")
AGE_GROUPS = [
    "總計", "0-4歲", "0歲", "1歲", "2歲", "3歲", "4歲",
    "5-9歲", "5歲", "6歲", "7歲", "8歲", "9歲",
    "10-14歲", "10歲", "11歲", "12歲", "13歲", "14歲",
    "15-19歲", "15歲", "16歲", "17歲", "18歲", "19歲",
    "20-24歲", "20歲", "21歲", "22歲", "23歲", "24歲",
    "25-29歲", "25歲", "26歲", "27歲", "28歲", "29歲",
    "30-34歲", "30歲", "31歲", "32歲", "33歲", "34歲",
    "35-39歲", "35歲", "36歲", "37歲", "38歲", "39歲",
    "40-44歲", "40歲", "41歲", "42歲", "43歲", "44歲",
    "45-49歲", "45歲", "46歲", "47歲", "48歲", "49歲",
    "50-54歲", "50歲", "51歲", "52歲", "53歲", "54歲",
    "55-59歲", "55歲", "56歲", "57歲", "58歲", "59歲",
    "60-64歲", "60歲", "61歲", "62歲", "63歲", "64歲",
    "65-69歲", "65歲", "66歲", "67歲", "68歲", "69歲",
    "70-74歲", "70歲", "71歲", "72歲", "73歲", "74歲",
    "75-79歲", "75歲", "76歲", "77歲", "78歲", "79歲",
    "80-84歲", "80歲", "81歲", "82歲", "83歲", "84歲",
    "85-89歲", "85歲", "86歲", "87歲", "88歲", "89歲",
    "90-94歲", "90歲", "91歲", "92歲", "93歲", "94歲",
    "95-99歲", "95歲", "96歲", "97歲", "98歲", "99歲",
    "100歲以上",
]


def parse_sheet(ws) -> list[dict]:
    """Parse one sheet into list of {region, gender, age_group: value}."""
    # Find data start row (first row where col0 or col1 = '計')
    data_start = 4
    records = []
    current_region = ""

    for r in range(data_start, ws.nrows):
        col0 = str(ws.cell_value(r, 0)).strip().replace("　", "").replace(" ", "")
        col1 = str(ws.cell_value(r, 1)).strip()

        if col0:
            current_region = col0
        if col1 not in ("計", "男", "女"):
            continue

        gender = col1
        # Build record with all age columns (col2 = 總計, col3+ = age groups)
        row_data = {"地區": current_region, "性別": gender}
        col_names = ["總計"] + AGE_GROUPS[1:ws.ncols - 2]
        for c in range(2, ws.ncols):
            if c - 2 < len(col_names):
                val = ws.cell_value(r, c)
                try:
                    row_data[col_names[c - 2]] = int(float(val)) if val != "" else 0
                except (ValueError, TypeError):
                    row_data[col_names[c - 2]] = str(val)
        records.append(row_data)
    return records


def fmt_int(v) -> str:
    try:
        return f"{int(v):,}"
    except (ValueError, TypeError):
        return str(v)


def process_xls(xls_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (xls_path.stem + ".md")
    wb = xlrd.open_workbook(str(xls_path))

    all_sections = [f"# {xls_path.name}\n\n資料來源：內政部統計月報 中華民國114年1月\n"]

    # Sheet 01 = 總表，後面的工作表是各縣市細項
    for sheet_idx, sheet_name in enumerate(wb.sheet_names()):
        ws = wb.sheet_by_name(sheet_name)
        records = parse_sheet(ws)
        if not records:
            continue

        section = [f"\n## 工作表 {sheet_name}（共 {len(records)} 筆記錄）\n"]

        # Summary table: 總計 by region and gender
        section.append("### 各地區總人口數\n")
        section.append("| 地區 | 性別 | 總計 | 0-4歲 | 15-64歲概估 | 65歲以上概估 |")
        section.append("|------|------|------|-------|-------------|-------------|")
        for rec in records:
            region = rec.get("地區", "")
            gender = rec.get("性別", "")
            total = fmt_int(rec.get("總計", 0))
            age04 = fmt_int(rec.get("0-4歲", 0))
            # Estimate working age (15-64) from groups
            working = sum(
                rec.get(f"{a0}-{a0+4}歲", 0)
                for a0 in range(15, 65, 5)
                if isinstance(rec.get(f"{a0}-{a0+4}歲", 0), int)
            )
            elderly = sum(
                rec.get(f"{a0}-{a0+4}歲", 0)
                for a0 in range(65, 100, 5)
                if isinstance(rec.get(f"{a0}-{a0+4}歲", 0), int)
            ) + rec.get("100歲以上", 0)
            section.append(
                f"| {region} | {gender} | {total} | {age04} | {fmt_int(working)} | {fmt_int(elderly)} |"
            )

        # Detailed age breakdown for first 3 regions only (to keep context manageable)
        section.append(f"\n### 年齡詳細分佈（前幾個主要地區）\n")
        age_keys = ["總計", "0-4歲", "5-9歲", "10-14歲", "15-19歲", "20-24歲",
                    "25-29歲", "30-34歲", "35-39歲", "40-44歲", "45-49歲",
                    "50-54歲", "55-59歲", "60-64歲", "65-69歲", "70-74歲",
                    "75-79歲", "80-84歲", "85-89歲", "90-94歲", "95-99歲", "100歲以上"]
        header = "| 地區 | 性別 | " + " | ".join(age_keys) + " |"
        separator = "|------|------|" + "|".join(["------"] * len(age_keys)) + "|"
        section.append(header)
        section.append(separator)

        # Show 計 rows only for main regions to keep size manageable
        shown = 0
        for rec in records:
            if rec.get("性別") == "計":
                vals = " | ".join(fmt_int(rec.get(k, 0)) for k in age_keys)
                section.append(f"| {rec.get('地區','')} | 計 | {vals} |")
                shown += 1
            if shown >= 25:  # cap at 25 regions per sheet
                break

        all_sections.append("\n".join(section))
        print(f"  ✓ 工作表 {sheet_name}: {len(records)} 筆")

    out_file.write_text("\n".join(all_sections), encoding="utf-8")
    print(f"\n✓ 輸出：{out_file}")


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("raw/xls")
    files = list(src.glob("*.xls")) + list(src.glob("*.xlsx"))
    if not files:
        print(f"找不到檔案：{src}")
        sys.exit(1)
    for f in files:
        process_xls(f, REFS_DIR)


if __name__ == "__main__":
    main()
