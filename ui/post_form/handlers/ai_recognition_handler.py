"""
AI Handler: UI-Updates und Event-Handler für das Meldungsformular.

Enthält:
- AI Recognition: KI-Rassenerkennung Funktionalität
- UI Updates: Status-Nachrichten, Dialogs, Formular-Updates
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Dict, Any, Optional, Callable, List

import flet as ft

from services.posts import PostStorageService
from services.ai.pet_recognition import PetRecognitionService
from ui.shared_components import show_error_dialog, show_progress_dialog, show_success_dialog
from ..components.ai_components import (
    create_consent_dialog,
    create_ai_result_content,
    create_ai_suggestion_dialog,
)


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
    # Prüfe ob Foto vorhanden (lokal oder bereits in Storage)
    if not selected_photo.get("path") and not selected_photo.get("local_path"):
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
    show_consent_dialog_callback()


async def show_consent_dialog(
    page: ft.Page,
    on_accept: Callable[[], None],
) -> None:
    """Zeigt den Einverständnisdialog für die KI-Erkennung.
    
    Args:
        page: Flet Page-Instanz
        on_accept: Callback der aufgerufen wird wenn Nutzer akzeptiert
    """
    dlg = create_consent_dialog(page=page, on_accept=on_accept)
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
        await asyncio.sleep(0.05)
        
        # Prüfe auf Abbruch
        if ai_recognition_cancelled_ref.get("cancelled"):
            page.close(progress_dlg)
            return
        
        # Bilddaten: lokal oder aus Storage
        local_path = selected_photo.get("local_path")
        storage_path = selected_photo.get("path")
        if not local_path and not storage_path:
            show_error_dialog(
                page,
                "Kein Bild vorhanden",
                "Bitte laden Sie zuerst ein Foto hoch, bevor Sie die KI-Erkennung starten.",
            )
            page.close(progress_dlg)
            return
        
        try:
            if local_path:
                image_data = post_storage_service.read_local_image_bytes(local_path)
            else:
                image_data = post_storage_service.download_post_image(storage_path)
            if not image_data:
                show_error_dialog(page, "Fehler", "Fehler beim Laden des Bildes")
                page.close(progress_dlg)
                return
        except Exception as ex:
            show_error_dialog(page, "Fehler", f"Fehler beim Laden des Bildes: {ex}")
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
        else:
            suggested_breed = result.get("suggested_breed")
            suggested_species = result.get("suggested_species")
            confidence = result.get("confidence", 0.0)
            base_message = result.get("error") or (
                "Die KI konnte das Tier nicht sicher erkennen. "
                "Bitte versuchen Sie ein anderes Bild oder tragen Sie die Rasse manuell ein. "
                "Sie können auch das Tierheim kontaktieren und das Tier beschreiben."
            )
            if suggested_breed:
                confidence_percent = int(confidence * 100)
                suggestion_text = f"Vorschlag: {suggested_species or 'Tier'}, {suggested_breed} ({confidence_percent}% Konfidenz)"
                message = f"{base_message}\n\n{suggestion_text}"
            else:
                message = base_message
            show_error_dialog(page, "KI-Erkennung", message)
                
    except Exception as ex:
        show_error_dialog(page, "Fehler", f"Fehler: {ex}")
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
    form_scroll_column: Optional[ft.Control] = None,
) -> None:
    """Zeigt das KI-Erkennungsergebnis an.
    
    Args:
        ai_result_container: Container für KI-Ergebnis
        result: Ergebnis-Dictionary von der Erkennung
        on_accept: Callback wenn Nutzer Ergebnis übernimmt
        on_reject: Callback wenn Nutzer Ergebnis ablehnt
        page: Flet Page-Instanz
        form_scroll_column: Optionale scrollbare Column, um zum Ergebnis zu scrollen
    """
    result_content = create_ai_result_content(
        result=result,
        on_accept=on_accept,
        on_reject=on_reject,
    )
    
    ai_result_container.content = result_content
    ai_result_container.visible = True
    if getattr(ai_result_container, "page", None):
        ai_result_container.update()
    else:
        page.update()
    
    # Ergebnis in den sichtbaren Bereich scrollen
    if form_scroll_column and hasattr(form_scroll_column, "scroll_to"):
        try:
            form_scroll_column.scroll_to(
                scroll_key="ai_result_container",
                duration=300,
            )
            page.update()
        except Exception:
            pass


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
    dlg = create_ai_suggestion_dialog(
        page=page,
        error_message=error_message,
        suggested_breed=suggested_breed,
        suggested_species=suggested_species,
        confidence=confidence,
        on_accept=on_accept,
    )
    page.open(dlg)


# ─────────────────────────────────────────────────────────────
# View-spezifische Handler (ehemalige View-Methoden)
# ─────────────────────────────────────────────────────────────

async def handle_view_start_ai_recognition(
    page: ft.Page,
    selected_photo: Dict[str, Any],
    post_statuses: List[Dict[str, Any]],
    meldungsart: ft.SegmentedButton,
    show_consent_dialog_callback: Callable[[], None],
) -> None:
    """Startet die KI-Rassenerkennung (View-Wrapper).
    
    Args:
        page: Flet Page-Instanz
        selected_photo: Dictionary mit Foto-Informationen
        post_statuses: Liste der Meldungsarten
        meldungsart: SegmentedButton für Meldungsart
        show_consent_dialog_callback: Callback zum Anzeigen des Einverständnisdialogs
    """
    await handle_start_ai_recognition(
        page=page,
        selected_photo=selected_photo,
        post_statuses=post_statuses,
        meldungsart=meldungsart,
        show_consent_dialog_callback=show_consent_dialog_callback,
    )


async def handle_view_show_consent_dialog(
    page: ft.Page,
    on_accept_callback: Callable[[], None],
) -> None:
    """Zeigt den Einverständnisdialog für die KI-Erkennung (View-Wrapper).
    
    Args:
        page: Flet Page-Instanz
        on_accept_callback: Callback der aufgerufen wird wenn Nutzer akzeptiert
    """
    await show_consent_dialog(
        page=page,
        on_accept=on_accept_callback,
    )


async def handle_view_perform_ai_recognition(
    page: ft.Page,
    recognition_service: PetRecognitionService,
    post_storage_service: PostStorageService,
    selected_photo: Dict[str, Any],
    ai_recognition_cancelled_ref: Dict[str, bool],
    show_status_callback: Callable[[str, bool, bool], None],
    show_ai_result_callback: Callable[[Dict[str, Any]], None],
    show_ai_suggestion_callback: Callable[[str, Optional[str], Optional[str], float], None],
) -> None:
    """Führt die KI-Erkennung durch (View-Wrapper).
    
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
    await perform_ai_recognition(
        page=page,
        recognition_service=recognition_service,
        post_storage_service=post_storage_service,
        selected_photo=selected_photo,
        ai_recognition_cancelled_ref=ai_recognition_cancelled_ref,
        show_status_callback=show_status_callback,
        show_ai_result_callback=show_ai_result_callback,
        show_ai_suggestion_callback=show_ai_suggestion_callback,
    )


