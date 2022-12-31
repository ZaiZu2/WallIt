from marshmallow import pre_load, post_load
from marshmallow.validate import Length, OneOf, And, Range

from app import ma
from app import Config
from app.models import ExchangeRate


class ExchangeRateSchema(ma.SQLAlchemySchema):
    """Schema used to validate loaded exchange rate values"""

    class Meta:
        model = ExchangeRate
        ordered = True

    id = ma.auto_field()
    date = ma.auto_field(format="%Y-%m-%d", required=True)
    target = ma.auto_field(validate=Length(equal=3))
    source = ma.auto_field(
        required=True, validate=And(Length(equal=3), OneOf(Config.SUPPORTED_CURRENCIES))
    )
    rate = ma.auto_field(required=True, validate=Range(min=0))

    @pre_load
    def _convert_to_nones(self, data: dict, **kwargs: dict) -> dict:
        """Convert values with empty strings to Nones"""
        return {key: None if value == "" else value for key, value in data.items()}

    @post_load
    def _trim_date(self, data: dict, **kwargs: dict) -> dict:
        data["date"] = data["date"].date()
        return data
