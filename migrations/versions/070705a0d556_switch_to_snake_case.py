"""switch to snake_case

Revision ID: 070705a0d556
Revises: df13f865dc70
Create Date: 2022-06-26 10:03:22.723853

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "070705a0d556"
down_revision = "df13f865dc70"
branch_labels = None
depends_on = None

naming_convention = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s_%(column_0_name)s",
}


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column("categories", sa.Column("user_id", sa.Integer(), nullable=False))
    with op.batch_alter_table(
        "categories", naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_categories_userId_users", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_categories_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
    op.drop_column("categories", "userId")

    op.add_column("transactions", sa.Column("src_amount", sa.Float(), nullable=True))
    op.add_column("transactions", sa.Column("src_currency", sa.Text(), nullable=True))
    op.add_column(
        "transactions", sa.Column("transaction_date", sa.DateTime(), nullable=False)
    )
    op.add_column("transactions", sa.Column("category_id", sa.Integer(), nullable=True))
    op.add_column("transactions", sa.Column("user_id", sa.Integer(), nullable=False))
    op.add_column("transactions", sa.Column("bank_id", sa.Integer(), nullable=False))
    op.drop_index("ix_transactions_categoryId", table_name="transactions")
    op.drop_index("ix_transactions_transactionDate", table_name="transactions")
    op.create_index(
        op.f("ix_transactions_category_id"),
        "transactions",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_transaction_date"),
        "transactions",
        ["transaction_date"],
        unique=False,
    )
    with op.batch_alter_table(
        "transactions", naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_transactions_categoryId_categories", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_transactions_category_id_categories",
            "categories",
            ["category_id"],
            ["id"],
        )

        batch_op.drop_constraint("fk_transactions_bankId_banks", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_transactions_bank_id_banks", "banks", ["bank_id"], ["id"]
        )

        batch_op.drop_constraint("fk_transactions_userId_users", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_transactions_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.drop_column("transactions", "bankId")
    op.drop_column("transactions", "userId")
    op.drop_column("transactions", "srcAmount")
    op.drop_column("transactions", "srcCurrency")
    op.drop_column("transactions", "transactionDate")
    op.drop_column("transactions", "categoryId")

    op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=False))
    op.add_column("users", sa.Column("first_name", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.Text(), nullable=True))
    op.drop_column("users", "firstName")
    op.drop_column("users", "lastName")
    op.drop_column("users", "passwordHash")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "categories",
        sa.Column("userId", sa.Integer(), autoincrement=False, nullable=False),
    )
    with op.batch_alter_table(
        "categories", naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_categories_user_id_users", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_categories_userId_users",
            "users",
            ["userId"],
            ["id"],
            ondelete="CASCADE",
        )
    op.drop_column("categories", "user_id")

    op.add_column(
        "transactions",
        sa.Column("categoryId", sa.Integer(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column(
            "transactionDate",
            sa.DateTime(),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "transactions",
        sa.Column("srcCurrency", sa.Text(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column(
            "srcAmount",
            sa.Float(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "transactions",
        sa.Column("userId", sa.Integer(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "transactions",
        sa.Column("bankId", sa.Integer(), autoincrement=False, nullable=False),
    )
    with op.batch_alter_table(
        "transactions", naming_convention=naming_convention
    ) as batch_op:
        batch_op.drop_constraint("fk_transactions_bank_id_banks", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_transactions_bankId_banks", "banks", ["bankId"], ["id"]
        )

        batch_op.drop_constraint("fk_transactions_user_id_users", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_transactions_userId_users",
            "users",
            ["userId"],
            ["id"],
            ondelete="CASCADE",
        )

        batch_op.drop_constraint(
            "fk_transactions_category_id_categories", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_transactions_categoryId_categories",
            "categories",
            ["categoryId"],
            ["id"],
        )
    op.drop_index(op.f("ix_transactions_transaction_date"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_category_id"), table_name="transactions")
    op.create_index(
        "ix_transactions_transactionDate",
        "transactions",
        ["transactionDate"],
        unique=False,
    )
    op.create_index(
        "ix_transactions_categoryId", "transactions", ["categoryId"], unique=False
    )
    op.drop_column("transactions", "bank_id")
    op.drop_column("transactions", "user_id")
    op.drop_column("transactions", "category_id")
    op.drop_column("transactions", "transaction_date")
    op.drop_column("transactions", "src_currency")
    op.drop_column("transactions", "src_amount")

    op.add_column(
        "users",
        sa.Column("passwordHash", sa.Text(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "users", sa.Column("lastName", sa.Text(), autoincrement=False, nullable=True)
    )
    op.add_column(
        "users", sa.Column("firstName", sa.Text(), autoincrement=False, nullable=True)
    )
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
    op.drop_column("users", "password_hash")
    # ### end Alembic commands ###
