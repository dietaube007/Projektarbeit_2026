"""
AI Recognition-Feature: UI und Logik für KI-Rassenerkennung.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Dict, Any, Optional, Callable, List

import flet as ft

from services.posts import PostStorageService
from services.ai.pet_recognition import PetRecognitionService
from utils.logging_config import get_logger
from ui.components import show_error_dialog, show_progress_dialog

logger = get_logger(__name__)


async def handle_start_ai_recognition(
    page: ft.Page,
    selected_photo: Dict[str, Any],
    post_statuses: List[Dict[str, Any]],
    meldungsart: ft.SegmentedButton,
    show_consent_dialog_callback: Callable[[], None],
) -> None:
    """Startet die KI-Rassenerkennung mit Einverständnisabfrage.
    
    Args:
        page: Flet Page-Instanz
        selected_photo: Dictionary mit Foto-Informationen
        post_statuses: Liste der Meldungsarten
        meldungsart: SegmentedButton für Meldungsart
        show_consent_dialog_callback: Callback zum Anzeigen des Einverständnisdialogs
    """
    # Prüfe ob Foto vorhanden
    if not selected_photo.get("path"):
        show_error_dialog(
            page,
            "Kein Foto",
            "Bitte laden Sie zuerst ein Foto hoch, bevor Sie die KI-Erkennung starten."
        )
        return
    
    # Prüfe ob "Fundtier" ausgewählt ist
    selected_id = list(meldungsart.selected)[0] if meldungsart.selected else None
    selected_status = None
    for status in post_statuses:
        if str(status["id"]) == selected_id:
            selected_status = status["name"].lower()
            break
    
    if selected_status != "fundtier":
        show_error_dialog(
            page,
            "Nur für Fundtiere",
            "Die KI-Rassenerkennung ist nur für gefundene Tiere verfügbar. "
            "Besitzer vermisster Tiere kennen in der Regel die Rasse ihres Tieres bereits."
        )
        return
    
    # Einverständnisdialog anzeigen
    await show_consent_dialog_callback()


async def show_consent_dialog(
    page: ft.Page,
    on_accept: Callable[[], None],
) -> None:
    """Zeigt den Einverständnisdialog für die KI-Erkennung.
    
    Args:
        page: Flet Page-Instanz
        on_accept: Callback der aufgerufen wird wenn Nutzer akzeptiert
    """
    def on_accept_handler(e):
        page.close(dlg)
        on_accept()
    
    def on_decline_handler(e):
        page.close(dlg)
    
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            [
                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.PURPLE_600, size=24),
                ft.Text("KI-Rassenerkennung", size=16, weight=ft.FontWeight.W_600),
            ],
            spacing=8,
        ),
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Einverständniserklärung:",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "Das hochgeladene Bild wird durch eine KI analysiert, um die Tierart und Rasse zu erkennen. "
                        "Die Analyse erfolgt lokal und das Bild wird nicht an externe Dienste gesendet.",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                    ft.Divider(),
                    ft.Text(
                        "Wichtige Hinweise:",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "• Die KI-Erkennung dient nur als Vorschlag\n"
                        "• Es gibt keine Garantie für die Richtigkeit\n"
                        "• Sie können den Vorschlag ablehnen und selbst eintragen\n"
                        "• Bei Unsicherheit kontaktieren Sie ein Tierheim",
                        size=12,
                        color=ft.Colors.GREY_700,
                    ),
                ],
                spacing=8,
                tight=True,
            ),
            width=400,
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=on_decline_handler),
            ft.FilledButton("Akzeptieren & Starten", on_click=on_accept_handler),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    page.open(dlg)


async def perform_ai_recognition(
    page: ft.Page,
    recognition_service: PetRecognitionService,
    post_storage_service: PostStorageService,
    selected_photo: Dict[str, Any],
    ai_recognition_cancelled_ref: Dict[str, bool],
    show_status_callback: Callable[[str, bool, bool], None],
    show_ai_result_callback: Callable[[Dict[str, Any]], None],
    show_ai_suggestion_callback: Callable[[str, Optional[str], Optional[str], float], None],
) -> None:
    """Führt die KI-Erkennung durch.
    
    Args:
        page: Flet Page-Instanz
        recognition_service: PetRecognitionService-Instanz
        post_storage_service: PostStorageService-Instanz
        selected_photo: Dictionary mit Foto-Informationen
        ai_recognition_cancelled_ref: Dictionary mit Cancel-Flag (wird modifiziert)
        show_status_callback: Callback für Status-Nachrichten
        show_ai_result_callback: Callback zum Anzeigen des Ergebnisses
        show_ai_suggestion_callback: Callback zum Anzeigen eines Vorschlags bei niedriger Konfidenz
    """
    try:
        # Reset Cancel-Flag
        ai_recognition_cancelled_ref["cancelled"] = False
        
        # Zeige Fortschrittsdialog
        progress_dlg = show_progress_dialog(page, "KI analysiert das Bild...")
        show_status_callback("KI analysiert das Bild...", is_error=False, is_loading=True)
        await asyncio.sleep(0.05)
        
        # Prüfe auf Abbruch
        if ai_recognition_cancelled_ref.get("cancelled"):
            page.close(progress_dlg)
            return
        
        # Hole Bilddaten vom Storage
        if not selected_photo.get("path"):
            show_status_callback("Kein Bild vorhanden", is_error=True, is_loading=False)
            page.close(progress_dlg)
            return
        
        # Lade Bild von Supabase über Service
        try:
            image_data = post_storage_service.download_post_image(selected_photo["path"])
            if not image_data:
                show_status_callback("Fehler beim Laden des Bildes", is_error=True, is_loading=False)
                page.close(progress_dlg)
                return
        except Exception as ex:
            show_status_callback(f"Fehler beim Laden des Bildes: {ex}", is_error=True, is_loading=False)
            page.close(progress_dlg)
            return
        
        # Prüfe erneut auf Abbruch vor der Analyse
        if ai_recognition_cancelled_ref.get("cancelled"):
            page.close(progress_dlg)
            return
        
        # Führe Erkennung in einem Executor aus
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(recognition_service.recognize_pet, image_data)
        
        # Warte auf das Ergebnis und prüfe periodisch auf Abbruch
        result = None
        while not future.done():
            await asyncio.sleep(0.1)
            if ai_recognition_cancelled_ref.get("cancelled"):
                executor.shutdown(wait=False, cancel_futures=True)
                page.close(progress_dlg)
                return
        
        # Hole das Ergebnis
        result = future.result()
        executor.shutdown(wait=False)
        
        # Finale Abbruch-Prüfung nach der Erkennung
        if ai_recognition_cancelled_ref.get("cancelled"):
            page.close(progress_dlg)
            return
        
        page.close(progress_dlg)
        
        if result["success"]:
            show_ai_result_callback(result)
            show_status_callback("Erkennung abgeschlossen!", is_error=False, is_loading=False)
        else:
            # Wenn es einen Vorschlag gibt, biete Übernahme in die Beschreibung an
            suggested_breed = result.get("suggested_breed")
            suggested_species = result.get("suggested_species")
            if suggested_breed:
                show_ai_suggestion_callback(
                    result.get("error") or "Die KI konnte das Tier nicht sicher erkennen.",
                    suggested_breed,
                    suggested_species,
                    result.get("confidence", 0.0),
                )
            else:
                show_error_dialog(
                    page,
                    "Erkennung fehlgeschlagen",
                    result.get("error") or "Die KI konnte das Tier nicht sicher erkennen. "
                    "Bitte versuchen Sie ein anderes Bild oder tragen Sie die Rasse manuell ein. "
                    "Sie können auch das Tierheim kontaktieren und das Tier beschreiben."
                )
            show_status_callback("", is_error=False, is_loading=False)
                
    except Exception as ex:
        show_status_callback(f"Fehler: {ex}", is_error=True, is_loading=False)
        if 'progress_dlg' in locals():
            try:
                page.close(progress_dlg)
            except Exception:
                pass


def show_ai_result(
    ai_result_container: ft.Container,
    result: Dict[str, Any],
    on_accept: Callable[[], None],
    on_reject: Callable[[], None],
    page: ft.Page,
) -> None:
    """Zeigt das KI-Erkennungsergebnis an.
    
    Args:
        ai_result_container: Container für KI-Ergebnis
        result: Ergebnis-Dictionary von der Erkennung
        on_accept: Callback wenn Nutzer Ergebnis übernimmt
        on_reject: Callback wenn Nutzer Ergebnis ablehnt
        page: Flet Page-Instanz
    """
    confidence_percent = int(result["confidence"] * 100)
    
    result_content = ft.Column(
        [
            ft.Row(
                [
                    ft.Icon(ft.Icons.AUTO_AWESOME, color=ft.Colors.PURPLE_600, size=20),
                    ft.Text(
                        "KI-Erkennungsergebnis",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PURPLE_900,
                    ),
                ],
                spacing=8,
            ),
            ft.Divider(height=10, color=ft.Colors.PURPLE_200),
            ft.Text(
                f"Tierart: {result['species']}",
                size=13,
                weight=ft.FontWeight.W_600,
            ),
            ft.Text(
                f"Rasse: {result['breed']}",
                size=13,
                weight=ft.FontWeight.W_600,
            ),
            ft.Text(
                f"Konfidenz: {confidence_percent}%",
                size=12,
                color=ft.Colors.GREY_700,
            ),
            ft.Container(
                content=ft.Text(
                    "Hinweis: Dies ist nur ein KI-Vorschlag ohne Garantie auf Richtigkeit.",
                    size=11,
                    color=ft.Colors.ORANGE_800,
                    italic=True,
                ),
                padding=8,
                bgcolor=ft.Colors.ORANGE_50,
                border_radius=4,
            ),
            ft.Divider(height=10, color=ft.Colors.PURPLE_200),
            ft.Row(
                [
                    ft.TextButton(
                        "Ablehnen",
                        icon=ft.Icons.CLOSE,
                        on_click=lambda _: on_reject(),
                    ),
                    ft.FilledButton(
                        "Übernehmen",
                        icon=ft.Icons.CHECK,
                        on_click=lambda _: on_accept(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
                spacing=10,
            ),
        ],
        spacing=8,
    )
    
    ai_result_container.content = result_content
    ai_result_container.visible = True
    page.update()


def show_ai_suggestion_dialog(
    page: ft.Page,
    error_message: str,
    suggested_breed: str,
    suggested_species: Optional[str],
    confidence: float,
    on_accept: Callable[[str, Optional[str]], None],
) -> None:
    """Zeigt einen Dialog mit KI-Vorschlag bei niedriger Konfidenz.
    
    Args:
        page: Flet Page-Instanz
        error_message: Fehlermeldung
        suggested_breed: Vorgeschlagene Rasse
        suggested_species: Vorgeschlagene Tierart
        confidence: Konfidenz-Wert
        on_accept: Callback wenn Nutzer Vorschlag übernimmt
    """
    confidence_percent = int(confidence * 100)
    
    def on_accept_handler(e):
        page.close(dlg)
        on_accept(suggested_breed, suggested_species)
    
    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("KI-Vorschlag (niedrige Konfidenz)"),
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(error_message, size=12),
                    ft.Divider(),
                    ft.Text(f"Vorgeschlagene Rasse: {suggested_breed}", size=13, weight=ft.FontWeight.W_600),
                    suggested_species and ft.Text(f"Vorgeschlagene Tierart: {suggested_species}", size=13),
                    ft.Text(f"Konfidenz: {confidence_percent}%", size=12, color=ft.Colors.GREY_700),
                    ft.Container(
                        content=ft.Text(
                            "Hinweis: Die Konfidenz ist niedrig. Bitte prüfen Sie den Vorschlag sorgfältig.",
                            size=11,
                            color=ft.Colors.ORANGE_800,
                            italic=True,
                        ),
                        padding=8,
                        bgcolor=ft.Colors.ORANGE_50,
                        border_radius=4,
                    ),
                ],
                spacing=8,
                tight=True,
            ),
            width=400,
        ),
        actions=[
            ft.TextButton("Abbrechen", on_click=lambda e: page.close(dlg)),
            ft.FilledButton("Trotzdem übernehmen", on_click=on_accept_handler),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    page.open(dlg)
