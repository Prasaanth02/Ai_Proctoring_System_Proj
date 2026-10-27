import re
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
ACCENT      = colors.HexColor("#4F46E5")   # indigo
ACCENT_LIGHT= colors.HexColor("#EEF2FF")
DARK        = colors.HexColor("#1E1B4B")
MUTED       = colors.HexColor("#6B7280")
WHITE       = colors.white
BLACK       = colors.HexColor("#111827")
ROW_ALT     = colors.HexColor("#F9FAFB")
BORDER      = colors.HexColor("#E5E7EB")


def _styles():
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "cover_title": s("cover_title",
            fontName="Helvetica-Bold", fontSize=26,
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=6),
        "cover_sub": s("cover_sub",
            fontName="Helvetica", fontSize=11,
            textColor=colors.HexColor("#C7D2FE"), alignment=TA_CENTER),
        "h1": s("h1",
            fontName="Helvetica-Bold", fontSize=18,
            textColor=DARK, spaceBefore=18, spaceAfter=6),
        "h2": s("h2",
            fontName="Helvetica-Bold", fontSize=13,
            textColor=ACCENT, spaceBefore=14, spaceAfter=4),
        "h3": s("h3",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=DARK, spaceBefore=10, spaceAfter=3),
        "body": s("body",
            fontName="Helvetica", fontSize=10,
            textColor=BLACK, leading=16, spaceAfter=4),
        "bullet": s("bullet",
            fontName="Helvetica", fontSize=10,
            textColor=BLACK, leading=15, leftIndent=14),
        "req_id": s("req_id",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=ACCENT, leading=15, leftIndent=14),
        "muted": s("muted",
            fontName="Helvetica-Oblique", fontSize=9,
            textColor=MUTED, spaceAfter=2),
    }


def markdown_to_pdf(markdown_text: str) -> bytes:
    """Convert BRD markdown string to a styled PDF, return bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.2*cm, rightMargin=2.2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="Business Requirements Document",
    )

    st = _styles()
    story = []

    # ── Cover block ──────────────────────────────────────────────────────────
    page_w = A4[0] - 4.4*cm
    cover_data = [[
        Paragraph("Business Requirements Document", st["cover_title"]),
    ]]
    cover_table = Table(cover_data, colWidths=[page_w])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), ACCENT),
        ("TOPPADDING",    (0,0), (-1,-1), 22),
        ("BOTTOMPADDING", (0,0), (-1,-1), 22),
        ("LEFTPADDING",   (0,0), (-1,-1), 18),
        ("RIGHTPADDING",  (0,0), (-1,-1), 18),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 0.3*cm))

    # ── Parse markdown lines ─────────────────────────────────────────────────
    lines = markdown_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # Skip the top-level # heading (already in cover)
        if line.startswith("# "):
            i += 1
            continue

        # H2
        if line.startswith("## "):
            text = line[3:].strip()
            story.append(Spacer(1, 0.2*cm))
            story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
            story.append(Paragraph(text, st["h2"]))
            i += 1
            continue

        # H3
        if line.startswith("### "):
            story.append(Paragraph(line[4:].strip(), st["h3"]))
            i += 1
            continue

        # Table detection
        if "|" in line and i + 1 < len(lines) and re.match(r"[\|\s\-:]+", lines[i+1]):
            table_lines = []
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            story.append(_build_table(table_lines, page_w))
            story.append(Spacer(1, 0.2*cm))
            continue

        # Bullet / numbered list
        if re.match(r"^(\-|\*|\d+\.)\s", line):
            bullets = []
            while i < len(lines) and re.match(r"^(\-|\*|\d+\.)\s", lines[i].rstrip()):
                item_text = re.sub(r"^(\-|\*|\d+\.)\s+", "", lines[i].rstrip())
                item_text = _inline(item_text)
                # FR/NFR IDs get accent colour
                if re.match(r"^(FR|NFR)-\d+", item_text):
                    bullets.append(ListItem(Paragraph(item_text, st["req_id"]), leftIndent=14))
                else:
                    bullets.append(ListItem(Paragraph(item_text, st["bullet"]), leftIndent=14))
                i += 1
            story.append(ListFlowable(bullets, bulletType="bullet", start="•",
                                      bulletFontSize=8, bulletColor=ACCENT,
                                      leftIndent=10, spaceBefore=2, spaceAfter=4))
            continue

        # Blank line
        if not line.strip():
            story.append(Spacer(1, 0.15*cm))
            i += 1
            continue

        # Normal paragraph
        story.append(Paragraph(_inline(line), st["body"]))
        i += 1

    doc.build(story)
    return buf.getvalue()


def _inline(text: str) -> str:
    """Convert inline markdown bold/italic to reportlab XML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`",       r"<font name='Courier'>\1</font>", text)
    # Escape bare & that aren't already entities
    text = re.sub(r"&(?!amp;|lt;|gt;|quot;)", "&amp;", text)
    return text


def _build_table(lines: list, page_w: float):
    """Build a reportlab Table from markdown table lines."""
    rows = []
    for line in lines:
        if re.match(r"[\|\s\-:]+$", line.replace("|", "").strip()):
            continue  # separator row
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)

    if not rows:
        return Spacer(1, 0)

    col_count = max(len(r) for r in rows)
    col_w = page_w / col_count

    st = _styles()
    table_data = []
    for r_idx, row in enumerate(rows):
        # pad short rows
        while len(row) < col_count:
            row.append("")
        style = st["req_id"] if r_idx == 0 else st["body"]
        table_data.append([Paragraph(cell, style) for cell in row])

    t = Table(table_data, colWidths=[col_w] * col_count, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  ACCENT),
        ("TEXTCOLOR",    (0,0), (-1,0),  WHITE),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, ROW_ALT]),
        ("GRID",         (0,0), (-1,-1), 0.5, BORDER),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
    ]))
    return t
