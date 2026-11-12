"""Transactional frozen exports, input snapshots, SQLite warehouse and integrity checks."""

import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

from .contracts import DISCLAIMER, M, ModelError
from .ingestion import canonical_hash, default_data_dir, digest
from .presentations import export_presentation
from .reporting import write_markdown, write_pdf, write_teaser
from .services import code_fingerprint, manifest, metric_registry
from .verification import verify_workbook
from .workbook import export_workbook


def json_file(path, value):
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False), encoding="utf-8"
    )


def verify_artifacts(directory: Path) -> dict:
    """Verify all frozen artifact checksums; fail on corruption/deletion."""
    data = json.loads((Path(directory) / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in data["artifacts"].items():
        path = Path(directory) / name
        if not path.resolve().is_relative_to(Path(directory).resolve()):
            raise ModelError("ARTIFACT_INTEGRITY: path outside frozen run")
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise ModelError(f"ARTIFACT_INTEGRITY: {name}")
    return {"status": "PASS", "run_id": data["run_id"], "artifacts": len(data["artifacts"])}


def export_html(run: dict, path: Path):
    """Standalone offline HTML overview; Plotly runtime embedded once, no CDN."""
    names = list(run["scenarios"])
    fig = go.Figure(
        go.Bar(
            x=names,
            y=[run["scenarios"][n]["valuation"]["ev"] / M for n in names],
            marker_color=["#B85450", "#087E8B", "#142D4E"],
            name="Standalone EV",
        )
    )
    fig.add_hline(y=run["bridge"]["ev"] / M, line_dash="dash", annotation_text="Illustrative bid EV")
    fig.update_layout(template="plotly_white", title="Standalone DCF EV by scenario | R$ mi", height=440)
    chart = pio.to_html(fig, include_plotlyjs=True, full_html=False)
    rows = "".join(
        f"<tr><td>{n}</td><td>{run['scenarios'][n]['valuation']['ev'] / M:,.2f}</td>"
        f"<td>{run['scenarios'][n]['decision']}</td></tr>"
        for n in names
    )
    html = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
    <title>Project Aurora | Synthetic DealLab</title>
    <style>body{{font:16px system-ui;background:#f4f7fa;color:#142d4e;margin:32px auto;max-width:1100px;padding:20px}}
    .tag{{background:#d8ecee;padding:9px;border-radius:6px}}.cards{{display:flex;gap:16px;flex-wrap:wrap;margin:30px 0}}
    .card{{background:white;padding:22px;min-width:180px;border:1px solid #dce3ec}}strong{{font-size:30px}}
    table{{border-collapse:collapse;width:100%;background:white}}td,th{{padding:14px;text-align:left;border-bottom:1px solid #ddd}}</style>
    <p class="tag">SYNTHETIC / AS-OF {run["as_of"]} / R$ mi / DRAFT</p>
    <h1>Project Aurora</h1><p>NexaOps Analytics Ltda. | M&amp;A DealLab Brazil</p>
    <div class="cards"><div class="card">LTM revenue<br><strong>{run["ltm"]["net_revenue"] / M:,.2f}</strong></div>
    <div class="card">LTM EBITDA<br><strong>{run["ltm"]["ebitda"] / M:,.2f}</strong></div>
    <div class="card">Financial net debt<br><strong>{run["net_debt"] / M:,.2f}</strong></div>
    <div class="card">Equity at bid<br><strong>{run["bridge"]["equity"] / M:,.2f}</strong></div></div>
    <h2>Price requires review</h2><p>Base recommendation: {run["scenarios"]["base"]["decision"]}.
    {run["closing_status"]}. NWC peg remains unagreed; proposed QoE adjustments remain unaccepted by default.</p>
    {chart}<table><tr><th>Scenario</th><th>Standalone EV</th><th>Conditional decision</th></tr>{rows}</table>
    <h2>Evidence and limitations</h2><p>Trading comparables: {run["comps"]["status"]}. Executed deals:
    {run["comps"]["transaction_comps"]}.</p><p>Run {run["run_id"]}. See manifest.json, run.json,
    metrics_registry.json, workbooks and draft reports in this frozen directory.</p><p>{DISCLAIMER}</p></html>"""
    path.write_text(html, encoding="utf-8")


def export_sqlite(run: dict, path: Path):
    """Queryable local full-BRL facts/forecasts, with hashes and run IDs."""
    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TABLE financial_facts(kind TEXT, period_end TEXT, account TEXT, amount_brl REAL, "
            "source_hash TEXT, data_class TEXT, PRIMARY KEY(kind,period_end,account))"
        )
        sources = {
            "income": "synthetic_income_statement.csv",
            "balance": "synthetic_balance_sheet.csv",
            "cashflow": "synthetic_cash_flow.csv",
        }
        for kind, source in sources.items():
            for end, facts in run[kind].items():
                db.executemany(
                    "INSERT INTO financial_facts VALUES(?,?,?,?,?,?)",
                    [
                        (kind, end, k, v, run["sources"][source]["sha256"], "SYNTHETIC")
                        for k, v in facts.items()
                    ],
                )
        db.execute("CREATE TABLE forecasts(run_id TEXT,scenario TEXT,year INT,account TEXT,amount_brl REAL)")
        for name, s in run["scenarios"].items():
            for row in s["forecast"]:
                db.executemany(
                    "INSERT INTO forecasts VALUES(?,?,?,?,?)",
                    [
                        (run["run_id"], name, row["year"], k, row[k])
                        for k in (
                            "net_revenue",
                            "ebitda",
                            "ebit",
                            "net_income",
                            "fcff",
                            "cash",
                            "capex",
                            "nwc",
                        )
                    ],
                )
        db.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY,value_json TEXT)")
        db.executemany(
            "INSERT INTO metadata VALUES(?,?)",
            [
                (k, json.dumps(run[k], sort_keys=True))
                for k in ("run_id", "sources", "checks", "as_of", "policy")
            ],
        )


def export_run(run: dict, output: Path, data_dir: Path | None = None) -> Path:
    """All artifacts are draft, frozen under outputs/<run_id>; atomic same-volume publish.

    Critical checks/negative cash block export. Existing complete runs are verified
    and reused. No approved distribution or closing is implied by generation.
    """
    if any(c["status"] != "PASS" for c in run["checks"]):
        raise ModelError("Critical financial checks block export")
    if any(s["warnings"] for s in run["scenarios"].values()):
        raise ModelError("FINANCING_REQUIRED: negative forecast cash blocks export")
    payload = {k: v for k, v in run.items() if k not in ("run_id", "metrics")}
    if canonical_hash(payload)[:20] != run["run_id"]:
        raise ModelError("RUN_INTEGRITY: model changed after freeze")
    if code_fingerprint() != run["code_hashes"] or metric_registry(run) != run["metrics"]:
        raise ModelError("RUN_INTEGRITY: code or metric registry changed after freeze")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    target = output / run["run_id"]
    if target.exists():
        verify_artifacts(target)
        return target
    stage = Path(tempfile.mkdtemp(prefix=".building-", dir=output))
    try:
        for sub in ("reports", "workbooks", "presentations", "snapshots", "vdr"):
            (stage / sub).mkdir()
        source_dir = Path(data_dir) if data_dir else default_data_dir()
        for name, source in run["sources"].items():
            raw = (source_dir / name).read_bytes()
            if digest(raw) != source["sha256"]:
                raise ModelError("INPUT_CHANGED_AFTER_RUN")
            (stage / "snapshots" / name).write_bytes(raw)
        json_file(stage / "run.json", run)
        json_file(stage / "metrics_registry.json", run["metrics"])
        audits = {}
        for name in run["scenarios"]:
            workbook = stage / "workbooks" / f"ma_model_{name}.xlsx"
            fm = export_workbook(run, workbook, name)
            audits[name] = verify_workbook(workbook, fm)
            json_file(stage / "workbooks" / f"formulas_{name}.json", fm)
        json_file(stage / "workbooks" / "parity_audit.json", audits)
        for kind in ("ic", "dd", "valuation", "closing"):
            write_pdf(run, stage / "reports" / f"{kind}.pdf", kind)
            write_markdown(run, stage / "reports" / f"{kind}.md", kind)
        write_teaser(run, stage / "reports" / "anonymous_teaser.pdf")
        from .materials import write_transaction_materials

        write_transaction_materials(run, stage / "reports")
        for kind in ("cim", "management"):
            export_presentation(run, stage / "presentations" / f"{kind}.pptx", kind)
        export_sqlite(run, stage / "warehouse.sqlite")
        export_html(run, stage / "dashboard.html")
        # Evidence requests are synthetic, not a claim of completed diligence.
        for issue in run["qoe"]["items"]:
            (stage / "vdr" / f"{issue['evidence_id']}.md").write_text(
                f"# {issue['evidence_id']}\n\n{DISCLAIMER}\n\n"
                f"Description: {issue['description']}\nPeriod: {issue['period_end']}\n"
                f"Proposed magnitude: {issue['amount_brl_millions'] or 'not monetary'} R$ mi\n"
                "Status: evidence illustration / REVIEW_REQUIRED. Not proof of acceptance.\n",
                encoding="utf-8",
            )
        json_file(
            stage / "vdr" / "index.json",
            {
                "scope": "SIMULATED_ROLE_POLICY_ONLY",
                "approved": False,
                "issues": run["risks"],
                "planned_events": run["planned_events"],
            },
        )
        m = manifest(run)
        m["workbook_parity"] = audits
        m["artifacts"] = {
            p.relative_to(stage).as_posix(): digest(p.read_bytes())
            for p in sorted(stage.rglob("*"))
            if p.is_file()
        }
        json_file(stage / "manifest.json", m)
        stage.rename(target)
        verify_artifacts(target)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return target
