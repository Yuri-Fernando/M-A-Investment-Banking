import json

import pytest
from pptx import Presentation

from ma_deallab.contracts import ModelError
from ma_deallab.export import export_run, verify_artifacts
from ma_deallab.services import build_run
from ma_deallab.verification import verify_workbook
from ma_deallab.workbook import TABS, export_workbook


def test_v14_workbook_all_formula_parity(run, tmp_path):
    path = tmp_path / "base.xlsx"
    fm = export_workbook(run, path)
    audit = verify_workbook(path, fm)
    assert len(fm["tabs"]) == 33
    assert len(set(TABS)) == 33
    assert audit["formulas_evaluated"] > 400


def test_complete_frozen_packet(run, tmp_path):
    fitz = pytest.importorskip("fitz")
    target = export_run(run, tmp_path / "out")
    assert verify_artifacts(target)["status"] == "PASS"
    for kind, expected in (("ic", 4), ("dd", 6), ("valuation", 4), ("closing", 3), ("anonymous_teaser", 1)):
        doc = fitz.open(target / "reports" / f"{kind}.pdf")
        assert len(doc) == expected
        alltext = "".join(page.get_text() for page in doc)
        assert "SYNTHETIC" in alltext
        if kind == "anonymous_teaser":
            assert "NexaOps" not in alltext
            assert "Atlas" not in alltext
        doc.close()
    for kind, count in (("cim", 16), ("management", 10)):
        prs = Presentation(target / "presentations" / f"{kind}.pptx")
        assert len(prs.slides) == count
        for slide in prs.slides:
            assert any("SYNTHETIC" in sh.text for sh in slide.shapes if sh.has_text_frame)
            for shape in slide.shapes:
                assert shape.left >= 0 and shape.top >= 0
                assert shape.left + shape.width <= prs.slide_width + 100
                assert shape.top + shape.height <= prs.slide_height + 100
    audit = json.loads((target / "workbooks" / "parity_audit.json").read_text())
    assert all(v["status"] == "PASS" for v in audit.values())
    # Re-export may not modify immutable existing outputs.
    before = (target / "manifest.json").read_bytes()
    assert export_run(run, tmp_path / "out") == target
    assert (target / "manifest.json").read_bytes() == before
    (target / "reports" / "ic.md").write_text("corrupt", encoding="utf-8")
    with pytest.raises(ModelError, match="INTEGRITY"):
        verify_artifacts(target)


def test_mutated_run_blocks_export(run, tmp_path):
    import copy

    changed = copy.deepcopy(run)
    changed["bridge"]["equity"] += 1
    with pytest.raises(ModelError, match="RUN_INTEGRITY"):
        export_run(changed, tmp_path)


def test_negative_cash_blocks_export(tmp_path):
    changed = build_run(overrides={"base": {"q4_revenue": 1e9, "nwc_ratio": 0.9}})
    with pytest.raises(ModelError, match="FINANCING_REQUIRED"):
        export_run(changed, tmp_path)


def test_tampered_metric_registry_blocks_export(run, tmp_path):
    import copy

    changed = copy.deepcopy(run)
    changed["metrics"]["bridge.equity"]["value"] += 1
    with pytest.raises(ModelError, match="RUN_INTEGRITY"):
        export_run(changed, tmp_path)
