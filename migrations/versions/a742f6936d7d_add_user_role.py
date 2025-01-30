"""add user role

Revision ID: a742f6936d7d
Revises: cf323191e928
Create Date: 2025-01-30 16:31:11.977928

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision: str = "a742f6936d7d"
down_revision: Union[str, None] = "cf323191e928"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define ENUM type for PostgreSQL
userrole_enum = ENUM("USER", "ADMIN", name="userrole", create_type=True)


def upgrade() -> None:
    # Explicitly create the ENUM type first
    userrole_enum.create(op.get_bind())

    # Now add the 'role' column using the ENUM
    op.add_column(
        "users", sa.Column("role", userrole_enum, nullable=False, server_default="USER")
    )


def downgrade() -> None:
    # Remove the 'role' column first
    op.drop_column("users", "role")

    # Then drop the ENUM type
    userrole_enum.drop(op.get_bind())
