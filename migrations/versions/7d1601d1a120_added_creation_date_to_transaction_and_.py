"""added creation_date to Transaction and statement_type to Bank

Revision ID: 7d1601d1a120
Revises: d81eefc58af9
Create Date: 2022-07-10 11:08:10.070672

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7d1601d1a120"
down_revision = "d81eefc58af9"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    op.add_column(
        "banks", sa.Column("statement_type", sa.String(length=10), nullable=True)
    )
    # Make column not-null
    op.execute("UPDATE banks SET statement_type='.csv' WHERE id=1")
    op.execute("UPDATE banks SET statement_type='.xml' WHERE id=2")
    with op.batch_alter_table("banks") as batch_op:
        batch_op.alter_column("statement_type", nullable=False)

    op.add_column(
        "transactions", sa.Column("creation_date", sa.DateTime(), nullable=True)
    )
    # Make column not-null
    op.execute("UPDATE transactions SET creation_date='2022-07-10 11:10:08'")
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column("creation_date", nullable=False)
        batch_op.create_index(
            op.f("ix_transactions_creation_date"),
            ["creation_date"],
            unique=False,
        )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_transactions_creation_date"), table_name="transactions")
    op.drop_column("transactions", "creation_date")
    op.drop_column("banks", "statement_type")
    # ### end Alembic commands ###
