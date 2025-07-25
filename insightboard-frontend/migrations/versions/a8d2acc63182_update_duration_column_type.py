"""Update duration column type

Revision ID: a8d2acc63182
Revises: e9b6bb1bfd84
Create Date: 2025-06-28 07:20:11.597541

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8d2acc63182'
down_revision = 'e9b6bb1bfd84'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('entries', schema=None) as batch_op:
        batch_op.drop_column('duration')
        batch_op.add_column(sa.Column('duration', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('entries', schema=None) as batch_op:
        batch_op.drop_column('duration')
        batch_op.add_column(sa.Column('duration', sa.Integer(), nullable=True))