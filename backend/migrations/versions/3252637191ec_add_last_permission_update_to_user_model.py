"""Add last_permission_update to User model

Revision ID: 3252637191ec
Revises: 75985e0c1f8d
Create Date: 2024-10-13 11:47:13.755082

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3252637191ec'
down_revision = '75985e0c1f8d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_permission_update', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_permission_update')

    # ### end Alembic commands ###
