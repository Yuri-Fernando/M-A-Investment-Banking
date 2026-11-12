"""Optional official CVM snapshot ingestion; never joined into synthetic target facts."""

import csv
import io
import json
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

from .contracts import ModelError
from .ingestion import amount_brl, digest


def download_cvm(kind: str, year: int, destination: Path) -> Path:
    """Opt-in official ZIP snapshot, immutable by hash; no automatic refresh."""
    if kind not in ("dfp", "itr") or not 2010 <= year <= date.today().year:
        raise ModelError("Invalid CVM kind/year")
    url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{kind.upper()}/DADOS/{kind}_cia_aberta_{year}.zip"
    with urlopen(url, timeout=45) as response:
        raw = response.read(150_000_001)
    if len(raw) > 150_000_000:
        raise ModelError("CVM snapshot exceeds size limit")
    with ZipFile(io.BytesIO(raw)) as archive:
        if not archive.namelist():
            raise ModelError("Empty CVM ZIP")
    snapshot = Path(destination) / digest(raw)
    snapshot.mkdir(parents=True, exist_ok=True)
    path = snapshot / "source.zip"
    if not path.exists():
        path.write_bytes(raw)
        (snapshot / "manifest.json").write_text(
            json.dumps(
                {
                    "source_url": url,
                    "downloaded_at": datetime.now(timezone.utc).isoformat(),
                    "sha256": digest(raw),
                    "data_class": "PUBLIC_OFFICIAL",
                    "license": "ODbL; verify attribution and redistribution obligations",
                    "available_at": None,
                    "point_in_time_status": "REQUIRES_FILING_PUBLICATION_EVIDENCE",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return path


def parse_cvm(
    path: Path, member: str, entity_cnpj: str, scope: str, as_of: str, available_at: str, version: str
) -> list[dict]:
    """Parse an explicitly chosen DRE/BPA/BPP/DFC member/version.

    Publication date must come from filing evidence supplied by analyst, not DT_REFER.
    Returns original CVM account codes; EBITDA, cash/debt mapping require reviewed policy.
    Duplicate/cumulative-period/scope differences are preserved or rejected, never summed.
    """
    date.fromisoformat(as_of)
    date.fromisoformat(available_at)
    if available_at > as_of:
        raise ModelError("DATA_FUTURE_LEAK: filing publication after cutoff")
    if entity_cnpj == "NEXAOPS_SYNTH" or scope not in ("CON", "IND"):
        raise ModelError("SCOPE_MISMATCH")
    if f"_{scope.lower()}_" not in member:
        raise ModelError("SCOPE_MISMATCH: archive member does not match requested scope")
    raw = Path(path).read_bytes()
    with ZipFile(io.BytesIO(raw)) as archive:
        info = archive.getinfo(member)
        if info.file_size > 300_000_000:
            raise ModelError("Oversized CVM member")
        text = archive.read(member).decode("latin-1")
    result, keys = [], set()
    for row in csv.DictReader(io.StringIO(text), delimiter=";"):
        if row["CNPJ_CIA"] != entity_cnpj or row["ORDEM_EXERC"] != "ÚLTIMO" or row["VERSAO"] != version:
            continue
        end = row["DT_FIM_EXERC"]
        if end > as_of:
            raise ModelError("DATA_FUTURE_LEAK")
        start = row.get("DT_INI_EXERC", "")
        key = (row["CD_CONTA"], start, end)
        if key in keys:
            raise ModelError("DUPLICATE_VERSION: review restatement/period")
        keys.add(key)
        scale = {"MIL": "BRL_thousands", "UNIDADE": "BRL"}.get(row["ESCALA_MOEDA"])
        if scale is None or row["MOEDA"] != "REAL":
            raise ModelError("Unsupported CVM currency/scale")
        result.append(
            {
                "entity_id": entity_cnpj,
                "scope": scope,
                "period_start": start,
                "period_end": end,
                "account_code": row["CD_CONTA"],
                "amount_brl": amount_brl(row["VL_CONTA"], scale),
                "data_class": "PUBLIC_OFFICIAL",
                "snapshot_hash": digest(raw),
                "source": member,
                "available_at": available_at,
                "version": version,
            }
        )
    if not result:
        raise ModelError("No CVM accounts matched explicit entity/scope/version")
    return result


def trading_comps(peers: list[dict], as_of: str) -> dict:
    """Only complete, evidenced same-date inputs, full BRL, produce peer multiples.

    Requires verified aligned lease accounting. Missing data is excluded, never zero.
    This contract is an import facility, not a claim of live market-data coverage.
    """
    included, excluded = [], []
    amounts = (
        "market_cap",
        "debt",
        "cash",
        "leases",
        "minority",
        "preferred",
        "nonoperating",
        "ltm_ebitda",
        "ltm_revenue",
    )
    for p in peers:
        reason = None
        if any(p.get(k) is None for k in amounts):
            reason = "MISSING_REQUIRED_FINANCIAL_OR_QUOTE"
        elif not p.get("source_url") or not p.get("snapshot_hash") or not p.get("inclusion_reason"):
            reason = "MISSING_PROVENANCE"
        elif p.get("available_at", "9999") > as_of or p.get("quote_date") != as_of:
            reason = "ASOF_MISMATCH"
        elif p.get("capital_structure_date") != as_of or p.get("ltm_end") != as_of:
            reason = "ASOF_MISMATCH"
        elif p.get("data_class") not in ("PUBLIC_OFFICIAL", "PUBLIC_THIRD_PARTY"):
            reason = "NOT_PUBLIC_PEER"
        elif p.get("lease_policy") != "ALIGNED":
            reason = "LEASE_POLICY_REVIEW"
        elif any(not isinstance(p[k], (int, float)) for k in amounts):
            reason = "INVALID_AMOUNT"
        elif any(not __import__("math").isfinite(p[k]) for k in amounts):
            reason = "INVALID_AMOUNT"
        elif p["ltm_ebitda"] <= 0 or p["ltm_revenue"] <= 0:
            reason = "NEGATIVE_DENOMINATOR"
        elif min(p[k] for k in amounts[:7]) < 0:
            reason = "NEGATIVE_CAPITAL_STRUCTURE"
        if reason:
            excluded.append({"name": p.get("name", "unknown"), "reason": reason})
            continue
        ev = (
            p["market_cap"]
            + p["debt"]
            + p["leases"]
            + p["minority"]
            + p["preferred"]
            - p["cash"]
            - p["nonoperating"]
        )
        if ev <= 0:
            excluded.append({"name": p.get("name", "unknown"), "reason": "NONPOSITIVE_EV"})
            continue
        included.append(
            {**p, "ev": ev, "ev_ebitda": ev / p["ltm_ebitda"], "ev_revenue": ev / p["ltm_revenue"]}
        )
    unique_names = {p.get("name") for p in included}
    if len(unique_names) != len(included):
        raise ModelError("DUPLICATE_PEER")
    import statistics

    enough = len(included) >= 3
    return {
        "status": "AVAILABLE" if enough else "INSUFFICIENT_COMPS",
        "included": included,
        "excluded": excluded,
        "median_ev_ebitda": statistics.median(p["ev_ebitda"] for p in included) if enough else None,
        "transaction_comps": "NOT_ENOUGH_VERIFIED_DEAL_DATA",
    }