def handle_view_show_ai_result(
    ai_result_container: ft.Container,
    result: Dict[str, Any],
    ai_result: dict,  # dict mit "result" key für Mutability
    on_accept: Callable[[], None],
    on_reject: Callable[[], None],
    page: ft.Page,
    form_scroll_column: Optional[ft.Control] = None,
) -> None:
    """Zeigt das KI-Erkennungsergebnis an (View-Wrapper).
    
    Args:
        ai_result_container: Container für KI-Ergebnis
        result: Ergebnis-Dictionary von der Erkennung
        ai_result: Dictionary mit "result" key (wird aktualisiert)
        on_accept: Callback wenn Nutzer Ergebnis übernimmt
        on_reject: Callback wenn Nutzer Ergebnis ablehnt
        page: Flet Page-Instanz
        form_scroll_column: Optionale scrollbare Column zum Ergebnis
    """
    ai_result["result"] = result
    show_ai_result(
        ai_result_container=ai_result_container,
        result=result,
        on_accept=on_accept,
        on_reject=on_reject,
        page=page,
        form_scroll_column=form_scroll_column,
    )


def handle_view_accept_ai_result(
    ai_result: dict,  # dict mit "result" key
    species_list: List[Dict[str, Any]],
    breeds_by_species: Dict[int, List[Dict[str, Any]]],
    species_dd: ft.Dropdown,
    breed_dd: ft.Dropdown,
    info_tf: ft.TextField,
    ai_result_container: ft.Container,
    page: ft.Page,
    update_breeds_callback: Callable[[], None],
    show_status_callback: Callable[[str, bool, bool], None],
    update_description_counter: Optional[Callable[[], None]] = None,
) -> None:
    """Übernimmt das KI-Erkennungsergebnis in die Formularfelder (View-Wrapper).
    
    Args:
        ai_result: Dictionary mit "result" key
        species_list: Liste der Tierarten
        breeds_by_species: Dictionary mit Rassen gruppiert nach Tierart-ID
        species_dd: Tierart-Dropdown
        breed_dd: Rasse-Dropdown
        info_tf: TextField für Beschreibung
        ai_result_container: Container für KI-Ergebnis
        page: Flet Page-Instanz
        update_breeds_callback: Callback zum Aktualisieren der Rassen-Dropdown
        show_status_callback: Callback für Status-Nachrichten
    """
    result = ai_result.get("result")
    if not result:
        return
    
    species_name = result["species"]
    species_id = None
    for species in species_list:
        if species["name"].lower() == species_name.lower():
            species_id = species["id"]
            break
    
    if species_id:
        species_dd.value = str(species_id)
        update_breeds_callback()
        
        # Warte kurz, dann Rasse setzen
        async def set_breed_async():
            # Rassen-Dropdown sollte jetzt aktualisiert sein
            breed_name = result["breed"]
            breed_id = None
            
            if species_id and species_id in breeds_by_species:
                for breed in breeds_by_species[species_id]:
                    if breed["name"].lower() == breed_name.lower():
                        breed_id = breed["id"]
                        break
            
            if breed_id:
                breed_dd.value = str(breed_id)
            
            confidence_percent = int(result["confidence"] * 100)
            ai_info = f"[KI-Erkennung: {species_name}, Rasse: {breed_name} ({confidence_percent}% Konfidenz)]"
            
            current_description = info_tf.value or ""
            if current_description:
                info_tf.value = f"{ai_info}\n\n{current_description}"
            else:
                info_tf.value = ai_info
            if update_description_counter:
                update_description_counter()
            
            ai_result_container.visible = False
            show_success_dialog(page, "KI-Vorschlag übernommen", "Die KI-Erkennung wurde übernommen.")
            page.update()
        
        page.run_task(set_breed_async)


