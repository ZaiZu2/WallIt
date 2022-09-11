from wallit import ma
from wallit.models import Bank, Category, Transaction, User
from wallit.imports import get_currencies

from typing import Any
from flask_login import current_user
from marshmallow import (
    fields,
    post_dump,
    pre_load,
    post_load,
    validate,
    validates_schema,
    ValidationError,
    EXCLUDE,
)
from copy import deepcopy


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        ordered = True

    id = ma.auto_field()
    username = ma.auto_field(
        validate=validate.Regexp(
            "^[A-Za-z0-9]+$",
            error="Username must be a single word consisting of alpha-numeric characters",
        )
    )
    email = ma.auto_field(validate=validate.Email())
    first_name = ma.auto_field(
        validate=validate.Regexp(
            "^[A-Za-z][a-z]*$",
            error="Name must be a single word starting with a capital letter",
        )
    )
    last_name = ma.auto_field(
        validate=validate.Regexp(
            "^[A-Za-z][a-z]*$",
            error="Last name must be a single word starting with a capital letter",
        )
    )
    main_currency = ma.auto_field(
        validate=validate.OneOf(
            get_currencies(), error="Only available currency can be accepted"
        )
    )


class CategorySchema(ma.SQLAlchemySchema):
    class Meta:
        model = Category
        ordered = True

    id = ma.auto_field(dump_only=True)
    name = ma.auto_field(
        validate=validate.Regexp(
            # Single chain of characters/digits
            # with no whitespaces (foreign characters included)
            "^[\u00BF-\u1FFF\u2C00-\uD7FF\w]+$",
            error="Category name must be a single word",
        )
    )


class BankSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Bank
        ordered = True

    id = ma.auto_field(dump_only=True)
    name = ma.auto_field()
    statement_type = ma.auto_field(load_only=True)
    # transactions = ma.auto_field()


class TransactionSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Transaction
        ordered = True

    id = ma.auto_field()
    info = ma.auto_field()
    title = ma.auto_field()
    amount = ma.auto_field("main_amount", required=False)
    base_amount = ma.auto_field(required=True)
    base_currency = ma.auto_field(
        required=True,
        validate=validate.OneOf(get_currencies()),
    )
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
        # TODO: Pluck field results in a nested orderedDict (with the Plucked field's name:value) during deserialization.
        # No clue how to avoid this.

        # Modify transaction instance passed in load()
        if self.instance:
            for column_name, value in data.items():
                # For modified Transactions only Category name can be nested
                if issubclass(type(value), dict):
                    category = Category.get_from_name(value["name"], current_user)
                    setattr(self.instance, column_name, category)
                else:
                    setattr(self.instance, column_name, value)
            return self.instance
        # Create a new transaction if no instance was passed
        else:
            if data["category"]:
                data["category"] = Category.get_from_name(
                    data["category"]["name"], current_user
                )
            if data["bank"]:
                data["bank"] = Bank.get_from_name(data["bank"]["name"])

            return Transaction(user=current_user, **data)

    @post_dump(pass_many=True)
    def _create_envelope(self, data: dict, **kwargs: dict[str, Any]) -> dict[str, dict]:
        return {"transactions": data}


class FilterSchema(ma.Schema):
    """Schema used for validation of user-input filtering values"""

    amount = fields.Dict(
        keys=fields.String(allow_none=True),
        values=fields.Float(allow_none=True),
        load_only=True,
    )
    date = fields.Dict(
        keys=fields.String(allow_none=True),
        values=fields.DateTime(format="%Y-%m-%d", allow_none=True),
        load_only=True,
    )
    base_currencies = fields.List(
        fields.String(
            validate=validate.OneOf(
                get_currencies(), error="Only available currency can be accepted"
            )
        ),
        allow_none=True,
        data_key="base_currency",
    )
    banks = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(BankSchema(only=("id", "name"))),
        allow_none=True,
        data_key="bank",
    )
    categories = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(CategorySchema(only=("id", "name"))),
        allow_none=True,
        data_key="category",
    )
    available_currencies = fields.List(
        fields.String(validate=validate.Length(equal=3)),
        dump_only=True,
        data_key="available_currencies",
    )

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

# WIP New structure of filter schemas
class FiltersSchema(ma.Schema):
    """Schema used for validation of filtering values"""

    amount = fields.Dict(
        keys=fields.String(validate=validate.OneOf(["min", "max"])),
        values=fields.Float(allow_none=True),
    )
    date = fields.Dict(
        keys=fields.String(validate=validate.OneOf(["min", "max"])),
        values=fields.DateTime(format="%Y-%m-%d", allow_none=True),
    )
    base_currencies = fields.List(
        fields.String(
            validate=validate.OneOf(
                get_currencies(), error="Only available currency can be accepted"
            )
        ),
        allow_none=True,
        data_key="base_currency",
    )
    banks = fields.List(fields.Integer(), allow_none=True, data_key="bank")
    categories = fields.List(fields.Integer(), allow_none=True, data_key="category")

    @pre_load
    def _remove_blanks(self, data: dict, **kwargs: dict[str, Any]) -> dict:
        """Replace empty values (strings) with None"""
        # TODO: Temporary fix for wrongly structured Request body
        # Sends fields with empty string instead of omitting them in request body

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


class UserEntitiesSchema(ma.Schema):
    """Schema used for dumping entities assigned to user"""

    base_currencies = fields.List(
        fields.String(
            validate=validate.OneOf(
                get_currencies(), error="Only available currency can be accepted"
            )
        ),
        dump_only=True,
        data_key="base_currencies",
    )
    banks = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(BankSchema()),
        dump_only=True,
        data_key="banks",
    )
    categories = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(CategorySchema()),
        dump_only=True,
        data_key="categories",
    )


class SessionEntitiesSchema(ma.Schema):
    """Schema used for dumping entities assigned to user"""

    currencies = fields.List(
        fields.String(
            validate=validate.OneOf(
                get_currencies(), error="Only available currency can be accepted"
            )
        ),
        dump_only=True,
        data_key="currencies",
    )
    banks = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(BankSchema()),
        dump_only=True,
        data_key="banks",
    )
