"""make an update in schemas in notificatio model

Revision ID: 4c86b601e842
Revises: 3252637191ec
Create Date: 2024-10-14 11:44:20.770005

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4c86b601e842'
down_revision = '3252637191ec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('read_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_notifications_user_id'), ['user_id'], unique=False)
        batch_op.create_foreign_key(None, 'projects', ['project_id'], ['id'])
        batch_op.drop_column('is_read')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_read', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_notifications_user_id'))
        batch_op.drop_column('project_id')
        batch_op.drop_column('read_at')

    # ### end Alembic commands ###
