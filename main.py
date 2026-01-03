# PetBuddy - Hauptanwendung.
# 
# Dieses Modul ist der Einstiegspunkt der Anwendung.
# Die Hauptlogik wurde in das app/ Modul ausgelagert.

import os
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
    ft.app(
        target=main,
        upload_dir="image_uploads",
        view=ft.AppView.WEB_BROWSER if os.getenv("FLY_APP_NAME") is None else None,
        port=port,
        host="0.0.0.0"
    )