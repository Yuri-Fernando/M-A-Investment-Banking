"""CLI: validate -> model -> export; demo runs the complete offline flow."""

import argparse
import json
import sys
from pathlib import Path

from .contracts import ModelError
from .ingestion import load_case
from .public_data import download_cvm, parse_cvm
from .services import build_run


def main(argv=None):
    parser = argparse.ArgumentParser(description="Synthetic M&A DealLab | Python 3.10")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("demo", "validate", "model", "export"):
        p = sub.add_parser(name)
        p.add_argument("--data-dir", type=Path)
        p.add_argument("--output", type=Path, default=Path("outputs"))
        p.add_argument("--assumptions", type=Path, help="JSON mapping scenario -> driver overrides, full BRL")
        p.add_argument("--qoe-decisions", type=Path, help="JSON issue -> reviewer and evidence_id")
        p.add_argument("--peers", type=Path, help="JSON sourced peer inputs, full BRL")
    p = sub.add_parser("verify")
    p.add_argument("directory", type=Path)
    p = sub.add_parser("fetch-cvm", help="Explicit opt-in official network download")
    p.add_argument("kind", choices=("dfp", "itr"))
    p.add_argument("year", type=int)
    p.add_argument("--output", type=Path, default=Path("data/raw/cvm"))
    p = sub.add_parser(
        "inspect-cvm", help="Explicit member/scope/version parse, publication evidence required"
    )
    p.add_argument("zip", type=Path)
    for key in ("member", "cnpj", "scope", "as-of", "available-at", "version"):
        p.add_argument("--" + key, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            from .export import verify_artifacts

            result = verify_artifacts(args.directory)
        elif args.command == "fetch-cvm":
            result = {"snapshot": str(download_cvm(args.kind, args.year, args.output))}
        elif args.command == "inspect-cvm":
            result = parse_cvm(
                args.zip, args.member, args.cnpj, args.scope, args.as_of, args.available_at, args.version
            )
        elif args.command == "validate":
            case = load_case(args.data_dir)
            result = {"status": "PASS", "checks": case["checks"]}
        else:

            def read(p):
                return json.loads(p.read_text(encoding="utf-8")) if p else None

            run = build_run(args.data_dir, read(args.assumptions), read(args.qoe_decisions), read(args.peers))
            result = {
                "status": "PASS",
                "run_id": run["run_id"],
                "as_of": run["as_of"],
                "ev_brl": {k: s["valuation"]["ev"] for k, s in run["scenarios"].items()},
                "closing": run["closing_status"],
            }
            if args.command in ("demo", "export"):
                from .export import export_run

                result["output"] = str(export_run(run, args.output, args.data_dir).resolve())
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ModelError, ValueError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
