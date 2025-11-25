"""
Report Form - Meldungsformular für Haustiere.

Dieses Modul implementiert das Formular zum Erstellen neuer Tiermeldungen
(Vermisste oder gefundene Haustiere) in der PetBuddy-Anwendung.

"""

import os
import base64
from datetime import datetime
from typing import Callable, Optional

import flet as ft
from services import references
from services.posts import create_post, add_color_to_post, add_photo_to_post

# ════════════════════════════════════════════════════════════════════
# KONSTANTEN
# ════════════════════════════════════════════════════════════════════

VALID_IMAGE_TYPES = ["jpg", "jpeg", "png", "gif", "webp"]
PLACEHOLDER_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
STORAGE_BUCKET = "pet-images"
UPLOAD_DIR = "image_uploads"
DATE_FORMAT = "%d.%m.%Y"

# Meldungsarten die im Formular angezeigt werden (ohne "Wiedervereint")
ALLOWED_POST_STATUSES = ["vermisst", "fundtier"]

def build_report_form(
    page: ft.Page, 
    sb, 
    on_saved_callback: Optional[Callable] = None
) -> ft.Column:

    # Baut das Tiermeldungs-Formular mit allen erforderlichen Feldern.

    # ════════════════════════════════════════════════════════════════════
    # REFERENZDATEN - Werden aus Datenbank geladen
    # ════════════════════════════════════════════════════════════════════
    
    post_statuses = []  # Meldungsarten (Vermisst, Gefunden, etc.)
    species_list = []
    breeds_by_species = {}
    colors_list = []
    sex_list = []  # Geschlechter (Männlich, Weiblich, Unbekannt)
    
    # ════════════════════════════════════════════════════════════════════
    # UI-ELEMENTE - Eingabefelder und Kontrollelemente
    # ════════════════════════════════════════════════════════════════════
    
    # MELDUNGSART: SegmentedButton für Vermisst/Gefunden
    meldungsart = ft.SegmentedButton(
        selected={"1"},  # Default: Vermisst (ID 1)
        segments=[],  # Wird in load_refs() befüllt
        allow_empty_selection=False,
        allow_multiple_selection=False,
    )
    
    # FOTOUPLOAD: Speichert Pfad und Namen des ausgewählten Bildes
    photo_preview = ft.Image(width=400, height=250, fit=ft.ImageFit.COVER, visible=False, src_base64=PLACEHOLDER_IMAGE)
    selected_photo = {"path": None, "name": None, "url": None, "base64": None}
    
    # NAME/ÜBERSCHRIFT: Label ändert sich je nach Meldungsart
    # "Name" für vermisste Tiere, "Überschrift" für gefundene
    title_label = ft.Text("Name﹡", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700)
    name_tf = ft.TextField(width=400)
    
    # TIERDETAILS: Dropdowns für Tierart, Rasse und Geschlecht
    # Rasse-Dropdown wird dynamisch basierend auf ausgewählter Tierart gefüllt
    species_dd = ft.Dropdown(label="Tierart﹡", text_size=14, width=250)
    breed_dd = ft.Dropdown(label="Rasse (optional)", width=250)
    sex_dd = ft.Dropdown(label="Geschlecht (optional)", width=250)
    
    # FARBEN: Responsive Row mit Checkboxes für Mehrfach-Auswahl
    # Benutzer können eine oder mehrere Farben auswählen
    farben_checkboxes = {}
    selected_farben = []
    farben_container = ft.ResponsiveRow(spacing=4, run_spacing=8)
    
    # Farben-Panel klappbar machen (wie in discover.py)
    farben_panel_visible = {"value": True}  # Dict für nonlocal-Zugriff
    farben_panel = ft.Container(
        content=farben_container,
        padding=12,
        visible=True,
    )
    
    farben_toggle_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_UP)
    
    def toggle_farben_panel(_):
        farben_panel_visible["value"] = not farben_panel_visible["value"]
        farben_panel.visible = farben_panel_visible["value"]
        farben_toggle_icon.name = ft.Icons.KEYBOARD_ARROW_UP if farben_panel_visible["value"] else ft.Icons.KEYBOARD_ARROW_DOWN
        page.update()
    
    farben_header = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PALETTE, size=18),
                ft.Text("Farben﹡", size=14, weight=ft.FontWeight.W_600),
                ft.Container(expand=True),
                farben_toggle_icon,
            ],
            spacing=12,
        ),
        padding=8,
        on_click=toggle_farben_panel,
        border_radius=8,
        bgcolor=ft.Colors.GREY_100,
    )
    
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
    
    def update_title_label(_=None):
        """Aktualisiert das Label basierend auf der gewählten Meldungsart."""
        selected_id = list(meldungsart.selected)[0] if meldungsart.selected else None
        
        # Finde den Namen der gewählten Meldungsart
        selected_status = None
        for status in post_statuses:
            if str(status["id"]) == selected_id:
                selected_status = status["name"].lower()
                break
        
        # "Vermisst" -> Name des Tieres, "Gefunden" -> Überschrift
        if selected_status == "vermisst":
            title_label.value = "Name﹡"
        else:
            title_label.value = "Überschrift﹡"
        page.update()

    meldungsart.on_change = update_title_label    # ════════════════════════════════════════════════════════════════════
    # FOTOMANAGEMENT - Upload und Vorschau
    # ════════════════════════════════════════════════════════════════════
    
    async def pick_photo():
        """Öffnet Dateiauswahl und lädt Bild zu Supabase Storage hoch."""
        
        def on_result(ev: ft.FilePickerResultEvent):
            if ev.files:
                f = ev.files[0]
                selected_photo["name"] = f.name
                
                fp.upload([ft.FilePickerUploadFile(
                    f.name,
                    upload_url=page.get_upload_url(f.name, 60)
                )])
        
        def on_upload(ev: ft.FilePickerUploadEvent):
            if ev.progress == 1.0:
                try:
                    upload_path = f"{UPLOAD_DIR}/{ev.file_name}"
                    with open(upload_path, "rb") as image_file:
                        file_bytes = image_file.read()
                        image_data = base64.b64encode(file_bytes).decode()
                    
                    # Eindeutiger Dateiname
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_ext = ev.file_name.split(".")[-1].lower()
                    storage_filename = f"{timestamp}_{ev.file_name}"
                    
                    # Upload zu Supabase Storage
                    sb.storage.from_(STORAGE_BUCKET).upload(
                        path=storage_filename,
                        file=file_bytes,
                        file_options={"content-type": f"image/{file_ext}"}
                    )
                    
                    # Public URL holen
                    public_url = sb.storage.from_(STORAGE_BUCKET).get_public_url(storage_filename)
                    
                    selected_photo["path"] = storage_filename
                    selected_photo["base64"] = image_data
                    selected_photo["url"] = public_url
                    
                    photo_preview.src_base64 = image_data
                    photo_preview.visible = True
                    status_text.value = f"✓ Hochgeladen: {ev.file_name}"
                    status_text.color = ft.Colors.GREEN
                    page.update()
                    
                    # Temporäre Datei löschen
                    os.remove(upload_path)
                    
                except Exception as ex:
                    status_text.value = f"❌ Fehler: {ex}"
                    status_text.color = ft.Colors.RED
                    page.update()
        
        fp = ft.FilePicker(on_result=on_result, on_upload=on_upload)
        page.overlay.append(fp)
        page.update()
        fp.pick_files(allow_multiple=False, allowed_extensions=VALID_IMAGE_TYPES)
    
    def remove_photo():
        """Entfernt das Foto aus der Vorschau UND aus Supabase Storage."""
        try:
            if selected_photo.get("path"):
                sb.storage.from_(STORAGE_BUCKET).remove([selected_photo["path"]])
                print(f"Gelöscht aus Storage: {selected_photo['path']}")
        except Exception as ex:
            print(f"Fehler beim Löschen aus Storage: {ex}")
        
        # Zurücksetzen
        selected_photo["path"] = None
        selected_photo["name"] = None
        selected_photo["url"] = None
        selected_photo["base64"] = None
        photo_preview.visible = False
        status_text.value = ""
        page.update()
    
    # ════════════════════════════════════════════════════════════════════
    # SPEICHERN - Post in Datenbank speichern
    # ════════════════════════════════════════════════════════════════════
    
    async def save_post(_=None):
        """Speichert die Meldung in der Datenbank."""
        
        # 1. VALIDIERUNG
        errors = []
        
        if not name_tf.value or not name_tf.value.strip():
            errors.append("Name/Überschrift")
        
        if not species_dd.value:
            errors.append("Tierart")
        
        if not selected_farben:
            errors.append("Mindestens eine Farbe")
        
        if not info_tf.value or not info_tf.value.strip():
            errors.append("Beschreibung")
        
        if not location_tf.value or not location_tf.value.strip():
            errors.append("Ort")
        
        if not date_tf.value or not date_tf.value.strip():
            errors.append("Datum")
        
        if not selected_photo.get("url"):
            errors.append("Foto")
        
        if errors:
            status_text.value = f"❌ Bitte ausfüllen: {', '.join(errors)}"
            status_text.color = ft.Colors.RED
            page.update()
            return
        
        # 2. DATUM PARSEN
        try:
            event_date = datetime.strptime(date_tf.value.strip(), DATE_FORMAT).date()
        except ValueError:
            status_text.value = f"❌ Ungültiges Datum. Format: TT.MM.YYYY"
            status_text.color = ft.Colors.RED
            page.update()
            return
        
        # 3. USER ID (Temporär für Entwicklung)
        # TODO: Später durch echte Authentifizierung ersetzen
        user_id = "d798bbdf-eb2d-4030-8830-24c93561ad4f"  
        
        # 4. POST ERSTELLEN
        try:
            status_text.value = "⏳ Erstelle Meldung..."
            status_text.color = ft.Colors.BLUE
            page.update()
            
            post_data = {
                "user_id": user_id,
                "post_status_id": int(list(meldungsart.selected)[0]),
                "headline": name_tf.value.strip(),
                "description": info_tf.value.strip(),
                "species_id": int(species_dd.value),
                "breed_id": int(breed_dd.value) if breed_dd.value and breed_dd.value.isdigit() else None,
                "sex_id": int(sex_dd.value) if sex_dd.value and sex_dd.value.isdigit() else None,
                "event_date": event_date.isoformat(),
                "location_text": location_tf.value.strip(),
            }
            
            # Post in Datenbank speichern
            new_post = create_post(sb, post_data)
            post_id = new_post["id"]
            
            # 5. FARBEN VERKNÜPFEN
            for color_id in selected_farben:
                add_color_to_post(sb, post_id, color_id)
            
            # 6. BILD VERKNÜPFEN
            if selected_photo.get("url"):
                add_photo_to_post(sb, post_id, selected_photo["url"])
            
            # 7. ERFOLG
            status_text.value = "✓ Meldung erfolgreich erstellt!"
            status_text.color = ft.Colors.GREEN
            page.update()
            
            # 8. FORMULAR ZURÜCKSETZEN
            reset_form()
            
            # 9. CALLBACK - Navigiert zur Startseite und lädt Liste neu
            if on_saved_callback:
                on_saved_callback(post_id)
                
        except Exception as ex:
            status_text.value = f"❌ Fehler beim Speichern: {ex}"
            status_text.color = ft.Colors.RED
            page.update()
    
    def reset_form():
        """Setzt das Formular auf Standardwerte zurück."""
        if post_statuses:
            meldungsart.selected = {str(post_statuses[0]["id"])}
        name_tf.value = ""
        if species_list:
            species_dd.value = str(species_list[0]["id"])
        breed_dd.value = None
        breed_dd.options = []
        info_tf.value = ""
        location_tf.value = ""
        date_tf.value = ""
        
        # Farben zurücksetzen
        selected_farben.clear()
        for cb in farben_checkboxes.values():
            cb.value = False
        
        # Foto zurücksetzen (ohne Storage zu löschen - Bild wurde ja gespeichert)
        selected_photo["path"] = None
        selected_photo["name"] = None
        selected_photo["url"] = None
        selected_photo["base64"] = None
        photo_preview.visible = False
        
        # Label zurücksetzen
        title_label.value = "Name﹡"
        status_text.value = ""
        
        page.update()
    
    # ════════════════════════════════════════════════════════════════════
    # DATENLADEN - Lädt Referenzdaten aus Datenbank
    # ════════════════════════════════════════════════════════════════════
    
    async def load_refs(_=None):
        # Lädt alle Referenzdaten aus der Datenbank.
        nonlocal post_statuses, species_list, breeds_by_species, colors_list, sex_list
        
        try:
            # Lade Meldungsarten (Vermisst, Fundtier) - ohne "Wiedervereint"
            all_statuses = references.get_post_statuses(sb)
            post_statuses = [s for s in all_statuses if s["name"].lower() in ALLOWED_POST_STATUSES]
            meldungsart.segments = [
                ft.Segment(value=str(s["id"]), label=ft.Text(s["name"])) for s in post_statuses
            ]
            if post_statuses:
                meldungsart.selected = {str(post_statuses[0]["id"])}
            
            species_list = references.get_species(sb)
            breeds_by_species = references.get_breeds_by_species(sb)
            colors_list = references.get_colors(sb)
            sex_list = references.get_sex(sb)
            
            species_dd.options = [ft.dropdown.Option(str(s["id"]), s["name"]) for s in species_list]
            
            # Geschlecht mit "Keine Angabe" Option
            sex_dd.options = [ft.dropdown.Option("none", "— Keine Angabe —")]
            sex_dd.options += [ft.dropdown.Option(str(s["id"]), s["name"]) for s in sex_list]
            sex_dd.value = "none"  # Standard: Keine Angabe
            
            farben_container.controls = []
            for color in colors_list:
                def on_color_change(e, c_id=color["id"]):
                    if e.control.value:
                        if c_id not in selected_farben:
                            selected_farben.append(c_id)
                    else:
                        if c_id in selected_farben:
                            selected_farben.remove(c_id)
                
                cb = ft.Checkbox(label=color["name"], value=False, on_change=on_color_change)
                farben_checkboxes[color["id"]] = cb
                farben_container.controls.append(
                    ft.Container(cb, col={"xs": 6, "sm": 4, "md": 3})
                )
            
            # Setze Tierart und lade Rassen
            if species_list:
                species_dd.value = str(species_list[0]["id"])
            
            page.update()
            
            # Lade Rassen NACH page.update() damit species_dd.value gesetzt ist
            if species_list:
                await update_breeds()
                page.update()
        except Exception as ex:
            print(f"Fehler beim Laden der Referenzdaten: {ex}")
    
    async def update_breeds(_=None):
        try:
            sid = int(species_dd.value) if species_dd.value else None
            if sid and sid in breeds_by_species:
                # Leere Option am Anfang für "Keine Angabe"
                breed_dd.options = [ft.dropdown.Option("none", "— Keine Angabe —")]
                breed_dd.options += [ft.dropdown.Option(str(b["id"]), b["name"]) for b in breeds_by_species[sid]]
                breed_dd.value = "none"  # Standard: Keine Angabe
            else:
                breed_dd.options = [ft.dropdown.Option("none", "— Keine Angabe —")]
                breed_dd.value = "none"
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
            ft.Text("Tier melden", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20),
            
            meldungsart,
            ft.Divider(height=20),
            
            ft.Text("Foto﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            ft.Container(
                content=ft.Column([
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
                    photo_preview,
                    ft.TextButton("Foto entfernen", icon=ft.Icons.DELETE, on_click=lambda _: remove_photo()),
                ], spacing=10),
            ),
            ft.Divider(height=20),
            
            title_label,
            name_tf,
            ft.Row([species_dd, breed_dd, sex_dd], spacing=15, wrap=True),
            
            farben_header,
            farben_panel,
            ft.Divider(height=20),
            
            ft.Text("Beschreibung & Merkmale﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            info_tf,
            ft.Divider(height=20),
            
            ft.Text("Standort & Datum﹡", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700),
            location_tf,
            date_tf,
            ft.Divider(height=20),
            
            # BUTTON MIT on_click VERKNÜPFT
            ft.Row([
                ft.FilledButton(
                    "Meldung erstellen", 
                    width=200, 
                    on_click=lambda e: page.run_task(save_post, e)
                ),
            ]),
            status_text,
        ],
        spacing=10,
    )
    
    return ft.Column(
        [form_column],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )