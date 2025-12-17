"""Merge all heads

Revision ID: 3d5c7cf6ff79
Revises: 0fc4b4906b29, 78d59b322323, 9ea88cf14e05, e55fe5ef1616
Create Date: 2025-12-17 23:11:58.228418

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d5c7cf6ff79'
down_revision = ('0fc4b4906b29', '78d59b322323', '9ea88cf14e05', 'e55fe5ef1616')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
