"""restructured transaction, main_currency moved to user

Revision ID: d81eefc58af9
Revises: 3f0d65263524
Create Date: 2022-06-30 21:21:42.513411

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d81eefc58af9"
down_revision = "3f0d65263524"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column(
            "base_amount",
            existing_type=sa.Float(),
            nullable=False,
        )
        batch_op.alter_column(
            "base_currency",
            existing_type=sa.VARCHAR(length=3),
            nullable=False,
        )
        batch_op.create_index(
            op.f("ix_transactions_base_amount"),
            ["base_amount"],
            unique=False,
        )
        batch_op.create_index(
            op.f("ix_transactions_base_currency"),
            ["base_currency"],
            unique=False,
        )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_index(op.f("ix_transactions_base_currency"))
        batch_op.drop_index(op.f("ix_transactions_base_amount"))
        batch_op.alter_column(
            "base_currency",
            existing_type=sa.VARCHAR(length=3),
            nullable=True,
        )
        batch_op.alter_column(
            "base_amount",
            existing_type=sa.Float(),
            nullable=True,
        )
    # ### end Alembic commands ###
