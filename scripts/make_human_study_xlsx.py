"""Write one Excel workbook per participant for the forced-choice human validation (as sent in November 2026).

Each workbook has an instructions tab (consent text in Uzbek, Latin and Cyrillic script; instructions in
Uzbek, both scripts, and in English; optional questions about the participant, with the participant's
code filled in) and the 320 pairs of human_study/forced_choice_latn.csv and forced_choice_cyrl.csv in a
Latin and a Cyrillic tab, with A/B and x dropdowns in the answer and unsure columns. The participant fills
in one of the two tabs. The texts of the instructions tab are in human_study/workbook_instructions.json.
Requires openpyxl.

    python scripts/make_human_study_xlsx.py p06 p07 p08 p09 p10 --out human_study_sheets
"""
import argparse
import csv
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT / "human_study"
HEAD = PatternFill("solid", fgColor="E6EBF2")
FILL = PatternFill("solid", fgColor="FFFAE0")


def workbook(code, instr, items):
    wb = Workbook()
    ws = wb.active
    ws.title = "Koʻrsatma"
    for row in instr:
        ws.append(row)
    ws["B10"] = code
    ws.column_dimensions["A"].width = 46
    ws.column_dimensions["B"].width = 95
    for row in ws.iter_rows(min_row=1, max_row=len(instr), max_col=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for r in range(1, len(instr) + 1):
        ws.cell(r, 1).font = Font(bold=True)
    ws["A1"].font = Font(bold=True, size=14)
    for r in range(10, 15):
        ws.cell(r, 2).fill = FILL
    for cell, options in (("B11", "18–24,25–34,35–44,45–54,55+"), ("B12", "Ha / Yes,Yoʻq / No"), ("B14", "Lotin,Кирилл")):
        dv = DataValidation(type="list", formula1=f'"{options}"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(cell)
    for tag, title in (("latn", "Lotin"), ("cyrl", "Кирилл")):
        sh = wb.create_sheet(title)
        for row in items[tag]:
            sh.append(row + [""] * (5 - len(row)))
        sh.freeze_panes = "A2"
        for col, width in zip("ABCDE", (7, 62, 62, 10, 10)):
            sh.column_dimensions[col].width = width
        for cell in sh[1]:
            cell.font = Font(bold=True)
            cell.fill = HEAD
        last = len(items[tag])
        for r in range(2, last + 1):
            for c in (2, 3):
                sh.cell(r, c).alignment = Alignment(wrap_text=True, vertical="top")
            for c in (4, 5):
                sh.cell(r, c).fill = FILL
                sh.cell(r, c).alignment = Alignment(horizontal="center", vertical="top")
        answer = DataValidation(type="list", formula1='"A,B"', allow_blank=True)
        unsure = DataValidation(type="list", formula1='"x"', allow_blank=True)
        sh.add_data_validation(answer)
        sh.add_data_validation(unsure)
        answer.add(f"D2:D{last}")
        unsure.add(f"E2:E{last}")
    return wb


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("codes", nargs="+", help="participant codes, one workbook each")
    p.add_argument("--out", default="human_study_sheets", help="output folder (keep it out of the repository)")
    args = p.parse_args()
    instr = json.loads((STUDY / "workbook_instructions.json").read_text(encoding="utf-8"))
    items = {tag: list(csv.reader(open(STUDY / f"forced_choice_{tag}.csv", encoding="utf-8-sig"))) for tag in ("latn", "cyrl")}
    assert len(items["latn"]) == len(items["cyrl"]), "the Latin and Cyrillic sheets must have the same items"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for code in args.codes:
        path = out / f"UzBLiMP_sorovnoma_{code}.xlsx"
        workbook(code, instr, items).save(path)
        print("wrote", path)


if __name__ == "__main__":
    main()
