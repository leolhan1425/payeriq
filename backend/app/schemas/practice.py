from pydantic import BaseModel


class PracticeCreate(BaseModel):
    name: str
    zip_code: str
    specialty: str | None = None


class PracticeResponse(BaseModel):
    id: int
    name: str
    zip_code: str
    gpci_locality: str | None
    specialty: str | None = None

    model_config = {"from_attributes": True}
