from typing import Any
from flask_login import current_user
from wallit.models import Bank, Category, Transaction, User
from wallit import ma

from marshmallow import (
    fields,
    post_dump,
    pre_load,
    post_load,
    validate,
    validates_schema,
    ValidationError,
)
from copy import deepcopy


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


class CategorySchema(ma.SQLAlchemySchema):
    class Meta:
        model = Category
        ordered = True

    id = ma.auto_field()
    name = ma.auto_field()
    user = ma.auto_field()


class BankSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Bank
        ordered = True

    id = ma.auto_field()
    name = ma.auto_field()
    statement_type = ma.auto_field()
    transactions = ma.auto_field()


class TransactionSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Transaction
        ordered = True

    id = ma.auto_field()
    info = ma.auto_field()
    title = ma.auto_field()
    amount = ma.auto_field("main_amount")
    base_amount = ma.auto_field(required=True)
    base_currency = ma.auto_field(required=True, validate=validate.Length(equal=3))
    date = ma.auto_field("transaction_date", required=True)
    creation_date = ma.auto_field()
    place = ma.auto_field()
    category = fields.Pluck(CategorySchema, "name", allow_none=True)
    bank = fields.Pluck(BankSchema, "name", allow_none=True)

    @post_load
    def _convert_to_transaction(
        self, data: dict, **kwargs: dict[str, Any]
    ) -> Transaction:
        """Convert nested schema name to foreign key relationships and load into Transaction object"""
        # TODO: Pluck field results in a nested orderedDict (with the Plucked field's key:value) during deserialization.
        # No clue how to avoid this.

        # Modify transaction instance passed in load()
        if self.instance:
            for column_name, value in data.items():
                if issubclass(
                    type(value), dict
                ):  # temporary fix for issue described above
                    category = Category.get_from_name(value["name"], current_user)
                    setattr(self.instance, column_name, category)
                else:
                    setattr(self.instance, column_name, value)
            return self.instance
        # Create a new transaction if no instance was passed
        else:
            category_name = data.get("category")
            del data["category"]
            bank_name = data.get("bank")
            del data["bank"]
            transaction = Transaction(user=current_user, **data)

            if category_name:
                category = Category.get_from_name(
                    category_name["name"], current_user
                )  # temporary fix for issue described above
                transaction.category = category

            if bank_name:
                bank = Bank.get_from_name(
                    bank_name["name"]
                )  # temporary fix for issue described above
                transaction.bank = bank

            return transaction

    @post_dump(pass_many=True)
    def _create_envelope(self, data: dict, **kwargs: dict[str, Any]) -> dict[str, dict]:
        return {"transactions": data}


class TransactionFilterSchema(ma.Schema):
    """Schema used for validation of user-input filtering values"""

    amount = fields.Dict(
        keys=fields.String(allow_none=True), values=fields.Float(allow_none=True)
    )
    date = fields.Dict(
        keys=fields.String(allow_none=True),
        values=fields.DateTime(format="%Y-%m-%d", allow_none=True),
    )
    banks = fields.List(fields.String(), allow_none=True, data_key="bank")
    base_currencies = fields.List(
        fields.String(),
        allow_none=True,
        data_key="base_currency",
        validate=validate.Length(equal=3),
    )
    categories = fields.List(fields.String(), allow_none=True, data_key="category")

    @pre_load
    def _remove_blanks(self, data: dict, **kwargs: dict[str, Any]) -> dict:
        """Replace empty values (strings) with None"""

        cleaned_data = deepcopy(data)
        for key, value in data.items():
            if isinstance(value, dict):
                for nested_key, nested_value in data[key].items():
                    if not nested_value:
                        cleaned_data[key][nested_key] = None
            elif not value:
                cleaned_data[key] = None

        return cleaned_data

    @validates_schema
    def _check_range_filters(self, data: dict, **kwargs: dict[str, Any]) -> None:
        for filter in ["amount", "date"]:
            if (
                data[filter]["min"]
                and data[filter]["max"]
                and data[filter]["min"] > data[filter]["max"]
            ):
                raise ValidationError("Lower end cannot be higher than higher end")


MonthlySaldoSchema = ma.Schema.from_dict(
    {
        "month": fields.DateTime(format="%Y-%m"),
        "incoming": fields.Number(),
        "outgoing": fields.Number(),
        "balance": fields.Number(),
    },
    name="MonthlySaldoSchema",
)
