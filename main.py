# PetBuddy - Hauptanwendung.
#
# Dieses Modul ist der Einstiegspunkt der Anwendung.
# Die Hauptlogik wurde in das app/ Modul ausgelagert.

import os
import webbrowser
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
    
    # Absoluten Upload-Pfad festlegen und Verzeichnis sicherstellen
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir_abs = os.path.join(base_dir, "image_uploads")
    os.makedirs(upload_dir_abs, exist_ok=True)
    os.environ["UPLOAD_DIR"] = upload_dir_abs
    
    if os.getenv("FLY_APP_NAME") is None:
        webbrowser.open(f"http://localhost:{port}")
    
    ft.app(
        target=main,
        upload_dir=upload_dir_abs,
        view=None,
        port=port,
        host="0.0.0.0"
    )