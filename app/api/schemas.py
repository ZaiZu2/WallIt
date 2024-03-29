import datetime as dt
from datetime import datetime
from typing import Any

from flask import current_app
from flask_login import current_user
from marshmallow import (
    EXCLUDE,
    ValidationError,
    fields,
    post_dump,
    post_load,
    pre_dump,
    pre_load,
    validates,
    validates_schema,
)
from marshmallow.validate import Email, Length, Range, Regexp

from app import ma
from app.models import Bank, Category, Transaction, User
from config import Config


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        ordered = True

    id = ma.auto_field()
    username = ma.auto_field(
        validate=Regexp(
            "^[A-Za-z0-9]+$",
            error="Username must be a single word consisting of alpha-numeric characters",
        ),
    )
    email = ma.auto_field(validate=Email())
    first_name = ma.auto_field(
        validate=Regexp(
            "^[A-Za-z]+$",
            error="Name must be a single word starting with a capital letter",
        )
    )
    last_name = ma.auto_field(
        validate=Regexp(
            "^[A-Za-z]+$",
            error="Last name must be a single word starting with a capital letter",
        )
    )
    main_currency = ma.auto_field()

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

    @validates("main_currency")
    def _check_available_currencies(self, currency: str) -> None:
        if currency not in current_app.config["SUPPORTED_CURRENCIES"]:
            raise ValidationError("Only available currency can be accepted")


class ModifyUserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        ordered = True

    username = ma.auto_field(
        required=False,
        validate=Regexp(
            "^[A-Za-z0-9]+$",
            error="Username must be a single word consisting of alpha-numeric characters",
        ),
    )
    first_name = ma.auto_field(
        required=False,
        validate=Regexp(
            "^[A-Za-z]+$",
            error="Name must be a single word starting with a capital letter",
        ),
    )
    last_name = ma.auto_field(
        required=False,
        validate=Regexp(
            "^[A-Za-z]+$",
            error="Last name must be a single word starting with a capital letter",
        ),
    )
    main_currency = ma.auto_field(required=False)

    @validates("username")
    def _check_unique_username(self, username: str) -> None:
        username_exists: bool = (
            User.query.filter_by(username=username).scalar() is not None
        )
        if username_exists:
            raise ValidationError(f"Username {username} already exists")

    @validates("main_currency")
    def _check_available_currencies(self, currency: str) -> None:
        if currency not in current_app.config["SUPPORTED_CURRENCIES"]:
            raise ValidationError("Only available currency can be accepted")


class ChangePasswordSchema(ma.Schema):

    old_password = fields.String(required=True)
    new_password = fields.String(
        required=True,
        validate=Length(min=5, error="Password should be minimum 5 characters long"),
    )
    repeat_password = fields.String(required=True)

    @validates_schema
    def _check_new_password(self, data: dict, **kwargs: dict) -> None:
        if data["old_password"] == data["new_password"]:
            raise ValidationError("New password cannot be the same")

    @validates_schema
    def _repeated_password_check(self, data: dict, **kwargs: dict) -> None:
        if data["new_password"] != data["repeat_password"]:
            raise ValidationError("Passwords do not match")


class CategorySchema(ma.SQLAlchemySchema):
    class Meta:
        model = Category
        ordered = True

    id = ma.auto_field()
    name = ma.auto_field(
        validate=Regexp(
            # Single chain of characters/digits
            # with no whitespaces (foreign characters included)
            "^[\u00BF-\u1FFF\u2C00-\uD7FF\w]+$",
            error="Category name must be a single word",
        )
    )


