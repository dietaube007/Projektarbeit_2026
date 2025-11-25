import os
import flet as ft
from services.supabase_client import get_client
from ui.theme import apply_theme, theme_toggle, soft_card
from ui.post_form import build_report_form
from ui.discover import build_list_and_map
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus .env
load_dotenv()

# Secret Key für Flet Uploads aus .env laden
os.environ["FLET_SECRET_KEY"] = os.getenv("FLET_SECRET_KEY", "")

# Konstanten für Tab-Indices
TAB_START, TAB_MELDEN, TAB_PROFIL = range(3)

def main(page: ft.Page):
    try:
        page.title = "PetBuddy"
        page.padding = 0
        page.scroll = ft.ScrollMode.ADAPTIVE
        page.window_min_width = 420
        page.window_width = 1100
        page.window_height = 820
        
        apply_theme(page, "light")
        sb = get_client()
    except Exception as e:
        page.snack_bar = ft.SnackBar(ft.Text(f"Fehler beim Laden: {str(e)}"))
        page.snack_bar.open = True
        page.update()
        return
    
    # ════════════════════════════════════════════════════════════════════
    # NAVIGATION HILFSFUNKTIONEN
    # ════════════════════════════════════════════════════════════════════
    
    current_tab = TAB_START
    body = ft.Container(padding=16, expand=True)
    
    # Platzhalter für UI-Elemente (werden später befüllt)
    start_section = None
    report_form = None
    profile_card = None
    
    def render_tab():
        body.content = {
            TAB_START: start_section,
            TAB_MELDEN: report_form,
            TAB_PROFIL: ft.Container(padding=16, content=profile_card),
        }.get(current_tab, start_section)
        page.update()
    
    def go_to_melden_tab(_=None):
        """Navigiert zum Melden-Tab."""
        nonlocal current_tab
        current_tab = TAB_MELDEN
        if nav:
            nav.selected_index = TAB_MELDEN
        render_tab()
    
    def on_post_saved(post_id=None):
        #Callback nach erfolgreicher Meldung - lädt Liste neu und navigiert zur Startseite.
        nonlocal current_tab
        page.run_task(search_load)
        current_tab = TAB_START
        if nav:
            nav.selected_index = TAB_START
        render_tab()
    
    # ════════════════════════════════════════════════════════════════════
    # UI-BEREICHE LADEN
    # ════════════════════════════════════════════════════════════════════
    
    try:
        list_map_section, search_load, search_row = build_list_and_map(page, sb, on_contact_click=None, on_melden_click=go_to_melden_tab)
        report_form = build_report_form(page, sb, on_saved_callback=on_post_saved)
    except Exception as e:
        page.snack_bar = ft.SnackBar(ft.Text(f"Fehler beim Laden der UI: {str(e)}"))
        page.snack_bar.open = True
        page.update()
        return
    
    # Profil-Karte
    profile_card = soft_card(
        ft.Column([], tight=True),
        elev=3,
    )
    
    # Start-Tab mit Suchleiste und Liste/Karte
    start_section = ft.Column(
        [
            soft_card(ft.Column([search_row], spacing=8), pad=12, elev=2),
            list_map_section,
        ],
        spacing=14,
        expand=True,
    )
    
    # ════════════════════════════════════════════════════════════════════
    # NAVIGATION SETUP
    # ════════════════════════════════════════════════════════════════════
    
    def on_nav_change(e):
        nonlocal current_tab
        current_tab = e.control.selected_index
        render_tab()
    
    nav = ft.NavigationBar(
        selected_index=current_tab,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Start"),
            ft.NavigationBarDestination(icon=ft.Icons.ADD_CIRCLE_OUTLINE, selected_icon=ft.Icons.ADD_CIRCLE, label="Melden"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Profil"),
        ],
        on_change=on_nav_change,
    )
    
    # ════════════════════════════════════════════════════════════════════
    # HAUPTAPP BAUEN
    # ════════════════════════════════════════════════════════════════════
    page.appbar = ft.AppBar(
        title=ft.Text("PetBuddy", size=20, weight=ft.FontWeight.W_600),
        center_title=True,
        actions=[
            ft.IconButton(ft.Icons.NOTIFICATIONS_NONE),
            theme_toggle(page),
        ],
    )
    
    page.navigation_bar = nav
    page.add(body)
    render_tab()
    page.run_task(search_load)
    page.update()


if __name__ == "__main__":
    ft.app(target=main, upload_dir="image_uploads", view=ft.AppView.WEB_BROWSER)