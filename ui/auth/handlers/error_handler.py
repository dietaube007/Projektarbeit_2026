"""
Error-Handler: Zentrale Fehlerbehandlung für Auth-Operationen.
"""

from __future__ import annotations

from typing import Callable

from utils.logging_config import get_logger
from ui.constants import MESSAGE_TYPE_ERROR

logger = get_logger(__name__)


def handle_auth_error(
    error: Exception,
    operation_name: str,
    show_message_callback: Callable[[str, str], None],
) -> None:
    """Zentrale Fehlerbehandlung für Auth-Operationen."""
    logger.error(f"Fehler bei {operation_name}: {error}", exc_info=True)
    show_message_callback(
        "Ein unerwarteter Fehler ist aufgetreten.",
        MESSAGE_TYPE_ERROR
    )
