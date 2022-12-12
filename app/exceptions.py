class InvalidConfigError(Exception):
    pass


class FileError(Exception):
    """Error raised during bank statement import"""

    pass


class ExternalError(Exception):
    """Error raised as a consequence of failed external API calls"""
