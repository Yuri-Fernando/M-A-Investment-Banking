"""Capture real generated Excel worksheets and native PowerPoint renders for the README.

Windows + installed Excel + pywin32 + PyMuPDF are optional prerequisites.
Usage: py -3.10 scripts/capture_readme_office.py outputs/<run_id>
       --native-render-dir outputs/validation/<run_id>/rendered
"""

import argparse
import shutil
import tempfile
from pathlib import Path

import fitz


def main():
    import pythoncom
    import win32com.client

    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--native-render-dir", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = root / "docs" / "assets"
    output.mkdir(parents=True, exist_ok=True)
    pythoncom.CoInitialize()
    excel = None
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.AutomationSecurity = 3
        with tempfile.TemporaryDirectory(prefix="deallab-readme-") as scratch:
            scratch = Path(scratch)
            source = args.run_dir / "workbooks" / "ma_model_base.xlsx"
            local = scratch / "model.xlsx"
            shutil.copyfile(source, local)
            workbook = excel.Workbooks.Open(str(local), UpdateLinks=0, ReadOnly=False)
            try:
                excel.CalculateFullRebuild()
                for sheet_name, area, filename in (
                    ("23_DCF", "$A$1:$G$16", "excel-dcf"),
                    ("31_Checks", "$A$1:$D$28", "excel-checks"),
                ):
                    sheet = workbook.Worksheets(sheet_name)
                    sheet.PageSetup.PrintArea = area
                    sheet.PageSetup.Orientation = 2
                    sheet.PageSetup.Zoom = False
                    sheet.PageSetup.FitToPagesWide = 1
                    sheet.PageSetup.FitToPagesTall = 1
                    pdf_path = scratch / f"{filename}.pdf"
                    sheet.ExportAsFixedFormat(0, str(pdf_path))
                    with fitz.open(pdf_path) as document:
                        document[0].get_pixmap(matrix=fitz.Matrix(1.6, 1.6)).save(output / f"{filename}.png")
            finally:
                workbook.Close(SaveChanges=False)
    finally:
        if excel is not None:
            excel.Quit()
        pythoncom.CoUninitialize()
    if args.native_render_dir:
        for source, name in (
            (args.native_render_dir / "cim" / "slide_12.png", "cim-valuation.png"),
            (args.native_render_dir / "management" / "slide_01.png", "management-cover.png"),
        ):
            shutil.copyfile(source, output / name)
    print("Captured native Office previews:", output)


if __name__ == "__main__":
    main()
