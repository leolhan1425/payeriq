"""Medicare rate comparison engine."""
from sqlalchemy.orm import Session

from app.models.contract import Contract, ContractStatus
from app.models.contract_rate import ContractRate
from app.models.practice import Practice
from app.models.medicare import MedicareRate, GPCILocality, CONVERSION_FACTOR


def calculate_medicare_rate(
    rvu: MedicareRate,
    gpci: GPCILocality,
    facility: bool = False,
) -> float:
    """Calculate GPCI-adjusted Medicare rate.

    Formula: [(Work RVU × Work GPCI) + (PE RVU × PE GPCI) + (MP RVU × MP GPCI)] × CF
    """
    pe_rvu = rvu.pe_rvu_facility if facility else rvu.pe_rvu_nonfacility
    return (
        (rvu.work_rvu * gpci.work_gpci)
        + (pe_rvu * gpci.pe_gpci)
        + (rvu.mp_rvu * gpci.mp_gpci)
    ) * CONVERSION_FACTOR


def compare_contract_rates(contract_id: int, db: Session) -> dict:
    """Compare all rates in a contract against Medicare benchmarks."""
    contract = db.get(Contract, contract_id)
    if not contract:
        raise ValueError("Contract not found")

    practice = db.get(Practice, contract.practice_id)
    if not practice or not practice.gpci_locality:
        raise ValueError("Practice has no GPCI locality set")

    gpci = (
        db.query(GPCILocality)
        .filter(GPCILocality.locality_number == practice.gpci_locality)
        .first()
    )
    if not gpci:
        raise ValueError(f"GPCI data not found for locality {practice.gpci_locality}")

    results = {"matched": 0, "unmatched": 0, "total_variance": 0.0, "rates": []}

    for rate in contract.rates:
        rvu = (
            db.query(MedicareRate)
            .filter(MedicareRate.cpt_code == rate.cpt_code)
            .first()
        )
        if not rvu:
            results["unmatched"] += 1
            continue

        medicare_rate = calculate_medicare_rate(rvu, gpci, facility=False)
        if medicare_rate > 0:
            variance = rate.contracted_rate - medicare_rate
            pct = (rate.contracted_rate / medicare_rate) * 100
        else:
            variance = rate.contracted_rate
            pct = None

        rate.medicare_rate = round(medicare_rate, 2)
        rate.variance = round(variance, 2)
        rate.pct_of_medicare = round(pct, 1) if pct else None
        results["matched"] += 1
        results["total_variance"] += variance

    contract.status = ContractStatus.compared
    db.commit()

    results["avg_pct_of_medicare"] = None
    matched_rates = [r for r in contract.rates if r.pct_of_medicare is not None]
    if matched_rates:
        results["avg_pct_of_medicare"] = round(
            sum(r.pct_of_medicare for r in matched_rates) / len(matched_rates), 1
        )

    return results
