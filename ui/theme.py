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


class ThemeManager:

    # Klasse zur Verwaltung des App-Themes.
    
    def __init__(self, page: ft.Page):
        
        # Initialisiert den ThemeManager.
        self.page = page
        self._toggle_button = None
    
    # ════════════════════════════════════════════════════════════════════
    # THEME-BUILDER
    # ════════════════════════════════════════════════════════════════════
    
    @staticmethod
    def build_theme_light() -> ft.Theme:
        
        # Erstellt ein helles Material-3-Theme für die Anwendung.

        t = ft.Theme()
        t.use_material3 = True
        t.color_scheme_seed = PRIMARY_SEED
        t.visual_density = ft.VisualDensity.COMFORTABLE

        # Karten-Styling
        t.card_theme = ft.CardTheme(
            shape=ft.RoundedRectangleBorder(radius=RADIUS)
        )
        
        # Button-Styling
        rounded = ft.RoundedRectangleBorder(radius=RADIUS)
        t.filled_button_theme = ft.ButtonStyle(shape=rounded)
        t.elevated_button_theme = ft.ButtonStyle(shape=rounded)
        t.outlined_button_theme = ft.ButtonStyle(shape=rounded)

        # Input-Decorator
        try:
            t.input_decorator_theme = ft.InputDecoratorTheme(border_radius=RADIUS)
        except AttributeError:
            pass

        return t

    @staticmethod
    def build_theme_dark() -> ft.Theme:

        # Erstellt ein dunkles Material-3-Theme für die Anwendung.

        return ThemeManager.build_theme_light()
    
    # ════════════════════════════════════════════════════════════════════
    # THEME-VERWALTUNG
    # ════════════════════════════════════════════════════════════════════
    
    def apply_theme(self, mode: str = "light"):
        # Wendet ein Theme auf die Seite an und setzt den Modus.
        if mode not in ("light", "dark"):
            print(f"Warnung: Ungültiger Theme-Modus '{mode}'. Verwende 'light'.")
            mode = "light"
        
        self.page.theme = self.build_theme_light()
        self.page.dark_theme = self.build_theme_dark()
        self.page.theme_mode = (
            ft.ThemeMode.LIGHT if mode == "light" else ft.ThemeMode.DARK
        )
        self.page.update()
    
    def _get_current_icon(self) -> str: 
        # Gibt das passende Icon basierend auf aktuellem Theme zurück.
        return ft.Icons.LIGHT_MODE if self.page.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE
    
    def _toggle_theme(self, _):
        # Toggled zwischen Light und Dark Theme.
        self.page.theme_mode = (
            ft.ThemeMode.LIGHT
            if self.page.theme_mode == ft.ThemeMode.DARK
            else ft.ThemeMode.DARK
        )
        if self._toggle_button:
            self._toggle_button.icon = self._get_current_icon()
        self.page.update()
    
    def create_toggle_button(self) -> ft.IconButton:
        # Erstellt einen Icon-Button zum Wechseln zwischen Hell/Dunkel-Modus.
        self._toggle_button = ft.IconButton(
            icon=self._get_current_icon(),
            tooltip="Theme wechseln",
            on_click=self._toggle_theme
        )
        return self._toggle_button


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