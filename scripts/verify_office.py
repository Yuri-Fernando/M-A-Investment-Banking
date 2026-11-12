"""Optional Windows native Excel recalculation and PowerPoint rendering.

Run with py -3.10 scripts/verify_office.py outputs/<run_id>.
Only copied synthetic workbooks and the generated presentations are opened.
Evidence is written outside immutable run directories, under outputs/validation/<run_id>.
"""

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import pythoncom
import win32com.client


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    source = args.run_dir.resolve()
    output = source.parent / "validation" / source.name
    output.mkdir(parents=True, exist_ok=True)
    audit = {"run_id": source.name, "excel": {}, "powerpoint": {}}
    pythoncom.CoInitialize()
    excel = None
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.AutomationSecurity = 3
        with tempfile.TemporaryDirectory(prefix="ma-excel-") as scratch:
            for scenario in ("downside", "base", "upside"):
                original = source / "workbooks" / f"ma_model_{scenario}.xlsx"
                copy = Path(scratch) / original.name
                shutil.copyfile(original, copy)
                workbook = excel.Workbooks.Open(str(copy), UpdateLinks=0, ReadOnly=False)
                try:
                    excel.CalculateFullRebuild()
                    formulas = json.loads((source / "workbooks" / f"formulas_{scenario}.json").read_text())[
                        "formulas"
                    ]
                    max_error = 0.0
                    for f in formulas:
                        value = workbook.Worksheets(f["sheet"]).Range(f["cell"]).Value
                        expected = f["expected"]
                        if not isinstance(value, (float, int)) or abs(value - expected) > max(
                            1e-8, abs(expected) * 1e-9
                        ):
                            raise AssertionError(
                                f"Native Excel mismatch {f['sheet']}!{f['cell']}: {value} != {expected}"
                            )
                        max_error = max(max_error, abs(value - expected))
                    audit["excel"][scenario] = {
                        "status": "PASS",
                        "formulas": len(formulas),
                        "max_abs_error": max_error,
                        "application_version": excel.Version,
                    }
                    print("Native Excel PASS", scenario, len(formulas), flush=True)
                finally:
                    workbook.Close(SaveChanges=False)
    finally:
        if excel is not None:
            excel.Quit()
    (output / "native_office_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    powerpoint = win32com.client.DispatchEx("PowerPoint.Application")
    # PowerPoint can share its process with an existing user session.
    # Close only the presentations opened here; do not quit the application.
    with tempfile.TemporaryDirectory(prefix="ma-ppt-") as scratch:
        short_output = Path(scratch)
        for kind in ("cim", "management"):
            shutil.copyfile(source / "presentations" / f"{kind}.pptx", short_output / f"{kind}.pptx")
            pres = powerpoint.Presentations.Open(
                str(short_output / f"{kind}.pptx"), ReadOnly=True, Untitled=False, WithWindow=False
            )
            try:
                destination = short_output / kind
                destination.mkdir(exist_ok=True)
                overflow = []
                for i in range(1, pres.Slides.Count + 1):
                    slide = pres.Slides(i)
                    slide.Export(str(destination / f"slide_{i:02d}.png"), "PNG", 1600, 900)
                    for j in range(1, slide.Shapes.Count + 1):
                        shape = slide.Shapes(j)
                        if shape.HasTextFrame and shape.TextFrame.HasText:
                            if shape.TextFrame2.TextRange.BoundHeight > shape.Height + 2:
                                overflow.append(
                                    {"slide": i, "shape": j, "text": shape.TextFrame.TextRange.Text}
                                )
                pres.SaveAs(str(short_output / f"{kind}.pdf"), 32)
                if overflow:
                    raise AssertionError(f"PowerPoint text overflow: {overflow}")
                audit["powerpoint"][kind] = {
                    "status": "PASS",
                    "slides": pres.Slides.Count,
                    "text_overflow": overflow,
                }
                print("Native PowerPoint PASS", kind, pres.Slides.Count, flush=True)
            finally:
                pres.Close()
        shutil.copytree(short_output, output / "rendered", dirs_exist_ok=True)
    (output / "native_office_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    pythoncom.CoUninitialize()
    print(output, flush=True)


if __name__ == "__main__":
    main()
