from pydantic import BaseModel


class ContractResponse(BaseModel):
    id: int
    payer_name: str
    status: str
    error_message: str | None
    practice_id: int

    model_config = {"from_attributes": True}


class ContractRateResponse(BaseModel):
    id: int
    cpt_code: str
    description: str | None
    modifier: str | None
    contracted_rate: float
    is_verified: bool
    medicare_rate: float | None
    variance: float | None
    pct_of_medicare: float | None
    benchmark_source: str | None
    national_volume: int | None
    national_avg_allowed: float | None
    commercial_avg_rate: float | None
    pct_of_commercial: float | None

    model_config = {"from_attributes": True}


class ContractRateUpdate(BaseModel):
    cpt_code: str | None = None
    description: str | None = None
    modifier: str | None = None
    contracted_rate: float | None = None
    is_verified: bool | None = None
