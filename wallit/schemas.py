from wallit import ma, db
from wallit.models import Bank, Category, Transaction, User
from wallit.imports import get_currencies

from typing import Any
from flask_login import current_user
from marshmallow import (
    fields,
    post_dump,
    pre_dump,
    pre_load,
    post_load,
    validate,
    validates,
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
        ),
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

    @validates("username")
    def check_unique_username(self, username: str) -> None:
        username_exists: bool = (
            User.query.filter_by(username=username).scalar() is not None
        )
        if username_exists:
            raise ValidationError(f"Username {username} already exists")

    @validates("email")
    def check_unique_email(self, email: str) -> None:
        if User.query.filter_by(email=email.lower()).scalar() is not None:
            raise ValidationError(f"Username {email} already exists")


class ModifyUserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        ordered = True

    username = ma.auto_field(
        required=False,
        validate=validate.Regexp(
            "^[A-Za-z0-9]+$",
            error="Username must be a single word consisting of alpha-numeric characters",
        ),
    )
    first_name = ma.auto_field(
        required=False,
        validate=validate.Regexp(
            "^[A-Za-z][a-z]*$",
            error="Name must be a single word starting with a capital letter",
        ),
    )
    last_name = ma.auto_field(
        required=False,
        validate=validate.Regexp(
            "^[A-Za-z][a-z]*$",
            error="Last name must be a single word starting with a capital letter",
        ),
    )
    main_currency = ma.auto_field(
        required=False,
        validate=validate.OneOf(
            get_currencies(), error="Only available currency can be accepted"
        ),
    )

    @validates("username")
    def _check_unique_username(self, username: str) -> None:
        username_exists: bool = (
            User.query.filter_by(username=username).scalar() is not None
        )
        if username_exists:
            raise ValidationError(f"Username {username} already exists")


class ChangePasswordSchema(ma.Schema):

    old_password = fields.String(required=True)
    new_password = fields.String(
        required=True,
        validate=validate.Length(
            min=5, error="Password should be minimum 5 characters long"
        ),
    )
    repeat_password = fields.String(required=True)

    @validates_schema
    def _check_new_password(self, data: dict, **kwargs: dict[str, Any]) -> None:
        if data["old_password"] == data["new_password"]:
            raise ValidationError("New password cannot be the same")

    @validates_schema
    def _repeated_password_check(self, data: dict, **kwargs: dict[str, Any]) -> None:
        if data["new_password"] != data["repeat_password"]:
            raise ValidationError("Passwords do not match")


class CategorySchema(ma.SQLAlchemySchema):
    class Meta:
        model = Category
        ordered = True

    id = ma.auto_field()
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

    id = ma.auto_field()
    name = ma.auto_field()


class TransactionSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Transaction
        ordered = True
        unknown = EXCLUDE

    id = ma.auto_field(dump_only=True)
    info = ma.auto_field()
    title = ma.auto_field()
    amount = ma.auto_field("main_amount", required=False)
    base_amount = ma.auto_field(required=True)
    base_currency = ma.auto_field(
        validate=validate.OneOf(get_currencies()),
        required=True,
    )
    date = ma.auto_field("transaction_date", required=True)
    creation_date = ma.auto_field()
    place = ma.auto_field()
    category = fields.Pluck(CategorySchema, "id", allow_none=True)
    bank = fields.Pluck(BankSchema, "id", allow_none=True)

    @post_load
    def _convert_to_transaction(
        self, data: dict, **kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        """Convert nested schema name to foreign key relationships and load into Transaction object"""

        if "category" in data:
            if data["category"]:
                data["category"] = Category.get_from_id(
                    data["category"]["id"], current_user
                )
            else:
                data["category"] = None
        if "bank" in data:
            if data["bank"]:
                data["bank"] = Bank.query.filter_by(id=data["bank"]["id"]).first()
            else:
                data["bank"] = None
        return data

    @post_dump(pass_many=True)
    def _create_envelope(self, data: dict, **kwargs: dict[str, Any]) -> dict[str, dict]:
        return {"transactions": data}


class ModifyTransactionSchema(ma.Schema):
    """Schema used for validation of modified transaction"""

    info = fields.String(load_only=True)
    title = fields.String(load_only=True)
    place = fields.String(load_only=True)
    category = fields.Pluck(CategorySchema, "id", allow_none=True, load_only=True)
    bank = fields.Pluck(BankSchema, "id", allow_none=True, load_only=True)

    @post_load
    def _findModelObjects(
        self, data: dict[str, Any], **kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        if "category" in data:
            if data["category"]:
                data["category"] = Category.get_from_id(
                    data["category"]["id"], current_user
                )
            else:
                data["category"] = None
        if "bank" in data:
            if data["bank"]:
                data["bank"] = Bank.query.filter_by(id=data["bank"]["id"]).first()
            else:
                data["bank"] = None
        return data


MonthlySaldoSchema = ma.Schema.from_dict(
    {
        "month": fields.DateTime(format="%Y-%m"),
        "incoming": fields.Number(),
        "outgoing": fields.Number(),
        "balance": fields.Number(),
    },
    name="MonthlySaldoSchema",
)


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
        # Client sends fields with empty string instead of omitting them in request body

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

    user_details = fields.Nested(UserSchema, exclude=("main_currency",), dump_only=True)
    main_currency = fields.String(dump_only=True)
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

    @pre_dump
    def _split_user_object(self, data: dict, **kwargs: dict[str, Any]) -> dict:
        """Move main_currency from nested dict to main one"""

        data["main_currency"] = data["user_details"].main_currency
        return data


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
