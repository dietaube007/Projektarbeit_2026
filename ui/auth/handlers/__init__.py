"""
Auth Handlers - UI-Handler für Authentifizierung.
"""

from .login_handler import handle_login, handle_logout
from .register_handler import handle_register
from .password_reset_handler import show_password_reset_dialog_feature
from .error_handler import handle_auth_error

__all__ = [
    "handle_login",
    "handle_logout",
    "handle_register",
    "show_password_reset_dialog_feature",
    "handle_auth_error",
]
