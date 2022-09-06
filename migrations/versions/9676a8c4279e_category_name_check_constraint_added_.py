"""category name check constraint added, category unique constraint renamed

Revision ID: 9676a8c4279e
Revises: a7dde7b63243
Create Date: 2022-09-06 22:38:56.628536

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9676a8c4279e"
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
            CHECK (name <> '' AND name ~ '^[\u00BF-\u1FFF\u2C00-\uD7FF\w]+$')
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
