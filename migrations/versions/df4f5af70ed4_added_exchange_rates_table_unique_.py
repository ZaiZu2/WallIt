"""added exchange_rates table, unique constraint on users.email and reverted to default names for old unique constraints

Revision ID: df4f5af70ed4
Revises: b4586bacf2a4
Create Date: 2022-12-30 17:08:18.281746

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "df4f5af70ed4"
down_revision = "b4586bacf2a4"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "exchange_rates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("target", sa.String(length=3), nullable=True),
        sa.Column("source", sa.String(length=3), nullable=False),
        sa.Column("rate", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exchange_rates")),
    )
    with op.batch_alter_table("categories", schema=None) as batch_op:
        batch_op.drop_constraint("unique_user_category_key", type_="unique")
        batch_op.create_unique_constraint(
            batch_op.f("uq_categories_name"), ["name", "user_id"]
        )

    # ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table("categories", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_categories_name"), type_="unique")
        batch_op.create_unique_constraint(
            "unique_user_category_key", ["name", "user_id"]
        )

    op.drop_table("exchange_rates")
    # ### end Alembic commands ###