def handle_view_reject_ai_result(
    ai_result: dict,  # dict mit "result" key
    ai_result_container: ft.Container,
    page: ft.Page,
    show_status_callback: Callable[[str, bool, bool], None],
) -> None:
    """Lehnt das KI-Erkennungsergebnis ab (View-Wrapper).
    
    Args:
        ai_result: Dictionary mit "result" key (wird zurückgesetzt)
        ai_result_container: Container für KI-Ergebnis
        page: Flet Page-Instanz
        show_status_callback: Callback für Status-Nachrichten
    """
    ai_result["result"] = None
    ai_result_container.visible = False
    show_error_dialog(
        page,
        "KI-Vorschlag abgelehnt",
        "Bitte tragen Sie die Daten manuell ein.",
    )
    page.update()


def handle_view_show_ai_suggestion_wrapper(
    page: ft.Page,
    error_message: str,
    suggested_breed: Optional[str],
    suggested_species: Optional[str],
    confidence: float,
    on_accept: Callable[[str, Optional[str]], None],
) -> None:
    """Zeigt einen Dialog mit KI-Vorschlag bei niedriger Konfidenz (View-Wrapper).
    
    Args:
        page: Flet Page-Instanz
        error_message: Fehlermeldung
        suggested_breed: Vorgeschlagene Rasse
        suggested_species: Vorgeschlagene Tierart
        confidence: Konfidenz-Wert
        on_accept: Callback wenn Nutzer Vorschlag übernimmt
    """
    show_ai_suggestion_dialog(
        page=page,
        error_message=error_message,
        suggested_breed=suggested_breed or "",
        suggested_species=suggested_species,
        confidence=confidence,
        on_accept=on_accept,
    )


# ════════════════════════════════════════════════════════════════════
# High-Level AI Recognition Flow (ersetzt View-Wrapper)
# ════════════════════════════════════════════════════════════════════

