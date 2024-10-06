"""Add soft delete fields to Project model

Revision ID: d7b929bee3c4
Revises: a8f92d5fbce7
Create Date: 2024-10-06 11:11:31.592991

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'd7b929bee3c4'
down_revision = 'a8f92d5fbce7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), nullable=False))
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.alter_column('status',
               existing_type=mysql.ENUM('DRAFT', 'PENDING', 'ACTIVE', 'FUNDED', 'COMPLETED', 'CANCELLEED'),
               type_=sa.Enum('DRAFT', 'PENDING', 'ACTIVE', 'FUNDED', 'COMPLETED', 'CANCELLED', name='projectstatus'),
               existing_nullable=True,
               existing_server_default=sa.text("'DRAFT'"))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.Enum('DRAFT', 'PENDING', 'ACTIVE', 'FUNDED', 'COMPLETED', 'CANCELLED', name='projectstatus'),
               type_=mysql.ENUM('DRAFT', 'PENDING', 'ACTIVE', 'FUNDED', 'COMPLETED', 'CANCELLEED'),
               existing_nullable=True,
               existing_server_default=sa.text("'DRAFT'"))
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('is_deleted')

    # ### end Alembic commands ###
