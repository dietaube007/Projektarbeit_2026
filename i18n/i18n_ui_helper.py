"""
i18n_ui_helper.py - Hilfsfunktion für Übersetzungen in UI-Komponenten.
"""

from i18n import get_translator


def t(key: str, **kwargs) -> str:
    """
    Kurzform für get_translator().t() für einfachere Verwendung in Views.
    
    Args:
        key: Übersetzungsschlüssel (z.B. "auth.login")
        **kwargs: Variablen für String-Formatierung
    
    Returns:
        Übersetzter Text
    
    Beispiel:
        from i18n.i18n_ui_helper import t
        ft.TextField(label=t("auth.email"))
    """
    return get_translator().t(key, **kwargs)
