"""category name check constraint added, category unique constraint renamed

Revision ID: b4586bacf2a4
Revises: a7dde7b63243
Create Date: 2022-09-07 20:43:13.964691

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b4586bacf2a4"
down_revision = "a7dde7b63243"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("unique_category", "categories", type_="unique")
    op.create_unique_constraint(
        "unique_user_category_key", "categories", ["name", "user_id"]
    )
    # ### end Alembic commands ###

    # Manually created CHECK constraint
    op.execute(
        """
        ALTER TABLE categories
            ADD CONSTRAINT single_word_name_check
            CHECK (name ~ '^[\u00BF-\u1FFF\u2C00-\uD7FF\w]+$')
            NO INHERIT;
        """
    )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("unique_user_category_key", "categories", type_="unique")
    op.create_unique_constraint("unique_category", "categories", ["name", "user_id"])
    # ### end Alembic commands ###

    # Manually created CHECK constraint
    op.execute("ALTER TABLE ONLY categories DROP CONSTRAINT single_word_name_check;")