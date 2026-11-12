import csv

import pytest

from ma_deallab.contracts import ModelError
from ma_deallab.ingestion import amount_brl, load_case
from ma_deallab.public_data import trading_comps
from ma_deallab.services import build_run


def mutate(path, change):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames)
    rows, fields = change(rows, fields)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_d01_future_publication(data_dir):
    def change(rows, fields):
        for row in rows:
            row["available_at"] = "2026-10-01"
        return rows, fields + ["available_at"]

    mutate(data_dir / "synthetic_income_statement.csv", change)
    with pytest.raises(ModelError, match="FUTURE"):
        load_case(data_dir)


def test_d02_duplicate(data_dir):
    mutate(data_dir / "synthetic_income_statement.csv", lambda r, f: (r + [r[0]], f))
    with pytest.raises(ModelError, match="DUPLICATE"):
        load_case(data_dir)


def test_f14_missing_account(data_dir):
    mutate(data_dir / "synthetic_balance_sheet.csv", lambda r, f: (r[1:], f))
    with pytest.raises(ModelError, match="MISSING_REQUIRED"):
        load_case(data_dir)


def test_f11_negative_magnitude(data_dir):
    def change(rows, fields):
        rows[0]["amount_brl_millions"] = "-58"
        return rows, fields

    mutate(data_dir / "synthetic_income_statement.csv", change)
    with pytest.raises(ModelError, match="Sign"):
        load_case(data_dir)


def test_f15_synthetic_scope_isolation(data_dir):
    def change(rows, fields):
        rows[0]["entity_id"] = "REAL_CNPJ"
        return rows, fields

    mutate(data_dir / "synthetic_balance_sheet.csv", change)
    with pytest.raises(ModelError, match="SCOPE"):
        load_case(data_dir)


def test_d03_d04_explicit_units_locale():
    assert amount_brl("1.234,56", "BRL", "pt_BR") == 1234.56
    assert amount_brl("1.23456", "BRL_thousands") == 1234.56
    assert amount_brl("0.00123456") == 1234.56
    with pytest.raises(ModelError):
        amount_brl("1,234")
    with pytest.raises(ModelError):
        amount_brl("10", "USD")


def test_d07_reproducibility():
    assert build_run()["run_id"] == build_run()["run_id"]


def test_source_hash_and_registry(run):
    assert all(len(s["sha256"]) == 64 for s in run["sources"].values())
    assert run["metrics"]["ltm.net_revenue"]["value"] == 99_000_000
    assert run["metrics"]["ltm.net_revenue"]["formula_reference"].startswith("FY2025")
    assert run["metrics"]["bridge.equity"]["run_id"] == run["run_id"]


def test_v12_v13_missing_comps():
    result = trading_comps([{"name": "Missing quote"}], "2026-09-30")
    assert result["status"] == "INSUFFICIENT_COMPS"
    assert result["median_ev_ebitda"] is None
    assert result["excluded"][0]["reason"] == "MISSING_REQUIRED_FINANCIAL_OR_QUOTE"


def peer(name):
    return {
        "name": name,
        "market_cap": 100,
        "debt": 20,
        "cash": 10,
        "leases": 0,
        "minority": 0,
        "preferred": 0,
        "nonoperating": 0,
        "ltm_ebitda": 10,
        "ltm_revenue": 50,
        "quote_date": "2026-09-30",
        "capital_structure_date": "2026-09-30",
        "ltm_end": "2026-09-30",
        "available_at": "2026-09-30",
        "source_url": "https://example.invalid/test-fixture",
        "snapshot_hash": "a" * 64,
        "inclusion_reason": "Test contract only",
        "lease_policy": "ALIGNED",
        "data_class": "PUBLIC_OFFICIAL",
    }


def test_public_comp_contract_three_peers_only():
    result = trading_comps([peer(n) for n in ("test-a", "test-b", "test-c")], "2026-09-30")
    assert result["median_ev_ebitda"] == 11
    assert result["status"] == "AVAILABLE"


def test_public_comp_asof():
    p = peer("test-only")
    p["available_at"] = "2026-10-01"
    assert trading_comps([p], "2026-09-30")["excluded"][0]["reason"] == "ASOF_MISMATCH"
