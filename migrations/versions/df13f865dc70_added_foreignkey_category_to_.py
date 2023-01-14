"""Added ForeignKey(category) to transactions

Revision ID: df13f865dc70
Revises: 28e803e18927
Create Date: 2022-06-24 18:12:38.887854

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "df13f865dc70"
down_revision = "28e803e18927"
branch_labels = None
depends_on = None

naming_convention = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s_%(column_0_name)s",
}


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("transactions", sa.Column("categoryId", sa.Integer(), nullable=True))
    op.drop_index("ix_transactions_category")
    op.create_index(
        "ix_transactions_categoryId", "transactions", ["categoryId"], unique=False
    )

    with op.batch_alter_table(
        "transactions", naming_convention=naming_convention
    ) as batch_op:
        batch_op.create_foreign_key(
            "fk_transactions_categoryId_categories",
            "categories",
            ["categoryId"],
            ["id"],
        )

    op.drop_column("transactions", "category")
    # ### end Alembic commands ###


def downgrade() -> None:
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "transactions",
        sa.Column("category", sa.Text(), autoincrement=False, nullable=True),
    )
    with op.batch_alter_table(
        "transactions", naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_transactions_categoryId_categories", type_="foreignkey"
        )
    op.drop_index(op.f("ix_transactions_categoryId"), table_name="transactions")
    op.create_index(
        "ix_transactions_category", "transactions", ["category"], unique=False
    )
    op.drop_column("transactions", "categoryId")
    ### end Alembic commands ###
