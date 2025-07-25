"""Change duration column type back to integer

Revision ID: d4a8d0a51711
Revises: a8d2acc63182
Create Date: 2025-06-28 07:47:14.663835

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4a8d0a51711'
down_revision = 'a8d2acc63182'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('entries', schema=None) as batch_op:
        batch_op.drop_column('duration')
        batch_op.add_column(sa.Column('duration', sa.Integer(), nullable=True))

def downgrade():
    with op.batch_alter_table('entries', schema=None) as batch_op:
        batch_op.drop_column('duration')
        batch_op.add_column(sa.Column('duration', sa.DateTime(), nullable=True))


