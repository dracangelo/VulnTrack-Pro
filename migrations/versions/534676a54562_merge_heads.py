"""merge heads

Revision ID: 534676a54562
Revises: 11fc5425d00a, add_report_columns_to_scans
Create Date: 2025-11-27 08:22:59.597923

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '534676a54562'
down_revision = ('11fc5425d00a', 'add_report_columns_to_scans')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