async def handle_ai_recognition_flow(
    page: ft.Page,
    recognition_service: PetRecognitionService,
    post_storage_service: PostStorageService,
    selected_photo: Dict[str, Any],
    post_statuses: List[Dict[str, Any]],
    meldungsart: ft.SegmentedButton,
    ai_result: Dict[str, Any],
    ai_recognition_cancelled_ref: Dict[str, bool],
    species_list: List[Dict[str, Any]],
    breeds_by_species: Dict[int, List[Dict[str, Any]]],
    species_dd: ft.Dropdown,
    breed_dd: ft.Dropdown,
    info_tf: ft.TextField,
    ai_result_container: ft.Container,
    show_status_callback: Callable[[str, bool, bool], None],
    update_breeds_callback: Callable[[], None],
    form_scroll_column: Optional[ft.Control] = None,
    update_description_counter: Optional[Callable[[], None]] = None,
) -> None:
    """Kompletter AI-Recognition-Flow von Start bis Ergebnis.
    
    Diese Funktion kapselt den gesamten Flow und ersetzt die Wrapper-Methoden
    in der View. Sie verwaltet intern alle Callbacks und den Flow.
    
    Args:
        page: Flet Page-Instanz
        recognition_service: PetRecognitionService-Instanz
        post_storage_service: PostStorageService-Instanz
        selected_photo: Dictionary mit Foto-Informationen
        post_statuses: Liste der Meldungsarten
        meldungsart: SegmentedButton für Meldungsart
        ai_result: Dictionary mit "result" key (wird aktualisiert)
        ai_recognition_cancelled_ref: Dictionary mit Cancel-Flag
        species_list: Liste der Tierarten
        breeds_by_species: Dictionary mit Rassen gruppiert nach Tierart-ID
        species_dd: Tierart-Dropdown
        breed_dd: Rasse-Dropdown
        info_tf: TextField für Beschreibung
        ai_result_container: Container für KI-Ergebnis
        show_status_callback: Callback für Status-Nachrichten
        update_breeds_callback: Callback zum Aktualisieren der Rassen-Dropdown
        form_scroll_column: Optionale scrollbare Column zum KI-Ergebnis
    """
    # Callback für Consent-Dialog
    async def show_consent_dialog_callback() -> None:
        async def on_accept_callback() -> None:
            # Führt die KI-Erkennung durch
            await handle_view_perform_ai_recognition(
                page=page,
                recognition_service=recognition_service,
                post_storage_service=post_storage_service,
                selected_photo=selected_photo,
                ai_recognition_cancelled_ref=ai_recognition_cancelled_ref,
                show_status_callback=show_status_callback,
                show_ai_result_callback=show_ai_result_callback,
                show_ai_suggestion_callback=show_ai_suggestion_callback,
            )
        
        await handle_view_show_consent_dialog(
            page=page,
            on_accept_callback=lambda: page.run_task(on_accept_callback),
        )
    
    # Callback für AI-Ergebnis anzeigen
    def show_ai_result_callback(result: Dict[str, Any]) -> None:
        handle_view_show_ai_result(
            ai_result_container=ai_result_container,
            result=result,
            ai_result=ai_result,
            on_accept=accept_ai_result_callback,
            on_reject=reject_ai_result_callback,
            page=page,
            form_scroll_column=form_scroll_column,
        )
    
    # Callback für AI-Ergebnis akzeptieren
    def accept_ai_result_callback() -> None:
        handle_view_accept_ai_result(
            ai_result=ai_result,
            species_list=species_list,
            breeds_by_species=breeds_by_species,
            species_dd=species_dd,
            breed_dd=breed_dd,
            info_tf=info_tf,
            ai_result_container=ai_result_container,
            page=page,
            update_breeds_callback=update_breeds_callback,
            show_status_callback=show_status_callback,
            update_description_counter=update_description_counter,
        )
    
    # Callback für AI-Ergebnis ablehnen
    def reject_ai_result_callback() -> None:
        handle_view_reject_ai_result(
            ai_result=ai_result,
            ai_result_container=ai_result_container,
            page=page,
            show_status_callback=show_status_callback,
        )
    
    # Callback für AI-Vorschlag bei niedriger Konfidenz
    def show_ai_suggestion_callback(
        error_message: str,
        suggested_breed: Optional[str],
        suggested_species: Optional[str],
        confidence: float,
    ) -> None:
        def on_accept(breed: str, species: Optional[str]):
            # TODO: Ähnlich wie accept_ai_result_callback, aber mit niedrigerer Konfidenz
            # Kann später implementiert werden
            pass
        
        handle_view_show_ai_suggestion_wrapper(
            page=page,
            error_message=error_message,
            suggested_breed=suggested_breed,
            suggested_species=suggested_species,
            confidence=confidence,
            on_accept=on_accept,
        )
    
    # Starte den AI-Recognition-Flow
    await handle_view_start_ai_recognition(
        page=page,
        selected_photo=selected_photo,
        post_statuses=post_statuses,
        meldungsart=meldungsart,
        show_consent_dialog_callback=lambda: page.run_task(show_consent_dialog_callback),
    )
