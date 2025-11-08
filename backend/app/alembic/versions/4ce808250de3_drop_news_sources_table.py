"""Drop news_sources table

Revision ID: 4ce808250de3
Revises: 7b5594e385cc
Create Date: 2025-11-07 00:42:08.563760

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '4ce808250de3'
down_revision = '7b5594e385cc'
branch_labels = None
depends_on = None


def upgrade():
    # Drop news_sources table as sources are now configured in settings
    op.drop_table('news_sources')


def downgrade():
    # Recreate news_sources table for rollback
    op.create_table(
        'news_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('rss_url', sa.String(length=2048), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_ingestion_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.String(length=1000), nullable=True),
        sa.Column('ingestion_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('rss_url')
    )
    op.create_index('ix_news_sources_is_active', 'news_sources', ['is_active'])
    op.create_index('ix_news_sources_name', 'news_sources', ['name'])
