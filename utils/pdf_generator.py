"""
PDF-Erstellung fuer Meldungen (Vermisst/Fundtier).
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Optional, Dict, Any, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas


def _format_date(date_str: Optional[str]) -> str:
    if not date_str:
        return "—"
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return date_str[:10]


def _extract_color_names(post_colors: List[Dict[str, Any]]) -> str:
    if not post_colors:
        return ""
    names: List[str] = []
    for pc in post_colors:
        if isinstance(pc, dict):
            color = pc.get("color") or {}
            if isinstance(color, dict):
                name = color.get("name")
                if name:
                    names.append(str(name))
    return ", ".join(names)


def _extract_post_data(post: Dict[str, Any]) -> Dict[str, str]:
    post_status = post.get("post_status") or {}
    species = post.get("species") or {}
    breed = post.get("breed") or {}
    sex = post.get("sex") or {}

    return {
        "headline": post.get("headline") or "Ohne Titel",
        "description": post.get("description") or "",
        "location_text": post.get("location_text") or "",
        "event_date": _format_date((post.get("event_date") or post.get("created_at") or "")[:10]),
        "created_at": _format_date((post.get("created_at") or "")[:10]),
        "active_label": "Aktiv" if post.get("is_active") else "Inaktiv",
        "status_name": str(post_status.get("name") or "").strip(),
        "species_name": str(species.get("name") or "").strip(),
        "breed_name": str(breed.get("name") or "").strip(),
        "sex_name": str(sex.get("name") or "").strip(),
        "colors": _extract_color_names(post.get("post_color") or []),
    }


def _draw_border(c: canvas.Canvas, width: float, height: float, margin: float) -> None:
    c.setStrokeColor(colors.red)
    c.setLineWidth(2)
    c.rect(margin / 2, margin / 2, width - margin, height - margin, stroke=1, fill=0)


def _split_long_word(
    c: canvas.Canvas,
    word: str,
    max_width: float,
    font_name: str,
    font_size: int,
) -> list[str]:
    """Splits a long word into chunks that fit max_width."""
    chunks: list[str] = []
    current = ""
    for ch in word:
        test = current + ch
        if c.stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            if current:
                chunks.append(current)
            current = ch
    if current:
        chunks.append(current)
    return chunks or [word]


def _wrap_text(
    c: canvas.Canvas,
    text: str,
    max_width: float,
    font_name: str,
    font_size: int,
) -> list[str]:
    """Wraps text to max_width and breaks long words if needed."""
    raw = text or "—"
    words = raw.split()
    if not words:
        return ["—"]

    lines: list[str] = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        if c.stringWidth(test, font_name, font_size) <= max_width:
            current = test
            continue

        if current:
            lines.append(current)
            current = ""

        if c.stringWidth(word, font_name, font_size) <= max_width:
            current = word
            continue

        for chunk in _split_long_word(c, word, max_width, font_name, font_size):
            if current:
                lines.append(current)
                current = ""
            if c.stringWidth(chunk, font_name, font_size) <= max_width:
                current = chunk
            else:
                lines.append(chunk)

    if current:
        lines.append(current)

    return lines


def _draw_wrapped_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_name: str,
    font_size: int,
    line_height: float,
) -> float:
    c.setFont(font_name, font_size)
    lines = _wrap_text(c, text, max_width, font_name, font_size)
    for line in lines:
        c.drawString(x, y, line)
        y -= line_height
    return y


def _render_post_pdf(
    c: canvas.Canvas,
    post: Dict[str, Any],
    image_bytes: Optional[bytes],
    contact_email: Optional[str],
    contact_phone: Optional[str],
    additions: Optional[str],
) -> None:
    data = _extract_post_data(post)
    status_lower = data["status_name"].lower()
    if "vermisst" in status_lower:
        title = "VERMISST-MELDUNG"
    elif "fund" in status_lower:
        title = "FUNDTIER-MELDUNG"
    else:
        title = "TIER-MELDUNG"

    width, height = A4
    margin = 18 * mm

    _draw_border(c, width, height, margin)

    y = height - margin
    c.setFont("Helvetica-Bold", 26)
    title_width = c.stringWidth(title, "Helvetica-Bold", 26)
    c.drawString((width - title_width) / 2, y - 10, title)
    y -= 40

    image_max_width = width - 2 * margin
    image_max_height = 240

    if image_bytes:
        img_reader = ImageReader(BytesIO(image_bytes))
        img_w, img_h = img_reader.getSize()
        scale = min(image_max_width / img_w, image_max_height / img_h)
        draw_w = img_w * scale
        draw_h = img_h * scale
        x = margin + (image_max_width - draw_w) / 2
        c.drawImage(
            img_reader,
            x,
            y - draw_h,
            width=draw_w,
            height=draw_h,
            preserveAspectRatio=True,
            mask="auto",
        )
        y -= draw_h + 16
    else:
        c.setStrokeColor(colors.grey)
        c.rect(margin, y - image_max_height, image_max_width, image_max_height, stroke=1, fill=0)
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(margin + 6, y - 16, "Kein Bild vorhanden")
        y -= image_max_height + 16

    def ensure_space(min_y: float) -> float:
        nonlocal y
        if y < min_y:
            c.showPage()
            _draw_border(c, width, height, margin)
            y = height - margin
        return y

    line_height = 16
    label_width = 110

    def draw_kv(label: str, value: str) -> None:
        nonlocal y
        ensure_space(margin + 80)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, f"{label}:")
        y = _draw_wrapped_text(
            c,
            value or "—",
            margin + label_width,
            y,
            width - 2 * margin - label_width,
            "Helvetica",
            12,
            line_height,
        )
        y -= 2

    draw_kv("Überschrift", data["headline"])
    draw_kv("Meldungsart", data["status_name"])
    draw_kv("Tierart", data["species_name"])
    draw_kv("Rasse", data["breed_name"])
    draw_kv("Geschlecht", data["sex_name"])
    draw_kv("Farben", data["colors"])
    draw_kv("Ort", data["location_text"])
    draw_kv("Datum", data["event_date"])

    draw_kv("Beschreibung", data["description"])

    contact_parts = []
    if contact_email:
        contact_parts.append(f"E-Mail: {contact_email}")
    if contact_phone:
        contact_parts.append(f"Telefon: {contact_phone}")
    contact_text = " | ".join(contact_parts) if contact_parts else "—"

    draw_kv("Kontakt", contact_text)

    if additions:
        draw_kv("Ergänzungen", additions)

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.grey)
    c.drawString(margin, margin - 6, f"PDF erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')}")


def create_post_pdf(
    post: Dict[str, Any],
    output_path: str,
    image_bytes: Optional[bytes],
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    additions: Optional[str] = None,
) -> None:
    """Erstellt eine PDF fuer eine Meldung.

    Args:
        post: Post-Dictionary aus der Datenbank
        output_path: Zielpfad fuer die PDF
        image_bytes: Bilddaten oder None
        contact_email: Kontakt-E-Mail (optional)
        contact_phone: Kontakt-Telefon (optional)
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    _render_post_pdf(c, post, image_bytes, contact_email, contact_phone, additions)
    c.save()


def create_post_pdf_bytes(
    post: Dict[str, Any],
    image_bytes: Optional[bytes],
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    additions: Optional[str] = None,
) -> bytes:
    """Erstellt eine PDF fuer eine Meldung und gibt Bytes zurueck."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    _render_post_pdf(c, post, image_bytes, contact_email, contact_phone, additions)
    c.save()
    buffer.seek(0)
    return buffer.read()
