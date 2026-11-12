"""Independent arithmetic evaluator for the workbook's documented formula subset."""

import ast
import math
import operator
import re
from pathlib import Path

import openpyxl

from .contracts import ModelError


def verify_workbook(path: Path, formula_manifest: dict) -> dict:
    """Evaluate cell references/arithmetic/MAX without using Python cached outputs.

    This covers every generated formula. It is not a replacement for a native
    Excel/LibreOffice acceptance check for arbitrary user-edited workbook formulas.
    """
    book = openpyxl.load_workbook(path, data_only=False)
    cache = openpyxl.load_workbook(path, data_only=True)
    memo, visiting = {}, set()
    ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }

    def evaluate(sheet, cell):
        key = (sheet, cell)
        if key in memo:
            return memo[key]
        if key in visiting:
            raise ModelError(f"Workbook circular reference {key}")
        visiting.add(key)
        raw = book[sheet][cell].value
        if not isinstance(raw, str) or not raw.startswith("="):
            if not isinstance(raw, (int, float)):
                raise ModelError(f"Non-numeric workbook dependency {key}: {raw}")
            result = raw
        else:
            expr = raw[1:]
            expr = re.sub(r"'([^']+)'!([A-Z]+[0-9]+)", lambda m: repr(evaluate(m[1], m[2])), expr)
            expr = re.sub(r"\b([A-Z]+[0-9]+)\b", lambda m: repr(evaluate(sheet, m[1])), expr)
            expr = expr.replace("^", "**")

            def walk(node):
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                    return node.value
                if isinstance(node, ast.BinOp) and type(node.op) in ops:
                    return ops[type(node.op)](walk(node.left), walk(node.right))
                if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                    return walk(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in ("MAX", "MIN")
                ):
                    return (max if node.func.id == "MAX" else min)(walk(n) for n in node.args)
                raise ModelError("Unsupported workbook expression")

            result = walk(ast.parse(expr, mode="eval").body)
        visiting.remove(key)
        memo[key] = result
        return result

    max_error = 0.0
    for entry in formula_manifest["formulas"]:
        result = evaluate(entry["sheet"], entry["cell"])
        expected = entry["expected"]
        cached = cache[entry["sheet"]][entry["cell"]].value
        tolerance = max(1e-9, abs(expected) * 1e-10)
        if not math.isfinite(result) or abs(result - expected) > tolerance:
            raise ModelError(f"WORKBOOK_PARITY {entry['sheet']}!{entry['cell']}: {result} != {expected}")
        if cached is None or abs(cached - expected) > tolerance:
            raise ModelError("WORKBOOK_CACHE_MISMATCH")
        max_error = max(max_error, abs(result - expected))
    book.close()
    cache.close()
    return {
        "status": "PASS",
        "formulas_evaluated": len(formula_manifest["formulas"]),
        "max_absolute_error_display_units": max_error,
        "native_excel_recalculation": "NOT_RUN",
        "method": "Independent AST evaluator for all generated arithmetic/reference/MAX formulas",
    }
