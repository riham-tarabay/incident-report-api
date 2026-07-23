"""add resolution_notes column to incidents

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("incidents", sa.Column("resolution_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    # batch_alter_table is required for DROP COLUMN support on SQLite.
    with op.batch_alter_table("incidents") as batch_op:
        batch_op.drop_column("resolution_notes")
