# migrations/versions/0002_create_notes_table.py
"""create notes and tokens tables

Revision ID: 0002
Revises: 0001
Create Date: 2024-05-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Refresh tokens table
    op.execute("""
        CREATE TABLE refresh_tokens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR(255) NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            revoked BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens (user_id);")
    op.execute("CREATE INDEX ix_refresh_tokens_token_hash ON refresh_tokens (token_hash);")

    # Password reset tokens table
    op.execute("""
        CREATE TABLE password_reset_tokens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR(255) NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            used BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    # Notes table
    op.execute("""
        CREATE TABLE notes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR(150) NOT NULL,
            body TEXT NOT NULL,
            tags TEXT[] NOT NULL DEFAULT '{}',
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX ix_notes_user_id ON notes (user_id);")
    op.execute("CREATE INDEX ix_notes_created_at ON notes (created_at);")


def downgrade() -> None:
    op.execute("DROP TABLE notes;")
    op.execute("DROP TABLE password_reset_tokens;")
    op.execute("DROP TABLE refresh_tokens;")
