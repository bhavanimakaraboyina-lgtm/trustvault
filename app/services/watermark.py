
import io
import uuid
from pathlib import Path

from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color


def watermark_pdf(file_path, tracking_id):
    """Add bold TrustVault branding and tracking reference at top-right."""

    # Attach the original PDF pages to the writer first.
    writer = PdfWriter(clone_from=str(file_path))

    for page in writer.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        buffer = io.BytesIO()

        pdf_canvas = canvas.Canvas(
            buffer,
            pagesize=(width, height)
        )

        margin = 30

        pdf_canvas.setFillColor(
            Color(0.25, 0.25, 0.25, alpha=0.75)
        )

        pdf_canvas.setFont("Helvetica-Bold", 12)
        pdf_canvas.drawRightString(
            width - margin,
            height - margin,
            "TRUSTVAULT"
        )

        pdf_canvas.setFont("Helvetica-Bold", 9)
        pdf_canvas.drawRightString(
            width - margin,
            height - margin - 15,
            f"Tracking Reference: {tracking_id}"
        )

        pdf_canvas.save()

        buffer.seek(0)
        overlay = PdfReader(buffer).pages[0]

        page.merge_page(overlay)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)

    return output


def watermark_image(file_path):
    """Add only the TrustVault shield-and-tick logo to images."""

    image = Image.open(file_path).convert("RGBA")

    icon_size = max(
        8,
        min(64, image.width // 6, image.height // 6)
    )

    padding = max(5, icon_size // 5)
    badge_size = icon_size + (padding * 2)

    margin = max(5, icon_size // 5)

    badge = Image.new(
        "RGBA",
        (badge_size, badge_size),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(badge)

    draw.rounded_rectangle(
        (0, 0, badge_size - 1, badge_size - 1),
        radius=max(4, icon_size // 5),
        fill=(15, 23, 42, 175)
    )

    # TrustVault shield outline.
    left = padding + icon_size * 0.15
    right = padding + icon_size * 0.85
    top = padding + icon_size * 0.08
    bottom = padding + icon_size * 0.92
    center = padding + icon_size * 0.5

    shield_points = [
        (center, top),
        (right, top + icon_size * 0.13),
        (right, top + icon_size * 0.40),
        (right - icon_size * 0.05, top + icon_size * 0.62),
        (center, bottom),
        (left + icon_size * 0.05, top + icon_size * 0.62),
        (left, top + icon_size * 0.40),
        (left, top + icon_size * 0.13),
        (center, top)
    ]

    draw.line(
        shield_points,
        fill=(255, 255, 255, 240),
        width=max(1, icon_size // 14),
        joint="curve"
    )

    # Tick inside the shield.
    draw.line(
        [
            (padding + icon_size * 0.30,
             padding + icon_size * 0.50),
            (padding + icon_size * 0.44,
             padding + icon_size * 0.64),
            (padding + icon_size * 0.70,
             padding + icon_size * 0.36)
        ],
        fill=(255, 255, 255, 255),
        width=max(1, icon_size // 12),
        joint="curve"
    )

    x = max(margin, image.width - badge_size - margin)
    y = margin

    image.alpha_composite(badge, (x, y))

    output = io.BytesIO()

    if file_path.suffix.lower() in (".jpg", ".jpeg"):
        image.convert("RGB").save(
            output,
            format="JPEG",
            quality=95
        )
    else:
        image.save(output, format="PNG")

    output.seek(0)
    return output


def watermark_text(file_path, tracking_id):
    """Keep the existing TXT watermark design unchanged."""

    original_text = file_path.read_text(encoding="utf-8")

    header = (
        "========================================\n"
        "              TRUSTVAULT\n"
        "========================================\n"
        f"Tracking Reference: {tracking_id}\n"
        "========================================\n\n"
    )

    output = io.BytesIO(
        (header + original_text).encode("utf-8")
    )

    output.seek(0)
    return output


def create_watermarked_copy(file_path):
    """Create a watermarked copy based on the document extension."""

    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension in (".png", ".jpg", ".jpeg"):
        output = watermark_image(file_path)
        tracking_id = None

    elif extension == ".pdf":
        tracking_id = uuid.uuid4().hex[:12].upper()
        output = watermark_pdf(file_path, tracking_id)

    elif extension == ".txt":
        tracking_id = uuid.uuid4().hex[:12].upper()
        output = watermark_text(file_path, tracking_id)

    else:
        raise ValueError(
            "Unsupported file type for watermarking."
        )

    return output, tracking_id
