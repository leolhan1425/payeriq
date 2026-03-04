from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, practices, contracts, rates, reports, medicare, negotiation
from app.core.config import settings

app = FastAPI(title="PayerIQ", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(practices.router, prefix="/api/practices", tags=["practices"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["contracts"])
app.include_router(rates.router, prefix="/api/rates", tags=["rates"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(medicare.router, prefix="/api/medicare", tags=["medicare"])
app.include_router(negotiation.router, prefix="/api/negotiation", tags=["negotiation"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
