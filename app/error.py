"""Implement SQuaSH API exceptions."""


class ApiError(Exception):
    """Basic exception for errors raised by the api."""

    def __init__(self, message=None, status_code=None):
        if message is None:
            message = "An error ocurred."
            status_code = 500
        super(ApiError, self).__init__(message, status_code)
        self.message = message
        self.status_code = status_code
