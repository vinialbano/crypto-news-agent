"""add_hnsw_index_to_news_articles

Adds HNSW (Hierarchical Navigable Small World) index to news_articles.embedding
column for improved semantic search performance.

HNSW provides:
- Better query performance than sequential scan
- No training data required (unlike IVFFlat)
- Accurate results for small-to-medium datasets
- Suitable for dynamic data with frequent inserts

Revision ID: 7b5594e385cc
Revises: 56dd3eeeadae
Create Date: 2025-11-06 18:03:36.683130

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '7b5594e385cc'
down_revision = '56dd3eeeadae'
branch_labels = None
depends_on = None


def upgrade():
    """Create HNSW index on news_articles.embedding column.

    Note: Not using CONCURRENTLY for initial migration since table is empty.
    For production migrations on populated tables, use CONCURRENTLY option
    and run migration with connection.execution_options(isolation_level="AUTOCOMMIT").
    """
    # Create HNSW index using pgvector's vector_cosine_ops
    op.create_index(
        "idx_news_articles_embedding_hnsw",
        "news_articles",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade():
    """Drop HNSW index from news_articles.embedding column."""
    op.drop_index(
        "idx_news_articles_embedding_hnsw",
        table_name="news_articles",
    )
