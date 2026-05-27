# migrations/script.py.mako
"""add is_flagged to user

Revision ID: 166bc46d87af
Revises: 0002
Create Date: 2026-05-26 22:24:56.917903

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '166bc46d87af'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_flagged', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'is_flagged')
