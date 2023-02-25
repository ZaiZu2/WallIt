"""added enum column to banks table

Revision ID: 984c9fe71fb0
Revises: 62607f52a3e3
Create Date: 2023-02-20 22:30:59.256549

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "984c9fe71fb0"
down_revision = "62607f52a3e3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("banks", schema=None) as batch_op:
        banks_enum = postgresql.ENUM("REVOLUT", "EQUABANK", name="banks_enum")
        banks_enum.create(op.get_bind())
        batch_op.add_column(sa.Column("name_enum", banks_enum, nullable=False))
        batch_op.create_unique_constraint(
            batch_op.f("uq_banks_name_enum"), ["name_enum"]
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("banks", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_banks_name_enum"), type_="unique")
        batch_op.drop_column("name_enum")

    # ### end Alembic commands ###
