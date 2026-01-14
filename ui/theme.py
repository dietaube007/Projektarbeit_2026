"""
Theme Management - Design-System und Farbgebung.

Dieses Modul verwaltet das visuelle Erscheinungsbild der PetBuddy-Anwendung.
Es definiert:
- Farbschema und Material-3 Design-System
- Hell- und Dunkelmodus-Themes
- Wiederverwendbare UI-Komponenten (Chips, Soft Cards)
- Theme-Toggle-Funktionalität

"""

from typing import Callable, Optional, Any, Dict
from ui.constants import TEXT_SECONDARY
import flet as ft
from utils.logging_config import get_logger

logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════════════
# DESIGN-KONSTANTEN
# ════════════════════════════════════════════════════════════════════

# Farben
PRIMARY_SEED: str = "#4C6FFF"  # Primäre Farbe - Blau für Material 3 Design

# Layout-Dimensionen
RADIUS: int = 16               # Standard Border-Radius für alle Elemente
CHIP_PADDING: int = 6          # Innerer Abstand in Badges/Chips
CHIP_BORDER_RADIUS: int = 999  # Vollständig rund (Pille-Form)
CHIP_FONT_SIZE: int = 11       # Schriftgröße in Chips

# Theme-Modi
THEME_LIGHT: str = "light"
THEME_DARK: str = "dark"
DEFAULT_CARD_PADDING: int = 16
DEFAULT_CARD_ELEVATION: float = 2.0

# ════════════════════════════════════════════════════════════════════
# THEME-FARBEN 
# ════════════════════════════════════════════════════════════════════

from ui.constants import (
    LIGHT_BACKGROUND,
    LIGHT_CARD,
    LIGHT_TEXT_PRIMARY,
    LIGHT_TEXT_SECONDARY,
    DARK_BACKGROUND,
    DARK_CARD,
    DARK_TEXT_PRIMARY,
    DARK_TEXT_SECONDARY,
)

__all__ = [
    "LIGHT_BACKGROUND",
    "LIGHT_CARD",
    "LIGHT_TEXT_PRIMARY",
    "LIGHT_TEXT_SECONDARY",
    "DARK_BACKGROUND",
    "DARK_CARD",
    "DARK_TEXT_PRIMARY",
    "DARK_TEXT_SECONDARY",
    "THEME_COLORS",
    "get_theme_color",
    "ThemeManager",
    "soft_card",
    "chip",
]

# Mapping für einfachen Zugriff
THEME_COLORS: dict[str, dict[str, Any]] = {
    "background": {
        "light": LIGHT_BACKGROUND,
        "dark": DARK_BACKGROUND,
    },
    "card": {
        "light": LIGHT_CARD,
        "dark": DARK_CARD,
    },
    "text_primary": {
        "light": LIGHT_TEXT_PRIMARY,
        "dark": DARK_TEXT_PRIMARY,
    },
    "text_secondary": {
        "light": LIGHT_TEXT_SECONDARY,
        "dark": DARK_TEXT_SECONDARY,
    },
}


def get_theme_color(
    color_key: str, 
    is_dark: Optional[bool] = None, 
    page: Optional[ft.Page] = None
) -> Any:
    """
    Gibt die passende Farbe für den aktuellen Theme-Modus zurück.
    
    Args:
        color_key: "background", "card", "text_primary", "text_secondary"
        is_dark: True für Dark-Modus, False für Light-Modus (optional wenn page gegeben)
        page: Flet Page-Instanz (optional, wird verwendet um is_dark automatisch zu ermitteln)
    
    Returns:
        Farbe als String oder ft.Color
    
    Raises:
        KeyError: Wenn color_key nicht existiert
        ValueError: Wenn weder is_dark noch page angegeben werden
    """
    # is_dark automatisch aus Page ermitteln, falls nicht gegeben
    if is_dark is None:
        if page:
            is_dark = page.theme_mode == ft.ThemeMode.DARK
        else:
            logger.warning("is_dark oder page muss angegeben werden. Verwende Light-Modus.")
            is_dark = False
    
    mode = "dark" if is_dark else "light"
    if color_key not in THEME_COLORS:
        logger.warning(f"Unbekannter Farb-Schlüssel '{color_key}'. Verwende 'background'.")
        color_key = "background"
    return THEME_COLORS[color_key][mode]


