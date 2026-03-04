"""Negotiation letter generator — Claude-powered."""
import logging

import anthropic
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.contract import Contract
from app.models.contract_rate import ContractRate
from app.models.practice import Practice

logger = logging.getLogger(__name__)

LETTER_SYSTEM_PROMPT = """You are an expert healthcare contract negotiation consultant.
Write professional, data-driven negotiation letters for physician practices seeking
rate increases from insurance payers. Be assertive but respectful. Cite specific CPT
codes and dollar gaps. The tone should be collaborative ("we'd like to schedule a
meeting to discuss") rather than confrontational."""

LETTER_TEMPLATE = """Write a negotiation letter and talking points for the following contract situation.

**Practice**: {practice_name} ({specialty})
**Payer**: {payer_name}
**Contract dates**: {effective_date} to {expiration_date}
**Fee schedule type**: {fee_schedule_type}
{medicare_pct_line}

**Top underpaid CPT codes (below Medicare):**
{underpaid_table}

**Contract term concerns:**
{term_concerns}

Please return a JSON object with exactly two fields:
{{
  "letter": "Full text of a professional negotiation letter addressed to the payer, from the practice. 1-2 pages. Cite specific CPT codes, dollar gaps, and Medicare benchmarks. Request a rate review meeting.",
  "talking_points": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"]
}}

The talking_points should be 5-7 concise bullets suitable for phone conversations.
Return ONLY the JSON object."""


def generate_negotiation_letter(contract_id: int, db: Session) -> dict:
    """Generate a negotiation letter and talking points for a contract."""
    contract = db.get(Contract, contract_id)
    if not contract:
        raise ValueError("Contract not found")

    practice = db.get(Practice, contract.practice_id)
    if not practice:
        raise ValueError("Practice not found")

    # Get top 10 underpaid codes (most negative variance first)
    underpaid = sorted(
        [r for r in contract.rates if r.variance is not None and r.variance < 0],
        key=lambda r: r.variance,
    )[:10]

    if not underpaid:
        return {
            "letter": "All extracted rates meet or exceed Medicare benchmarks. No negotiation letter is needed at this time.",
            "talking_points": ["All rates are at or above Medicare — this is a well-paying contract."],
        }

    # Build underpaid table
    lines = []
    for r in underpaid:
        pct_str = f"{r.pct_of_medicare}%" if r.pct_of_medicare else "N/A"
        lines.append(
            f"- CPT {r.cpt_code}: Contract ${r.contracted_rate:.2f} vs Medicare ${r.medicare_rate:.2f} "
            f"(gap: ${abs(r.variance):.2f}, {pct_str} of Medicare)"
        )
    underpaid_table = "\n".join(lines)

    # Build term concerns
    concerns = []
    if contract.unilateral_amendment:
        concerns.append("- Payer has unilateral amendment rights (can change terms without your consent)")
    if contract.lesser_of_clause:
        concerns.append("- Lesser-of clause (pays the lower of billed charges or fee schedule)")
    if contract.timely_filing_days and contract.timely_filing_days < 90:
        concerns.append(f"- Short timely filing window: {contract.timely_filing_days} days")
    if contract.auto_renewal:
        notice = f" ({contract.termination_notice_days}-day notice required)" if contract.termination_notice_days else ""
        concerns.append(f"- Auto-renewal clause{notice}")
    term_concerns = "\n".join(concerns) if concerns else "None identified"

    # Format dates
    eff = str(contract.effective_date) if contract.effective_date else "Unknown"
    exp = str(contract.expiration_date) if contract.expiration_date else "Unknown"
    fst = contract.fee_schedule_type or "Unknown"
    specialty = practice.specialty or "General Practice"

    medicare_pct_line = ""
    if contract.medicare_percentage:
        medicare_pct_line = f"**Stated Medicare percentage**: {contract.medicare_percentage}%"

    prompt = LETTER_TEMPLATE.format(
        practice_name=practice.name,
        specialty=specialty,
        payer_name=contract.payer_name,
        effective_date=eff,
        expiration_date=exp,
        fee_schedule_type=fst,
        medicare_pct_line=medicare_pct_line,
        underpaid_table=underpaid_table,
        term_concerns=term_concerns,
    )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=LETTER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()
    # Strip markdown fences
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

    import json
    result = json.loads(response_text)
    return {
        "letter": result.get("letter", ""),
        "talking_points": result.get("talking_points", []),
    }
