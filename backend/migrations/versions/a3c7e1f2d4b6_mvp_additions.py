"""mvp additions

Revision ID: a3c7e1f2d4b6
Revises: 2f1bf95db81c
Create Date: 2026-03-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3c7e1f2d4b6'
down_revision: Union[str, Sequence[str], None] = '2f1bf95db81c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add MVP fields: practice specialty, contract terms, extraction confidence."""
    # Practice specialty
    op.add_column('practices', sa.Column('specialty', sa.String(length=50), nullable=True))

    # Contract term fields
    op.add_column('contracts', sa.Column('effective_date', sa.Date(), nullable=True))
    op.add_column('contracts', sa.Column('expiration_date', sa.Date(), nullable=True))
    op.add_column('contracts', sa.Column('fee_schedule_type', sa.String(length=50), nullable=True))
    op.add_column('contracts', sa.Column('medicare_percentage', sa.Float(), nullable=True))
    op.add_column('contracts', sa.Column('auto_renewal', sa.Boolean(), nullable=True))
    op.add_column('contracts', sa.Column('unilateral_amendment', sa.Boolean(), nullable=True))
    op.add_column('contracts', sa.Column('termination_notice_days', sa.Integer(), nullable=True))
    op.add_column('contracts', sa.Column('lesser_of_clause', sa.Boolean(), nullable=True))
    op.add_column('contracts', sa.Column('timely_filing_days', sa.Integer(), nullable=True))
    op.add_column('contracts', sa.Column('raw_extraction', sa.Text(), nullable=True))
    op.add_column('contracts', sa.Column('extraction_confidence', sa.Float(), nullable=True))

    # Per-rate extraction confidence
    op.add_column('contract_rates', sa.Column('extraction_confidence', sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove MVP fields."""
    op.drop_column('contract_rates', 'extraction_confidence')

    op.drop_column('contracts', 'extraction_confidence')
    op.drop_column('contracts', 'raw_extraction')
    op.drop_column('contracts', 'timely_filing_days')
    op.drop_column('contracts', 'lesser_of_clause')
    op.drop_column('contracts', 'termination_notice_days')
    op.drop_column('contracts', 'unilateral_amendment')
    op.drop_column('contracts', 'auto_renewal')
    op.drop_column('contracts', 'medicare_percentage')
    op.drop_column('contracts', 'fee_schedule_type')
    op.drop_column('contracts', 'expiration_date')
    op.drop_column('contracts', 'effective_date')

    op.drop_column('practices', 'specialty')
