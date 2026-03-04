"""Medicare rate comparison engine."""
from sqlalchemy.orm import Session

from app.models.contract import Contract, ContractStatus
from app.models.contract_rate import ContractRate
from app.models.practice import Practice
from app.models.medicare import (
    MedicareRate, GPCILocality, LabFeeSchedule, Utilization, CommercialBenchmark,
    CONVERSION_FACTOR,
)


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
    """Compare all rates in a contract against Medicare benchmarks.

    Uses PFS (physician fee schedule) as primary benchmark. Falls back to
    CLFS (clinical lab fee schedule) for lab codes with $0 PFS rate.
    Enriches with national utilization data for volume-weighted analysis.
    """
    contract = db.get(Contract, contract_id)
    if not contract:
        raise ValueError("Contract not found")

    practice = db.get(Practice, contract.practice_id)
    if not practice or not practice.gpci_locality:
        raise ValueError("Practice has no GPCI locality set")

    # Look up GPCI by MAC/carrier + locality number
    gpci_query = db.query(GPCILocality).filter(GPCILocality.locality_number == practice.gpci_locality)
    if practice.gpci_carrier:
        gpci_query = gpci_query.filter(GPCILocality.mac == practice.gpci_carrier)
    gpci = gpci_query.first()
    if not gpci:
        raise ValueError(f"GPCI data not found for carrier={practice.gpci_carrier} locality={practice.gpci_locality}")

    results = {"matched": 0, "unmatched": 0, "total_variance": 0.0}

    for rate in contract.rates:
        # Try PFS first
        rvu = db.query(MedicareRate).filter(MedicareRate.cpt_code == rate.cpt_code).first()
        medicare_rate = 0.0
        source = None

        if rvu:
            medicare_rate = calculate_medicare_rate(rvu, gpci, facility=False)
            source = "PFS"

        # If PFS rate is $0, try CLFS (lab codes)
        if medicare_rate == 0.0:
            lab = db.query(LabFeeSchedule).filter(LabFeeSchedule.cpt_code == rate.cpt_code).first()
            if lab and lab.rate > 0:
                medicare_rate = lab.rate
                source = "CLFS"

        if not rvu and source is None:
            results["unmatched"] += 1
            continue

        if medicare_rate > 0:
            variance = rate.contracted_rate - medicare_rate
            pct = (rate.contracted_rate / medicare_rate) * 100
        else:
            variance = rate.contracted_rate
            pct = None

        rate.medicare_rate = round(medicare_rate, 2)
        rate.variance = round(variance, 2)
        rate.pct_of_medicare = round(pct, 1) if pct else None
        rate.benchmark_source = source

        # Enrich with utilization data
        util = db.query(Utilization).filter(Utilization.cpt_code == rate.cpt_code).first()
        if util:
            rate.national_volume = util.total_services
            rate.national_avg_allowed = util.avg_allowed

        # Commercial benchmark
        commercial = db.query(CommercialBenchmark).filter(
            CommercialBenchmark.cpt_code == rate.cpt_code
        ).first()
        if commercial and commercial.avg_rate > 0:
            rate.commercial_avg_rate = round(commercial.avg_rate, 2)
            rate.pct_of_commercial = round(
                (rate.contracted_rate / commercial.avg_rate) * 100, 1
            )

        results["matched"] += 1
        results["total_variance"] += variance

    contract.status = ContractStatus.compared
    db.commit()

    # Compute summary stats
    matched_rates = [r for r in contract.rates if r.pct_of_medicare is not None]
    results["avg_pct_of_medicare"] = None
    if matched_rates:
        results["avg_pct_of_medicare"] = round(
            sum(r.pct_of_medicare for r in matched_rates) / len(matched_rates), 1
        )

    # Volume-weighted average (if utilization data available)
    rates_with_vol = [r for r in matched_rates if r.national_volume and r.national_volume > 0]
    if rates_with_vol:
        weighted_sum = sum(r.pct_of_medicare * r.national_volume for r in rates_with_vol)
        total_vol = sum(r.national_volume for r in rates_with_vol)
        results["volume_weighted_pct"] = round(weighted_sum / total_vol, 1)
    else:
        results["volume_weighted_pct"] = None

    # --- Estimated annual revenue impact ---
    # For each rate below Medicare with utilization data, estimate the annual
    # dollar gap. Scale factor approximates a typical practice's share of
    # national volume (solo ~1/10000, small group ~1/5000).
    scale_factor = 1 / 10000  # conservative solo-practice default
    annual_impact = 0.0
    for r in matched_rates:
        if r.variance and r.variance < 0 and r.national_volume and r.national_volume > 0:
            annual_impact += abs(r.variance) * r.national_volume * scale_factor
    results["estimated_annual_impact"] = round(annual_impact, 2) if annual_impact > 0 else None

    return results
