from sqlalchemy import String, Integer, Float, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContractRate(Base):
    __tablename__ = "contract_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"))
    cpt_code: Mapped[str] = mapped_column(String(10), index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    modifier: Mapped[str | None] = mapped_column(String(10), nullable=True)
    contracted_rate: Mapped[float] = mapped_column(Float)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Comparison results (filled after comparison)
    medicare_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    variance: Mapped[float | None] = mapped_column(Float, nullable=True)
    pct_of_medicare: Mapped[float | None] = mapped_column(Float, nullable=True)

    contract: Mapped["Contract"] = relationship(back_populates="rates")
