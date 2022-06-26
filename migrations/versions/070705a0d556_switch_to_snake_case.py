"""switch to snake_case

Revision ID: 070705a0d556
Revises: df13f865dc70
Create Date: 2022-06-26 10:03:22.723853

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "070705a0d556"
down_revision = "df13f865dc70"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("categories", sa.Column("user_id", sa.Integer(), nullable=False))
    op.drop_constraint("categories_userId_fkey", "categories", type_="foreignkey")
    op.create_foreign_key(
        None, "categories", "users", ["user_id"], ["id"], ondelete="CASCADE"
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
    op.drop_constraint(
        "transactions_categoryId_fkey", "transactions", type_="foreignkey"
    )
    op.drop_constraint("transactions_bankId_fkey", "transactions", type_="foreignkey")
    op.drop_constraint("transactions_userId_fkey", "transactions", type_="foreignkey")
    op.create_foreign_key(None, "transactions", "categories", ["category_id"], ["id"])
    op.create_foreign_key(
        None, "transactions", "users", ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(None, "transactions", "banks", ["bank_id"], ["id"])
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
        "users",
        sa.Column("passwordHash", sa.TEXT(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "users", sa.Column("lastName", sa.TEXT(), autoincrement=False, nullable=True)
    )
    op.add_column(
        "users", sa.Column("firstName", sa.TEXT(), autoincrement=False, nullable=True)
    )
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
    op.drop_column("users", "password_hash")
    op.add_column(
        "transactions",
        sa.Column("categoryId", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column(
            "transactionDate",
            postgresql.TIMESTAMP(),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "transactions",
        sa.Column("srcCurrency", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column(
            "srcAmount",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "transactions",
        sa.Column("userId", sa.INTEGER(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "transactions",
        sa.Column("bankId", sa.INTEGER(), autoincrement=False, nullable=False),
    )
    op.drop_constraint(None, "transactions", type_="foreignkey")
    op.drop_constraint(None, "transactions", type_="foreignkey")
    op.drop_constraint(None, "transactions", type_="foreignkey")
    op.create_foreign_key(
        "transactions_userId_fkey",
        "transactions",
        "users",
        ["userId"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "transactions_bankId_fkey", "transactions", "banks", ["bankId"], ["id"]
    )
    op.create_foreign_key(
        "transactions_categoryId_fkey",
        "transactions",
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
        "categories",
        sa.Column("userId", sa.INTEGER(), autoincrement=False, nullable=False),
    )
    op.drop_constraint(None, "categories", type_="foreignkey")
    op.create_foreign_key(
        "categories_userId_fkey",
        "categories",
        "users",
        ["userId"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_column("categories", "user_id")
    # ### end Alembic commands ###
