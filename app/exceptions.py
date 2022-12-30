class InvalidConfigError(Exception):
    pass


class FileError(Exception):
    """Error raised due to incompatibility or
    errors in imported external files (statements/exchange rate csvs)"""

    def __init__(self, message: str) -> None:
        self.message = message


class ExternalApiError(Exception):
    """Error raised as a consequence of failed external API calls"""

    def __init__(self, message: str) -> None:
        self.message = message
