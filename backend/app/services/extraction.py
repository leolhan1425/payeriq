"""Claude API PDF extraction service."""
import base64
import json
import logging

import anthropic
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.contract import Contract, ContractStatus
from app.models.contract_rate import ContractRate

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are analyzing a medical payer contract PDF. Extract all reimbursement rates from this document.

For each rate you find, extract:
- cpt_code: The CPT/HCPCS procedure code (e.g. "99213", "99214")
- description: Brief description of the procedure
- modifier: Any modifier codes (e.g. "26", "TC"), or null if none
- contracted_rate: The dollar amount the payer will reimburse

Return ONLY a JSON array of objects with these fields. Example:
[
  {"cpt_code": "99213", "description": "Office visit, established patient, low complexity", "modifier": null, "contracted_rate": 95.50},
  {"cpt_code": "99214", "description": "Office visit, established patient, moderate complexity", "modifier": null, "contracted_rate": 142.00}
]

If you find percentage-of-Medicare rates (e.g. "110% of Medicare"), note them but still try to find any specific dollar amounts.
If no specific rates are found, return an empty array [].
Return ONLY the JSON array, no other text."""


def extract_rates_from_pdf(contract_id: int) -> None:
    """Background task: send contract PDF to Claude and parse extracted rates."""
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
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64},
                        },
                        {"type": "text", "text": EXTRACTION_PROMPT},
                    ],
                }
            ],
        )

        # Parse response
        response_text = message.content[0].text.strip()
        # Strip markdown fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

        rates_data = json.loads(response_text)

        for item in rates_data:
            rate = ContractRate(
                contract_id=contract.id,
                cpt_code=str(item["cpt_code"]).strip(),
                description=item.get("description"),
                modifier=item.get("modifier"),
                contracted_rate=float(item["contracted_rate"]),
            )
            db.add(rate)

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
