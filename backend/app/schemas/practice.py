from pydantic import BaseModel


class PracticeCreate(BaseModel):
    name: str
    zip_code: str


class PracticeResponse(BaseModel):
    id: int
    name: str
    zip_code: str
    gpci_locality: str | None

    model_config = {"from_attributes": True}