class UniqueCategorySchema(CategorySchema):
    """Subclass of CategorySchema which raises ValidationError if category already exists for a given user"""

    @validates_schema
    def _check_duplicates(self, data: dict, **kwargs: dict) -> None:
        if Category.query.filter_by(name=data.get("name"), user=current_user).scalar():
            raise ValidationError("Category with this name already exists")


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
    base_currency = ma.auto_field(required=True)
    transaction_date = fields.NaiveDateTime(
        data_key="date",
        timezone=dt.timezone.utc,
        required=True,
        validate=Range(max=datetime.now(), max_inclusive=True),
    )
    creation_date = ma.auto_field()
    place = ma.auto_field()
    category = fields.Pluck(CategorySchema, "id", allow_none=True)
    bank = fields.Pluck(BankSchema, "id", allow_none=True)

    @pre_load
    def _convert_to_nones(self, data: dict, **kwargs: dict) -> dict:
        """Convert values with empty strings to Nones"""
        return {key: None if value == "" else value for key, value in data.items()}

    @validates("base_currency")
    def _check_available_currencies(self, currency: str) -> None:
        if currency not in current_app.config["SUPPORTED_CURRENCIES"]:
            raise ValidationError("Specified currency is not available")

    @validates("category")
    def _check_available_categories(self, category: dict[str, int]) -> None:
        if category is not None and not Category.get_from_id(
            category["id"], current_user
        ):
            raise ValidationError("User does not have a specified category")

    @validates("bank")
    def _check_available_banks(self, bank: dict[str, int]) -> None:
        if bank is not None and not Bank.query.filter_by(id=bank["id"]).first():
            raise ValidationError("Specified bank is not available")

    @post_load
    def _convert_to_models(self, data: dict, **kwargs: dict) -> dict:
        """Convert nested schema name to referenced model objects"""

        if "category" in data and data["category"]:
            data["category"] = Category.query.filter_by(
                id=data["category"]["id"]
            ).first()
        if "bank" in data and data["bank"]:
            data["bank"] = Bank.query.filter_by(id=data["bank"]["id"]).first()
        return data

    @post_dump(pass_many=True)
    def _create_envelope(self, data: dict, **kwargs: dict) -> dict:
        return {"transactions": data}


class ModifyTransactionSchema(ma.Schema):
    """Schema used for validation of modified transaction"""

    info = fields.String(load_only=True)
    title = fields.String(load_only=True)
    place = fields.String(load_only=True)
    category = fields.Pluck(CategorySchema, "id", allow_none=True, load_only=True)
    bank = fields.Pluck(BankSchema, "id", allow_none=True, load_only=True)

    @post_load
    def _findModelObjects(self, data: dict[str, Any], **kwargs: dict) -> dict[str, Any]:
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

    amount_min = fields.Float()
    amount_max = fields.Float()
    date_min = fields.DateTime(format="%Y-%m-%d", allow_none=True)
    date_max = fields.DateTime(format="%Y-%m-%d", allow_none=True)
    base_currencies = fields.List(
        fields.String(),
        allow_none=True,
        data_key="base_currency",
    )
    banks = fields.List(fields.Integer(), allow_none=True, data_key="bank")
    categories = fields.List(fields.Integer(), allow_none=True, data_key="category")

    @validates("base_currencies")
    def _check_available_currencies(self, currencies: list[str]) -> None:
        if currencies and not set(currencies).issubset(
            current_app.config["SUPPORTED_CURRENCIES"]
        ):
            raise ValidationError("Only available currencies can be filtered")

    @validates_schema
    def _check_amount_range(self, data: dict, **kwargs: dict) -> None:
        if (
            data.get("amount_min")
            and data.get("amount_max")
            and data["amount_min"] > data["amount_max"]
        ):
            raise ValidationError("Lower end cannot be higher than the higher end")

    @validates_schema
    def _check_date_range(self, data: dict, **kwargs: dict) -> None:
        if (
            data.get("date_min")
            and data.get("date_max")
            and data["date_min"] > data["date_max"]
        ):
            raise ValidationError("Lower end cannot be higher than the higher end")

    @pre_load
    def _create_list_from_string(self, data: dict, **kwargs: dict) -> dict:
        """Split comma separated values into a list"""

        for param in "base_currency", "category", "bank":
            if data.get(param, None):
                data[param] = data[param].split(",")

        return data


class UserEntitiesSchema(ma.Schema):
    """Schema used for dumping entities assigned to a user"""

    user_details = fields.Nested(UserSchema, exclude=("main_currency",), dump_only=True)
    main_currency = fields.String(dump_only=True)
    base_currencies = fields.List(
        fields.String(),
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
    def _split_user_object(self, data: dict, **kwargs: dict) -> dict:
        """Move main_currency from nested dict to main one"""

        data["main_currency"] = data["user_details"].main_currency
        return data


class SessionEntitiesSchema(ma.Schema):
    """Schema used for dumping entities assigned to user"""

    currencies = fields.List(
        fields.String(),
        dump_only=True,
        data_key="currencies",
    )
    banks = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(BankSchema()),
        dump_only=True,
        data_key="banks",
    )
