class PhotosAppException(Exception):
    """Base exception class for Photos APP application."""

    def __init__(self, message=None, *args, **kwargs):
        if message is None:
            message = "An error occurred in the Photos APP application."
        super().__init__(message, *args, **kwargs)


class InvalidTransactionError(PhotosAppException):
    """Exception raised for invalid transactions."""

    def __init__(self, transaction_id, message=None):
        if message is None:
            message = f"Invalid transaction: {transaction_id}"
        super().__init__(message)


class UnauthorizedAccessError(PhotosAppException):
    """Exception raised for unauthorized access."""

    def __init__(self, user_id, message=None):
        if message is None:
            message = f"Unauthorized access by user: {user_id}"
        super().__init__(message)


class DataNotFoundError(PhotosAppException):
    """Exception raised when the required data is not found."""

    def __init__(self, data_id, message=None):
        if message is None:
            message = f"Data not found: {data_id}"
        super().__init__(message)


class UserNotFoundException(PhotosAppException):
    """Exception raised when a user is not found."""

    def __init__(self, username, message=None):
        if message is None:
            message = f"User not found: {username}"
        super().__init__(message)


class AuthenticationFailedException(PhotosAppException):
    """Exception raised when authentication fails."""

    def __init__(self, username=None, message=None):
        if message is None:
            message = (
                f"Authentication failed for user: {username}"
                if username
                else "Authentication failed."
            )
        super().__init__(message)


class AuthenticationCredentialsNotProvidedException(PhotosAppException):
    """Exception raised when authentication credentials are not provided."""

    def __init__(self, message=None):
        if message is None:
            message = "Authentication credentials were not provided."
        super().__init__(message)


class InvalidOrExpiredTokenException(PhotosAppException):
    """Exception raised for invalid or expired token."""

    def __init__(self, message=None):
        if message is None:
            message = "Invalid or expired token."
        super().__init__(message)