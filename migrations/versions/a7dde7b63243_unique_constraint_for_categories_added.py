"""unique constraint for categories added

Revision ID: a7dde7b63243
Revises: 8cb831dd02e6
Create Date: 2022-09-04 20:35:44.431214

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a7dde7b63243"
down_revision = "8cb831dd02e6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint("unique_category", "categories", ["name", "user_id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("unique_category", "categories", type_="unique")
    # ### end Alembic commands ###
