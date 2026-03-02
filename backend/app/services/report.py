"""Report generation service — HTML + PDF via WeasyPrint."""
import io
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.practice import Practice

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


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
    from weasyprint import HTML  # lazy import — needs system libs (pango)
    html_str = generate_report_html(contract_id, db)
    pdf = HTML(string=html_str).write_pdf()
    return pdf