class ThemeManager:
    """
    Klasse zur Verwaltung des App-Themes.
    
    Verantwortlich für:
    - Erstellen und Anwenden von Light/Dark Themes
    - Theme-Toggle-Funktionalität
    - Sprach-Umschalter
    - Material 3 Design-Konfiguration
    """
    
    def __init__(self, page: ft.Page) -> None:
        """Initialisiert den ThemeManager mit einer Flet-Page."""
        self.page = page
        self._toggle_button: ft.IconButton | None = None
        self._on_after_toggle: Optional[Callable[[bool], None]] = None
    
    # ════════════════════════════════════════════════════════════════════
    # THEME-BUILDER
    # ════════════════════════════════════════════════════════════════════
    
    @staticmethod
    def build_theme_light() -> ft.Theme:
        """
        Erstellt ein helles Material-3-Theme für die Anwendung.
        
        Returns:
            ft.Theme: Konfiguriertes Theme mit Material 3 Design.
        """
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

        # Input-Decorator (optional, abhängig von Flet-Version)
        try:
            t.input_decorator_theme = ft.InputDecoratorTheme(border_radius=RADIUS)
        except AttributeError:
            # InputDecoratorTheme nicht verfügbar in älterer Flet-Version
            pass

        return t

    @staticmethod
    def build_theme_dark() -> ft.Theme:
        """
        Erstellt ein dunkles Material-3-Theme für die Anwendung.
        
        Hinweis: Verwendet aktuell das gleiche Theme wie Light-Modus.
        Flet passt Farben automatisch an den Dark-Modus an.
        """
        return ThemeManager.build_theme_light()
    
    # ════════════════════════════════════════════════════════════════════
    # THEME-VERWALTUNG
    # ════════════════════════════════════════════════════════════════════
    
    def apply_theme(self, mode: str = THEME_LIGHT) -> None:
        """Wendet ein Theme auf die Seite an und setzt den Modus."""
        if mode not in (THEME_LIGHT, THEME_DARK):
            logger.warning(f"Ungültiger Theme-Modus '{mode}'. Verwende '{THEME_LIGHT}'.")
            mode = THEME_LIGHT
        
        self.page.theme = self.build_theme_light()
        self.page.dark_theme = self.build_theme_dark()
        self.page.theme_mode = (
            ft.ThemeMode.LIGHT if mode == THEME_LIGHT else ft.ThemeMode.DARK
        )
        self.page.update()
    
    def _get_current_icon(self) -> str:
        """Gibt das passende Icon basierend auf aktuellem Theme zurück."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        return ft.Icons.LIGHT_MODE if is_dark else ft.Icons.DARK_MODE
    
    def _get_current_tooltip(self) -> str:
        """Gibt den passenden Tooltip/Aria-Label-Text für die Toggle-Aktion zurück."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        return "Zu Hellmodus wechseln" if is_dark else "Zu Dunkelmodus wechseln"
    
    def _toggle_theme(self, _) -> None:
        """Toggled zwischen Light und Dark Theme."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        self.page.theme_mode = ft.ThemeMode.LIGHT if is_dark else ft.ThemeMode.DARK
        
        # Page-Hintergrund aktualisieren
        new_is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        self.page.bgcolor = get_theme_color("background", new_is_dark)
        
        # Icon-Update im Button (wenn vorhanden)
        if self._toggle_button:
            self._toggle_button.icon = self._get_current_icon()
            # Icon-Farbe basierend auf neuem Theme aktualisieren
            self._toggle_button.icon_color = ft.Colors.WHITE if new_is_dark else ft.Colors.GREY_700
            tip = self._get_current_tooltip()
            self._toggle_button.tooltip = tip
            try:
                self._toggle_button.semantic_label = tip
            except Exception as e:
                logger.debug(f"Semantic label nicht verfügbar: {e}")
                pass
        
        # Callback für View-spezifische UI-Updates nach Theme-Wechsel
        if self._on_after_toggle:
            self._on_after_toggle(new_is_dark)
        
        self.page.update()
    
    def create_toggle_button(
        self, 
        on_after_toggle: Optional[Callable[[bool], None]] = None,
        icon_color: Optional[str] = None
    ) -> ft.IconButton:
        """
        Erstellt einen Icon-Button zum Wechseln zwischen Hell/Dunkel-Modus.
        
        Args:
            on_after_toggle: Optionaler Callback(is_dark: bool), der nach Theme-Wechsel 
                            aufgerufen wird für View-spezifische UI-Updates
            icon_color: Optional manuelle Icon-Farbe (Standard: automatisch)
        
        Returns:
            IconButton für Theme-Toggle
        """
        self._on_after_toggle = on_after_toggle
        
        tip = self._get_current_tooltip()
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        
        # Icon-Farbe: manuell gesetzt oder automatisch basierend auf Theme
        if icon_color is None:
            icon_color=get_theme_color("text_secondary", is_dark) if is_dark else TEXT_SECONDARY
        
        self._toggle_button = ft.IconButton(
            icon=self._get_current_icon(),
            tooltip=tip,
            on_click=self._toggle_theme,
            icon_color=icon_color,
        )
        # Optional: Screenreader-Label nur setzen, wenn unterstützt
        try:
            self._toggle_button.semantic_label = tip
        except Exception as e:
            logger.debug(f"Semantic label nicht verfügbar: {e}")
            pass
        return self._toggle_button
    


# ════════════════════════════════════════════════════════════════════
# UI-KOMPONENTEN - Wiederverwendbare Design-Elemente
# ════════════════════════════════════════════════════════════════════



# ════════════════════════════════════════════════════════════════════
# UI-KOMPONENTEN - Wiederverwendbare Design-Elemente
# ════════════════════════════════════════════════════════════════════

def chip(label: str, color: str | None = None) -> ft.Control:
    """
    Erstellt einen kleinen, runden Badge-Chip mit Text.
    
    Args:
        label: Text-Inhalt des Chips.
        color: Hintergrundfarbe (Standard: Grau).
    
    Returns:
        ft.Control: Container mit Chip-Styling.
    
    Design:
        - Pille-Form (vollständig gerundete Ecken)
        - Weißer Text auf farbigem Hintergrund
        - Kleiner Font (CHIP_FONT_SIZE)
    """
    return ft.Container(
        content=ft.Text(label, size=CHIP_FONT_SIZE, color=ft.Colors.WHITE),
        bgcolor=color or ft.Colors.GREY_700,
        padding=ft.padding.symmetric(CHIP_PADDING, CHIP_PADDING),
        border_radius=CHIP_BORDER_RADIUS,
    )


def soft_card(
    content: ft.Control,
    pad: int = DEFAULT_CARD_PADDING,
    elev: float = DEFAULT_CARD_ELEVATION
) -> ft.Control:
    """
    Erstellt eine Card mit sanfter Elevation und runden Ecken.
    
    Args:
        content: Der Inhalt der Karte.
        pad: Innerer Abstand (Standard: DEFAULT_CARD_PADDING).
        elev: Schattenstärke (Standard: DEFAULT_CARD_ELEVATION).
    
    Returns:
        ft.Control: Material-3 Card mit dem gegebenen Inhalt.
    
    Design:
        - Soft Design mit subtlem Schatten
        - Runde Ecken (RADIUS)
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