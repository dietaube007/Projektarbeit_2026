# PetBuddy - Hauptanwendung.
#
# Dieses Modul ist der Einstiegspunkt der Anwendung.
# Die Hauptlogik wurde in das app/ Modul ausgelagert.

import os
import webbrowser
import flet as ft
import uvicorn
from fastapi.responses import FileResponse, PlainTextResponse
from flet.fastapi import FastAPI, app as flet_app
from dotenv import load_dotenv

from app import PetBuddyApp
from utils.logging_config import setup_logging

# Lade Umgebungsvariablen aus .env
load_dotenv()

# Logging initialisieren
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_to_file=os.getenv("LOG_TO_FILE", "true").lower() == "true"
)

# Secret Key für Flet Uploads aus .env laden
os.environ["FLET_SECRET_KEY"] = os.getenv("FLET_SECRET_KEY", "")


def main(page: ft.Page):
    # App-Sprache auf Deutsch setzen (betrifft u.a. DatePicker)
    page.locale = "de-DE"
    page.locale_configuration = ft.LocaleConfiguration(
        supported_locales=[ft.Locale("de", "DE")],
        current_locale=ft.Locale("de", "DE"),
    )

    app = PetBuddyApp(page)
    app.run()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))

    # Absoluten Upload-Pfad festlegen und Verzeichnis sicherstellen
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir_abs = os.path.join(base_dir, "image_uploads")
    os.makedirs(upload_dir_abs, exist_ok=True)
    os.environ["UPLOAD_DIR"] = upload_dir_abs

    assets_dir_abs = os.path.join(base_dir, "assets")
    os.makedirs(os.path.join(assets_dir_abs, "pdf_exports"), exist_ok=True)

    app = FastAPI()

    @app.get("/download/{filename}")
    def download_pdf(filename: str):
        safe_name = os.path.basename(filename)
        pdf_path = os.path.join(assets_dir_abs, "pdf_exports", safe_name)
        if not os.path.exists(pdf_path):
            return PlainTextResponse("PDF nicht gefunden", status_code=404)
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=safe_name,
            headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
        )

    # Download-Route vor der Flet-App mounten
    app.mount(
        "/",
        flet_app(
            main,
            upload_dir=upload_dir_abs,
            assets_dir=assets_dir_abs,
        ),
    )

    if os.getenv("FLY_APP_NAME") is None:
        webbrowser.open(f"http://localhost:{port}")

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")