"""enable pgvector extension

Revision ID: 523ea05134fd
Revises: 1a31ce608336
Create Date: 2025-11-05 18:05:37.472970

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '523ea05134fd'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    # Enable pgvector extension for vector similarity search
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')


def downgrade():
    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector')
