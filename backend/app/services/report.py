"""Report generation service — HTML + PDF via WeasyPrint."""
import io
import os
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.practice import Practice

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"

# Fix WeasyPrint library discovery on macOS with Homebrew.
# WeasyPrint uses cffi.dlopen() which searches standard paths.
# On macOS, Homebrew libs live in /opt/homebrew/lib and aren't in the default search path.
# We patch cffi's ffi.dlopen to also try /opt/homebrew/lib/<name>.dylib variants.
if sys.platform == "darwin":
    _brew_lib = "/opt/homebrew/lib"
    if os.path.isdir(_brew_lib):
        import cffi

        _orig_dlopen = cffi.FFI.dlopen

        def _patched_dlopen(self, *args, **kwargs):
            try:
                return _orig_dlopen(self, *args, **kwargs)
            except OSError:
                name = args[0] if args else ""
                # Try Homebrew path with .dylib extension
                for suffix in [".dylib", ".0.dylib"]:
                    brew_path = os.path.join(_brew_lib, f"lib{name}{suffix}")
                    if os.path.exists(brew_path):
                        return _orig_dlopen(self, brew_path, **(kwargs or {}))
                    # Also try the name as-is with .dylib
                    brew_path = os.path.join(_brew_lib, f"{name}.dylib")
                    if os.path.exists(brew_path):
                        return _orig_dlopen(self, brew_path, **(kwargs or {}))
                # If name looks like libfoo-X.Y-Z, try libfoo-X.Y.Z.dylib
                if isinstance(name, str) and "-" in name:
                    parts = name.rsplit("-", 1)
                    dylib_name = f"{parts[0]}.{parts[1]}.dylib"
                    brew_path = os.path.join(_brew_lib, dylib_name)
                    if os.path.exists(brew_path):
                        return _orig_dlopen(self, brew_path, **(kwargs or {}))
                raise

        cffi.FFI.dlopen = _patched_dlopen


def generate_report_html(contract_id: int, db: Session) -> str:
    """Generate HTML comparison report for a contract."""
    contract = db.get(Contract, contract_id)
    practice = db.get(Practice, contract.practice_id)

    rates = sorted(contract.rates, key=lambda r: (r.pct_of_medicare or 0))
    matched = [r for r in rates if r.medicare_rate is not None]
    unmatched = [r for r in rates if r.medicare_rate is None]

    summary = {}
    if matched:
        pcts = [r.pct_of_medicare for r in matched if r.pct_of_medicare]
        summary["avg_pct"] = round(sum(pcts) / len(pcts), 1) if pcts else None
        summary["total_contracted"] = round(sum(r.contracted_rate for r in matched), 2)
        summary["total_medicare"] = round(sum(r.medicare_rate for r in matched), 2)
        summary["total_variance"] = round(summary["total_contracted"] - summary["total_medicare"], 2)
        summary["below_medicare"] = len([r for r in matched if (r.pct_of_medicare or 0) < 100])
        summary["above_medicare"] = len([r for r in matched if (r.pct_of_medicare or 0) >= 100])
        # Volume-weighted average
        with_vol = [r for r in matched if r.national_volume and r.national_volume > 0 and r.pct_of_medicare]
        if with_vol:
            weighted = sum(r.pct_of_medicare * r.national_volume for r in with_vol)
            total_vol = sum(r.national_volume for r in with_vol)
            summary["volume_weighted_pct"] = round(weighted / total_vol, 1)
        else:
            summary["volume_weighted_pct"] = None
    summary["matched_count"] = len(matched)
    summary["unmatched_count"] = len(unmatched)

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("report.html")
    return template.render(
        contract=contract,
        practice=practice,
        rates=matched,
        unmatched=unmatched,
        summary=summary,
    )


def generate_report_pdf(contract_id: int, db: Session) -> bytes:
    """Generate PDF report."""
    from weasyprint import HTML
    html_str = generate_report_html(contract_id, db)
    pdf = HTML(string=html_str).write_pdf()
    return pdf
