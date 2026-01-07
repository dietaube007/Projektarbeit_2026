# PetBuddy - Hauptanwendung.
#
# Dieses Modul ist der Einstiegspunkt der Anwendung.
# Die Hauptlogik wurde in das app/ Modul ausgelagert.

import os
import flet as ft
from dotenv import load_dotenv

from app import PetBuddyApp
from utils.logging_config import setup_logging, get_logger

# Lade Umgebungsvariablen aus .env
load_dotenv()

# Logging initialisieren
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_to_file=os.getenv("LOG_TO_FILE", "true").lower() == "true"
)

logger = get_logger(__name__)

# Secret Key für Flet Uploads aus .env laden
os.environ["FLET_SECRET_KEY"] = os.getenv("FLET_SECRET_KEY", "")


def main(page: ft.Page):
    # App-Sprache auf Deutsch setzen (betrifft u.a. DatePicker)
    page.locale = "de-DE"

    app = PetBuddyApp(page)
    app.run()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8550))
    ft.app(
        target=main,
        upload_dir="image_uploads",
        view=ft.AppView.WEB_BROWSER if os.getenv("FLY_APP_NAME") is None else None,
        port=port,
        host="0.0.0.0"
    )