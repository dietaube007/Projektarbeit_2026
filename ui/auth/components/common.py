"""
Gemeinsame Auth-Komponenten: Wiederverwendbare Basis-Komponenten.
"""

from __future__ import annotations

import flet as ft
from typing import Optional

from ui.constants import PRIMARY_COLOR, BORDER_COLOR


def create_base_textfield(
    label: str,
    hint_text: str = "",
    password: bool = False,
    keyboard_type: Optional[ft.KeyboardType] = None,
    border_radius: int = 12,
    max_length: Optional[int] = None,
    prefix_icon: Optional[str] = None,
    value: Optional[str] = None,
    width: Optional[int] = None,
) -> ft.TextField:
    """Erstellt ein TextField mit konsistentem Styling.
    
    Wird von login, register und password_reset verwendet.
    
    Args:
        label: Feld-Label
        hint_text: Platzhalter-Text
        password: Ob es ein Passwort-Feld ist
        keyboard_type: Optionaler Keyboard-Typ (z.B. EMAIL)
        border_radius: Border-Radius (Standard: 12)
        max_length: Maximale Textlänge
        prefix_icon: Optionales Icon
        value: Optionaler Vorbelegungswert
        width: Optionale Breite
    
    Returns:
        TextField mit konsistentem Styling
    """
    field = ft.TextField(
        label=label,
        hint_text=hint_text,
        password=password,
        can_reveal_password=password,
        keyboard_type=keyboard_type,
        border_radius=border_radius,
        border_color=BORDER_COLOR,
        border_width=1,
        focused_border_color=PRIMARY_COLOR,
        focused_border_width=2,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )
    
    if max_length:
        field.max_length = max_length
    if prefix_icon:
        field.prefix_icon = prefix_icon
    if value is not None:
        field.value = value
    if width:
        field.width = width
    
    return field
