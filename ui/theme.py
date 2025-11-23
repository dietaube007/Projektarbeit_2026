"""
Theme Management - Design-System und Farbgebung.

Dieses Modul verwaltet das visuelle Erscheinungsbild der PetBuddy-Anwendung.
Es definiert:
- Farbschema und Material-3 Design-System
- Hell- und Dunkelmodus-Themes
- Wiederverwendbare UI-Komponenten (Chips, Soft Cards)
- Theme-Toggle-Funktionalität

"""

import flet as ft

# ════════════════════════════════════════════════════════════════════
# DESIGN-KONSTANTEN
# ════════════════════════════════════════════════════════════════════

PRIMARY_SEED = "#4C6FFF"  # Primäre Farbe - Blau für Material 3 Design
RADIUS = 16              # Standard Border-Radius für alle Elemente
CHIP_PADDING = 6         # Innerer Abstand in Badges/Chips
CHIP_BORDER_RADIUS = 999 # Vollständig rund (Pille-Form)

# ════════════════════════════════════════════════════════════════════
# THEME-BUILDER - Erstellt Material-3 Design Themes
# ════════════════════════════════════════════════════════════════════

def build_theme_light() -> ft.Theme:

    # Erstellt ein helles Material-3-Theme für die Anwendung.
 
    t = ft.Theme()
    t.use_material3 = True
    t.color_scheme_seed = PRIMARY_SEED
    t.visual_density = ft.VisualDensity.COMFORTABLE

    # Karten-Styling: Runde Ecken mit RADIUS
    t.card_theme = ft.CardTheme(
        shape=ft.RoundedRectangleBorder(radius=RADIUS)
    )
    
    # Button-Styling: Alle Button-Typen mit runden Ecken

    rounded = ft.RoundedRectangleBorder(radius=RADIUS)
    t.filled_button_theme = ft.ButtonStyle(shape=rounded)
    t.elevated_button_theme = ft.ButtonStyle(shape=rounded)
    t.outlined_button_theme = ft.ButtonStyle(shape=rounded)

    # Input-Decorator: TextFields mit runden Ecken
    # Mit Try-Catch für Kompatibilität mit älteren Flet-Versionen
    try:
        t.input_decorator_theme = ft.InputDecoratorTheme(border_radius=RADIUS)
    except AttributeError:
        # Ältere Flet-Versionen unterstützen dies möglicherweise nicht
        pass

    return t


def build_theme_dark() -> ft.Theme:
    
    # Erstellt ein dunkles Material-3-Theme für die Anwendung.

    
    # Verwendet die gleiche Basis wie das Light-Theme
    # Material Design 3 passt automatisch die Farben an
    return build_theme_light()


# ════════════════════════════════════════════════════════════════════
# THEME-VERWALTUNG - Anwendung von Themes auf die Seite
# ════════════════════════════════════════════════════════════════════

def apply_theme(page: ft.Page, mode: str = "light"):
    
    # Wendet ein Theme auf die Seite an und setzt den Modus.

    if mode not in ("light", "dark"):
        print(f"Warnung: Ungültiger Theme-Modus '{mode}'. Verwende 'light'.")
        mode = "light"
    
    page.theme = build_theme_light()
    page.dark_theme = build_theme_dark()
    page.theme_mode = (
        ft.ThemeMode.LIGHT if mode == "light" else ft.ThemeMode.DARK
    )
    page.update()


def theme_toggle(page: ft.Page) -> ft.IconButton:
    """
    Erstellt einen Icon-Button zum Wechseln zwischen Hell/Dunkel-Modus.
    
    Der Button zeigt:
    - 🌙 Mond-Icon: Wenn aktuell Hell-Modus (zum Wechsel zu Dunkel)
    - ☀️  Sonne-Icon: Wenn aktuell Dunkel-Modus (zum Wechsel zu Hell)

    """
    
    def get_current_icon() -> str:

        # Gibt das passende Icon basierend auf aktuellem Theme zurück.

        return ft.Icons.LIGHT_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE

    def toggle_theme(_):
        
        # Toggled zwischen Light und Dark Theme.
        
        page.theme_mode = (
            ft.ThemeMode.LIGHT
            if page.theme_mode == ft.ThemeMode.DARK
            else ft.ThemeMode.DARK
        )
        btn.icon = get_current_icon()
        page.update()

    btn = ft.IconButton(
        icon=get_current_icon(),
        tooltip="Theme wechseln",
        on_click=toggle_theme
    )
    return btn


# ════════════════════════════════════════════════════════════════════
# UI-KOMPONENTEN - Wiederverwendbare Design-Elemente
# ════════════════════════════════════════════════════════════════════

def chip(label: str, color: str | None = None) -> ft.Control:
    """
    Erstellt einen kleinen, runden Badge-Chip mit Text.
    
    Verwendet:
    - Pille-Form (vollständig gerundete Ecken)
    - Weißer Text auf farbigem Hintergrund
    - Kleiner Font (11px)
    - Standard-Padding (CHIP_PADDING)

    """
    return ft.Container(
        content=ft.Text(label, size=11, color=ft.Colors.WHITE),
        bgcolor=color or ft.Colors.GREY_700,
        padding=ft.padding.symmetric(CHIP_PADDING, CHIP_PADDING),
        border_radius=CHIP_BORDER_RADIUS,
    )


def soft_card(content: ft.Control, pad: int = 16, elev: float = 2) -> ft.Control:
    """
    Erstellt eine Card mit sanfter Elevation und runden Ecken.
    
    Diese Komponente wird häufig zum Umhüllen von Inhalten verwendet:
    - Soft Design mit subtlem Schatten
    - Runde Ecken (RADIUS = 16)
    - Flexibles Padding
    - Material-3 Card-Styling

    """
    return ft.Card(
        elevation=elev,
        content=ft.Container(
            content=content,
            padding=pad,
            border_radius=RADIUS
        ),
    )