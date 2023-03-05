"""Create groups and confidant table

Revision ID: 029f4742af99
Revises: 7fb069d39bb2
Create Date: 2023-03-05 17:30:00.261422

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '029f4742af99'
down_revision = '7fb069d39bb2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('groups',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('id', name='groups_pkey'),
    )
    op.create_index('ix_groups_id', 'groups', ['id'], unique=True)

    op.create_table('confidants',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('group', sa.INTEGER(), sa.ForeignKey("groups.id", ondelete="CASCADE"),
                                autoincrement=False, nullable=False,),
        sa.Column('user', sa.INTEGER(), sa.ForeignKey("users.id", ondelete="CASCADE"),
                    autoincrement=False, nullable=False,),
        sa.Column('role', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('id', name='confidants_pkey'),
    )
    op.create_index('ix_confidants_id', 'confidants', ['id'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_confidants_id', table_name='confidants')
    op.drop_table('confidants')
    op.drop_index('ix_groups_id', table_name='groups')
    op.drop_table('groups')
    # ### end Alembic commands ###
