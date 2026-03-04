"""Claude API PDF extraction service — two-pass: metadata + fee schedule."""
import base64
import json
import logging
from datetime import date

import anthropic
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.contract import Contract, ContractStatus
from app.models.contract_rate import ContractRate

logger = logging.getLogger(__name__)

METADATA_PROMPT = """You are analyzing a medical payer contract PDF. Extract the contract metadata.

Return ONLY a JSON object with these fields:
{
  "payer_name": "string — the insurance company / payer name",
  "effective_date": "YYYY-MM-DD or null",
  "expiration_date": "YYYY-MM-DD or null",
  "fee_schedule_type": "flat_fee" | "percent_of_medicare" | "unknown",
  "medicare_percentage": number or null (e.g. 110 for 110% of Medicare, only if fee_schedule_type is percent_of_medicare),
  "auto_renewal": true/false/null,
  "unilateral_amendment": true/false/null (can the payer change terms without provider consent?),
  "termination_notice_days": integer or null (days of notice required to terminate),
  "lesser_of_clause": true/false/null (does contract pay the lesser of billed charges vs fee schedule?),
  "timely_filing_days": integer or null (deadline in days for claim submission),
  "confidence": 0.0 to 1.0 (your overall confidence in this extraction)
}

If a field is not found in the document, use null.
Return ONLY the JSON object, no other text."""

EXTRACTION_PROMPT = """You are analyzing a medical payer contract PDF. Extract all reimbursement rates from this document.

For each rate you find, extract:
- cpt_code: The CPT/HCPCS procedure code (e.g. "99213", "99214")
- description: Brief description of the procedure
- modifier: Any modifier codes (e.g. "26", "TC"), or null if none
- contracted_rate: The dollar amount the payer will reimburse
- confidence: Your confidence in this extraction (0.0 to 1.0)

Important notes on rate types:
- If the contract specifies PERCENTAGE OF MEDICARE (e.g. "110% of Medicare"), and lists specific dollar amounts calculated from that percentage, extract those dollar amounts.
- If it only says "X% of Medicare" without listing dollar amounts, extract rates as 0.0 and note the percentage in the description (e.g. "110% of Medicare - E/M visit").
- For flat-fee schedules, extract the listed dollar amounts directly.

Return ONLY a JSON array of objects. Example:
[
  {"cpt_code": "99213", "description": "Office visit, established, low complexity", "modifier": null, "contracted_rate": 95.50, "confidence": 0.95},
  {"cpt_code": "99214", "description": "Office visit, established, moderate complexity", "modifier": null, "contracted_rate": 142.00, "confidence": 0.90}
]

If no specific rates are found, return an empty array [].
Return ONLY the JSON array, no other text."""


def _call_claude(client: anthropic.Anthropic, pdf_b64: str, prompt: str, max_tokens: int = 4096) -> str:
    """Send PDF to Claude and return response text."""
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return message.content[0].text.strip()


def _parse_json(text: str):
    """Parse JSON from Claude response, stripping markdown fences if present."""
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return json.loads(text)


def _safe_date(val) -> date | None:
    """Parse a date string, returning None on failure."""
    if not val:
        return None
    try:
        return date.fromisoformat(str(val))
    except (ValueError, TypeError):
        return None


def extract_rates_from_pdf(contract_id: int) -> None:
    """Background task: two-pass extraction — metadata then fee schedule."""
    db: Session = SessionLocal()
    try:
        contract = db.get(Contract, contract_id)
        if not contract:
            return

        # Read PDF file
        with open(contract.file_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        # --- Pass 1: Metadata extraction ---
        meta_text = _call_claude(client, pdf_b64, METADATA_PROMPT)
        meta = _parse_json(meta_text)

        # Store contract terms
        contract.effective_date = _safe_date(meta.get("effective_date"))
        contract.expiration_date = _safe_date(meta.get("expiration_date"))
        contract.fee_schedule_type = meta.get("fee_schedule_type")
        contract.medicare_percentage = meta.get("medicare_percentage")
        contract.auto_renewal = meta.get("auto_renewal")
        contract.unilateral_amendment = meta.get("unilateral_amendment")
        contract.termination_notice_days = meta.get("termination_notice_days")
        contract.lesser_of_clause = meta.get("lesser_of_clause")
        contract.timely_filing_days = meta.get("timely_filing_days")
        contract.extraction_confidence = meta.get("confidence")

        # Keep user-entered payer name (trust user input over extraction)

        # --- Pass 2: Fee schedule extraction ---
        rates_text = _call_claude(client, pdf_b64, EXTRACTION_PROMPT, max_tokens=8192)
        rates_data = _parse_json(rates_text)

        for item in rates_data:
            rate = ContractRate(
                contract_id=contract.id,
                cpt_code=str(item["cpt_code"]).strip(),
                description=item.get("description"),
                modifier=item.get("modifier"),
                contracted_rate=float(item["contracted_rate"]),
                extraction_confidence=item.get("confidence"),
            )
            db.add(rate)

        # Store raw extraction results
        contract.raw_extraction = json.dumps({"metadata": meta, "rates": rates_data})

        contract.status = ContractStatus.review
        db.commit()

    except Exception as e:
        logger.exception("Extraction failed for contract %s", contract_id)
        contract = db.get(Contract, contract_id)
        if contract:
            contract.status = ContractStatus.error
            contract.error_message = str(e)[:500]
            db.commit()
    finally:
        db.close()
