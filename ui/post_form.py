"""
Report Form - Meldungsformular für Haustiere.

Dieses Modul implementiert das Formular zum Erstellen neuer Tiermeldungen
(Vermisste oder gefundene Haustiere) in der PetBuddy-Anwendung.

"""

import flet as ft
from services import references
from datetime import datetime

# ════════════════════════════════════════════════════════════════════
# KONSTANTEN
# ════════════════════════════════════════════════════════════════════

STATUS_VERMISST = "1"
STATUS_GEFUNDEN = "2"
VALID_IMAGE_TYPES = ["jpg", "jpeg", "png", "gif", "webp"]


def build_report_form(page: ft.Page, sb, on_saved_callback=None):

    # Baut das Tiermeldungs-Formular mit allen erforderlichen Feldern.

    # ════════════════════════════════════════════════════════════════════
    # REFERENZDATEN - Werden aus Datenbank geladen
    # ════════════════════════════════════════════════════════════════════
    
    post_statuses = []
    species_list = []
    breeds_by_species = {}
    colors_list = []
    
    # ════════════════════════════════════════════════════════════════════
    # UI-ELEMENTE - Eingabefelder und Kontrollelemente
    # ════════════════════════════════════════════════════════════════════
    
    # MELDUNGSART: Segmentierter Button für Vermisst/Gefunden Auswahl
    meldungsart = ft.SegmentedButton(
        segments=[
            ft.Segment(value="1", label=ft.Text("Vermisst")),
            ft.Segment(value="2", label=ft.Text("Gefunden")),
        ],
        selected=["1"],
        allow_multiple_selection=False,
    )
    
    # FOTOUPLOAD: Speichert Pfad und Namen des ausgewählten Bildes
    photo_preview = ft.Image(width=400, height=250, fit=ft.ImageFit.COVER, visible=False)
    selected_photo = {"path": None, "name": None}
    
    # NAME/ÜBERSCHRIFT: Label ändert sich je nach Meldungsart
    # "Name" für vermisste Tiere, "Überschrift" für gefundene
    title_label = ft.Text("Name﹡", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700)
    name_tf = ft.TextField(width=400)
    
    # TIERDETAILS: Dropdowns für Tierart und Rasse
    # Rasse-Dropdown wird dynamisch basierend auf ausgewählter Tierart gefüllt
    species_dd = ft.Dropdown(label="Tierart﹡", text_size=14, width=250)
    breed_dd = ft.Dropdown(label="Rasse (optional)", width=250)
    
    # FARBEN: Responsive Row mit Checkboxes für Mehrfach-Auswahl
    # Benutzer können eine oder mehrere Farben auswählen
    farben_checkboxes = {}
    selected_farben = []
    farben_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
    
    # BESCHREIBUNG: Mehrzeiliges Textfeld für Details und Merkmale
    info_tf = ft.TextField(
        multiline=True,
        max_lines=4,
        width=500,
        min_lines=2,
    )
    
    # STANDORT & DATUM: Lokation und Zeitpunkt der Sichtung
    location_tf = ft.TextField(label="Ort﹡", width=500)
    date_tf = ft.TextField(label="Datum﹡ (TT.MM.YYYY)", width=250, hint_text="z.B. 15.11.2025")
    
    # STATUS-NACHRICHT: Zeigt Fehler, Warnung oder Erfolgsmeldungen
    status_text = ft.Text("", color=ft.Colors.BLUE, size=12)
    
    # ════════════════════════════════════════════════════════════════════
    # HILFSFUNKTIONEN - Reagieren auf Benutzerinteraktion
    # ════════════════════════════════════════════════════════════════════
    
    def update_title_label():

        # Aktualisiert das Label und Placeholder des Namensfelds.
 
        is_vermisst = STATUS_VERMISST in (meldungsart.selected or [STATUS_VERMISST])
        title_label.value = "Name﹡" if is_vermisst else "Überschrift﹡"
        page.update()
    
    meldungsart.on_change = lambda _: update_title_label()
    
    # ════════════════════════════════════════════════════════════════════
    # FOTOMANAGEMENT - Upload und Vorschau
    # ════════════════════════════════════════════════════════════════════
    
    async def pick_photo():
        """
        Öffnet den nativen Dateiauswahl-Dialog zur Fotoauswahl.
        
        Akzeptierte Dateitypen: jpg, jpeg, png, gif, webp
        
        """
        def on_result(ev: ft.FilePickerResultEvent):
            if ev.files:
                f = ev.files[0]
                selected_photo["path"] = f.path
                selected_photo["name"] = f.name
                photo_preview.src = f.path
                photo_preview.visible = True
                status_text.value = f"✓ Foto: {f.name}"
                status_text.color = ft.Colors.GREEN
                page.update()
        
        fp = ft.FilePicker(on_result=on_result)
        page.overlay.append(fp)
        page.update()
        fp.pick_files(allow_multiple=False, allowed_extensions=VALID_IMAGE_TYPES)
    
    def remove_photo():

        # Entfernt das aktuell ausgewählte Foto aus der Meldung.

        selected_photo["path"] = None
        selected_photo["name"] = None
        photo_preview.visible = False
        status_text.value = ""
        page.update()
    
    # ════════════════════════════════════════════════════════════════════
    # DATENLADEN - Lädt Referenzdaten aus Datenbank
    # ════════════════════════════════════════════════════════════════════
    
    async def load_refs():

        # Lädt alle Referenzdaten aus der Datenbank.

        nonlocal post_statuses, species_list, breeds_by_species, colors_list
        
        try:
            # Lade alle Referenzdaten aus den Services
            post_statuses = references.get_post_statuses(sb)
            species_list = references.get_species(sb)
            breeds_by_species = references.get_breeds_by_species(sb)
            colors_list = references.get_colors(sb)
            
            # Fülle Tierart-Dropdown mit Optionen
            species_dd.options = [ft.dropdown.Option(str(s["id"]), s["name"]) for s in species_list]
            
            # Baue Farben-Checkboxes auf
            farben_container.controls = []
            for color in colors_list:
                def on_color_change(e, c_id=color["id"], c_name=color["name"]):
                    """
                    Callback wenn Farb-Checkbox geklickt wird.
                    
                    Addiert/Entfernt Farb-ID aus selected_farben Liste.
                    """
                    if e.control.value:
                        if c_id not in selected_farben:
                            selected_farben.append(c_id)
                    else:
                        if c_id in selected_farben:
                            selected_farben.remove(c_id)
                
                cb = ft.Checkbox(label=color["name"], value=False, on_change=on_color_change)
                farben_checkboxes[color["id"]] = cb
                farben_container.controls.append(
                    ft.Container(cb, col={"xs": 6, "sm": 6, "md": 4})
                )
            
            # Setze Standard-Werte
            if species_list:
                species_dd.value = str(species_list[0]["id"])
                await update_breeds()
            
            page.update()
        except Exception as ex:
            print(f"Fehler beim Laden der Referenzdaten: {ex}")
    
    async def update_breeds():
        """
        Aktualisiert Rasse-Dropdown basierend auf ausgewählter Tierart.
        
        Wenn ein Benutzer eine Tierart wählt, werden die
        entsprechenden Rassen im breed_dd geladen.

        """
        try:
            sid = int(species_dd.value) if species_dd.value else None
            if sid and sid in breeds_by_species:
                breed_dd.options = [ft.dropdown.Option(str(b["id"]), b["name"]) for b in breeds_by_species[sid]]
                if breed_dd.options:
                    breed_dd.value = breed_dd.options[0].key
            else:
                breed_dd.options = []
            page.update()
        except Exception as ex:
            print(f"Fehler beim Aktualisieren der Rassen: {ex}")
    
    species_dd.on_change = lambda _: page.run_task(update_breeds)
        
    page.run_task(load_refs)
    
    # ════════════════════════════════════════════════════════════════════
    # FORMULAR-LAYOUT - Visuelle Struktur und Anordnung
    # ════════════════════════════════════════════════════════════════════
    
    form_column = ft.Column(
        [
            # HEADER: Formular-Titel
            ft.Text("Tier melden", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20),
            
            # SEKTION 1: Meldungsart (Vermisst/Gefunden)
            ft.Text("Meldungsart", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            meldungsart,
            ft.Divider(height=20),
            
            # SEKTION 2: Fotoupload mit Vorschau
            ft.Text("Foto﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            ft.Container(
                content=ft.Column([
                    # Upload-Area (klickbar zum Öffnen des Datei-Dialogs)
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.CAMERA_ALT, size=40, color=ft.Colors.GREY_500),
                            ft.Text("Foto hochladen (Tippen)", color=ft.Colors.GREY_700, size=12),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        width=400,
                        height=150,
                        border=ft.border.all(2, ft.Colors.GREY_300),
                        border_radius=8,
                        on_click=lambda _: page.run_task(pick_photo),
                    ),
                    # Vorschaubild (nur sichtbar wenn Foto gewählt)
                    photo_preview,
                    # Entfernen-Button (nur sichtbar wenn Foto gewählt)
                    ft.Row([
                        ft.TextButton("Foto entfernen", icon=ft.Icons.DELETE, on_click=lambda _: remove_photo()),
                    ]) if selected_photo["path"] else ft.Container(height=0),
                ], spacing=10),
            ),
            ft.Divider(height=20),
            
            # SEKTION 3: Tier-Grundinfos (Name/Überschrift, Tierart, Rasse)
            title_label,
            name_tf,
            ft.Row([species_dd, breed_dd], spacing=15, wrap=True),
            
            # SEKTION 4: Farben (Checkboxes in ResponsiveRow)
            ft.Text("Farben﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            farben_container,
            ft.Divider(height=20),
            
            # SEKTION 5: Beschreibung & Besondere Merkmale
            ft.Text("Beschreibung & Merkmale﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            info_tf,
            ft.Divider(height=20),
            
            # SEKTION 6: Standort & Zeitpunkt der Sichtung
            ft.Text("Standort & Datum﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            location_tf,
            date_tf,
            ft.Divider(height=20),
            
            # SEKTION 7: Speichern-Button und Status-Nachricht
            ft.Row([
                ft.FilledButton("Meldung speichern", width=200),
            ]),
            status_text,
        ],
        spacing=10,
    )
    
    # ════════════════════════════════════════════════════════════════════
    # RÜCKGABE - Scrollbarer Container mit kompletten Formular
    # ════════════════════════════════════════════════════════════════════
    
    return ft.Column(
        [form_column],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )