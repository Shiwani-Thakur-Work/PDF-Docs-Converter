class AppBaseException(Exception):
    """Base exception for converter application."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class ValidationError(AppBaseException):
    """Raised when file validation (magic bytes, size, format) fails."""
    def __init__(self, message: str):
        super().__init__(message, status_code=422)

class PasswordProtectedError(AppBaseException):
    """Raised when a PDF is encrypted with a password."""
    def __init__(self, message: str = "The document is password-protected. Please remove the password and try again."):
        super().__init__(message, status_code=422)

class ConversionError(AppBaseException):
    """Raised when document conversion fails."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)
