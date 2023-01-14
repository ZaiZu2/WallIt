"""added missing unique constraint on exchange_rates table

Revision ID: 62607f52a3e3
Revises: df4f5af70ed4
Create Date: 2022-12-31 14:19:29.020554

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "62607f52a3e3"
down_revision = "df4f5af70ed4"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("exchange_rates", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_exchange_rates_date"), ["date", "source", "rate"]
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("exchange_rates", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_exchange_rates_date"), type_="unique")

    # ### end Alembic commands ###
