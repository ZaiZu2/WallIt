"""added categories TABLE, DELETE CASCADE on transactions

Revision ID: 28e803e18927
Revises: 874b0ebea9e4
Create Date: 2022-06-24 17:10:45.970115

"""
from alembic import op
import sqlalchemy as sa

# import debugpy

# debugpy.listen(5680)
# print("Waiting for debugger attach")
# debugpy.wait_for_client()
# debugpy.breakpoint()
# print('break on this line')


# revision identifiers, used by Alembic.
revision = "28e803e18927"
down_revision = "874b0ebea9e4"
branch_labels = None
depends_on = None

naming_convention = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s_%(column_0_name)s",
}


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("userId", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["userId"],
            ["users.id"],
            name="fk_categories_userId_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table(
        "transactions", naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_transactions_userId_users", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_transactions_userId_users",
            "users",
            ["userId"],
            ["id"],
            ondelete="CASCADE",
        )

    op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table(
        "transactions", naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_transactions_userId_users", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_transactions_userId_users", "users", ["userId"], ["id"]
        )

    op.drop_index(op.f("ix_categories_name"))
    op.drop_table("categories")
    ### end Alembic commands ###
