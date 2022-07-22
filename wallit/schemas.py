from wallit.models import Transaction, User
from wallit import ma

from marshmallow import fields, validate


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        ordered = True

    id = ma.auto_field()
    username = ma.auto_field()
    email = ma.auto_field(validate=validate.Email())
    first_name = ma.auto_field()
    last_name = ma.auto_field()
    main_currency = ma.auto_field(validate=validate.Length(equal=3))


class TransactionSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Transaction
        ordered = True

    id = ma.auto_field()
    info = ma.auto_field()
    title = ma.auto_field()
    main_amount = ma.auto_field()
    base_amount = ma.auto_field(required=True)
    base_currency = ma.auto_field(required=True, validate=validate.Length(equal=3))
    transaction_date = ma.auto_field(required=True)
    creation_date = ma.auto_field(required=True)
    place = ma.auto_field()
    category_name = fields.String()
    bank_name = fields.String()


class FilterSchema(ma.Schema):
    currencies = fields.List(fields.String())
    categories = fields.List(fields.String())
    banks = fields.List(fields.String())
