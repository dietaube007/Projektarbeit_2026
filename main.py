# PetBuddy - Hauptanwendung.
# 
# Dieses Modul ist der Einstiegspunkt der Anwendung.
# Die Hauptlogik wurde in das app/ Modul ausgelagert.

import os
import webbrowser
import flet as ft
from dotenv import load_dotenv

from app import PetBuddyApp

# Lade Umgebungsvariablen aus .env
load_dotenv()

# Secret Key für Flet Uploads aus .env laden
os.environ["FLET_SECRET_KEY"] = os.getenv("FLET_SECRET_KEY", "")


def main(page: ft.Page):
    app = PetBuddyApp(page)
    app.run()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8550))
    
    # Absoluten Upload-Pfad festlegen und Verzeichnis sicherstellen
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir_abs = os.path.join(base_dir, "image_uploads")
    os.makedirs(upload_dir_abs, exist_ok=True)
    # Für Konsistenz auch als Umgebungsvariable bereitstellen
    os.environ["UPLOAD_DIR"] = upload_dir_abs
    
    # Öffne Browser automatisch mit localhost (nur lokal, nicht auf Fly.io)
    if os.getenv("FLY_APP_NAME") is None:
        webbrowser.open(f"http://localhost:{port}")
    
    ft.app(
        target=main,
        upload_dir=upload_dir_abs,
        view=None,  # Kein automatischer Browser-Start durch Flet
        port=port,
        host="0.0.0.0"
    )