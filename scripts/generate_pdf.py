#!/usr/bin/env python3
"""
generate_pdf.py -- Convert all World of Protocols markdown files into a single PDF.

Uses ReportLab (Platypus) to produce a professional, organized PDF with:
  - Cover page
  - Table of contents with clickable links
  - Category divider pages
  - Parsed markdown content (headings, tables, code blocks, bullets, etc.)

Usage:
    python scripts/generate_pdf.py [--output PATH]

Default output: maps/world-of-protocols.pdf
"""

import argparse
import base64
import hashlib
import io
import re
import sys
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.75 * inch

GITHUB_URL = "https://github.com/yepher/world_of_protocols"

# Mermaid rendering cache directory
MERMAID_CACHE_DIR = Path(__file__).resolve().parent.parent / ".mermaid_cache"

# Global flag -- set by CLI --no-diagrams
SKIP_MERMAID = False

import shutil
import subprocess
import tempfile
import time

def _find_mmdc() -> str | None:
    """Find mermaid-cli (mmdc) binary or npx."""
    mmdc = shutil.which("mmdc")
    if mmdc:
        return mmdc
    # Check if npx is available (will use npx @mermaid-js/mermaid-cli)
    npx = shutil.which("npx")
    if npx:
        return npx
    return None

def _render_mermaid_local(code: str, output_path: Path) -> bool:
    """Render mermaid diagram locally using mmdc or npx mmdc."""
    mmdc = shutil.which("mmdc")
    with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", delete=False) as f:
        f.write(code)
        input_path = f.name
    try:
        if mmdc:
            cmd = [mmdc, "-i", input_path, "-o", str(output_path), "-b", "white", "--scale", "2"]
        else:
            npx = shutil.which("npx")
            if not npx:
                return False
            cmd = [npx, "-y", "@mermaid-js/mermaid-cli", "-i", input_path, "-o", str(output_path), "-b", "white", "--scale", "2"]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 100
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False
    finally:
        Path(input_path).unlink(missing_ok=True)

def _render_mermaid_api(code: str, output_path: Path) -> bool:
    """Render mermaid diagram via mermaid.ink API with rate limiting and retry."""
    encoded = base64.urlsafe_b64encode(code.encode()).decode()
    url = f"https://mermaid.ink/img/{encoded}?bgColor=white&theme=default"

    for attempt in range(3):
        try:
            if attempt > 0:
                time.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s
            req = urllib.request.Request(url, headers={"User-Agent": "WorldOfProtocols-PDFGen/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                png_data = resp.read()
            if len(png_data) < 100:
                continue
            output_path.write_bytes(png_data)
            time.sleep(0.5)  # Rate limit: 0.5s between successful requests
            return True
        except (urllib.error.URLError, OSError, TimeoutError):
            continue
    return False

def render_mermaid(code: str, max_width: float = None) -> "Image | None":
    """Render a Mermaid diagram to a ReportLab Image.

    Tries local mmdc first (fast, reliable), falls back to mermaid.ink API.
    Uses a local file cache (keyed by content hash) to avoid re-rendering.
    Returns None on failure so the caller can fall back to a placeholder.
    """
    if SKIP_MERMAID:
        return None

    if max_width is None:
        max_width = PAGE_WIDTH - 2 * MARGIN - 4

    # Cache setup
    MERMAID_CACHE_DIR.mkdir(exist_ok=True)
    code_hash = hashlib.md5(code.encode()).hexdigest()
    cache_file = MERMAID_CACHE_DIR / f"{code_hash}.png"

    if not (cache_file.exists() and cache_file.stat().st_size > 100):
        # Try local rendering first (much faster and more reliable)
        if not _render_mermaid_local(code, cache_file):
            # Fall back to API
            if not _render_mermaid_api(code, cache_file):
                print(f"    WARNING: Mermaid render failed (both local and API)")
                return None

    # Create ReportLab Image from the cached PNG
    try:
        png_data = cache_file.read_bytes()
        img_buf = io.BytesIO(png_data)
        img = Image(img_buf)
        # Scale to fit page width while maintaining aspect ratio
        orig_w, orig_h = img.drawWidth, img.drawHeight
        if orig_w > max_width:
            scale = max_width / orig_w
            img.drawWidth = orig_w * scale
            img.drawHeight = orig_h * scale
        # Also cap height to avoid page overflow
        max_height = PAGE_HEIGHT - 2 * MARGIN - 1.5 * inch
        if img.drawHeight > max_height:
            scale = max_height / img.drawHeight
            img.drawWidth = img.drawWidth * scale
            img.drawHeight = img.drawHeight * scale
        return img
    except Exception as e:
        print(f"    WARNING: Mermaid image embed failed: {e}")
        return None


# Directory name -> human-readable display name
CATEGORY_NAMES = {
    "automotive": "Automotive",
    "aviation": "Aviation",
    "bus": "Bus & IC Protocols",
    "data-formats": "Data & Model Formats",
    "database": "Database Wire Protocols",
    "email": "Email",
    "encoding": "Encoding & Symbology",
    "file-sharing": "File Sharing & Transfer",
    "healthcare": "Healthcare",
    "hpc": "High-Performance Computing",
    "industrial": "Industrial & SCADA",
    "link-layer": "Data Link Layer",
    "media": "Media & Broadcast",
    "messaging": "Messaging & Pub/Sub",
    "mobile-sync": "Mobile Sync",
    "monitoring": "Network Management & Monitoring",
    "naming": "Naming, Addressing & Discovery",
    "network-layer": "Network Layer",
    "remote-access": "Remote Access",
    "robotics": "Robotics",
    "routing": "Routing",
    "security": "Security & Authentication",
    "serial": "Serial Protocols",
    "space": "Space & Satellite",
    "storage": "Storage Networking",
    "telecom": "Telecommunications",
    "transport-layer": "Transport Layer",
    "tunneling": "Tunneling & VPN",
    "voip": "VoIP & Real-Time",
    "web": "Web & API",
    "wireless": "Wireless & Radio",
}

# Category -> (R, G, B) tuples for divider page accent bars
CATEGORY_COLORS = {
    "automotive": (55, 71, 79),
    "aviation": (2, 136, 209),
    "bus": (0, 105, 92),
    "data-formats": (93, 64, 55),
    "database": (139, 105, 20),
    "email": (230, 126, 34),
    "encoding": (142, 68, 173),
    "file-sharing": (39, 174, 96),
    "healthcare": (233, 30, 99),
    "hpc": (63, 81, 181),
    "industrial": (130, 119, 23),
    "link-layer": (108, 52, 131),
    "media": (142, 68, 173),
    "messaging": (22, 160, 133),
    "mobile-sync": (96, 125, 139),
    "monitoring": (96, 125, 139),
    "naming": (39, 174, 96),
    "network-layer": (44, 62, 80),
    "remote-access": (52, 73, 94),
    "robotics": (0, 150, 136),
    "routing": (211, 84, 0),
    "security": (192, 57, 43),
    "serial": (0, 105, 92),
    "space": (26, 35, 126),
    "storage": (93, 64, 55),
    "telecom": (173, 20, 87),
    "transport-layer": (44, 110, 73),
    "tunneling": (74, 20, 140),
    "voip": (231, 76, 60),
    "web": (74, 144, 217),
    "wireless": (0, 172, 193),
}

# Brief descriptions for each category (shown on divider pages)
CATEGORY_DESCRIPTIONS = {
    "automotive": "Protocols used in vehicle networks, from in-car buses to V2X communication.",
    "aviation": "Communication and data-link protocols used in aviation and air traffic systems.",
    "bus": "Low-level bus and inter-IC communication protocols for hardware and embedded systems.",
    "data-formats": "Serialization, data modeling, and interchange format protocols.",
    "database": "Wire protocols used by databases for client-server communication.",
    "email": "Protocols for sending, receiving, and accessing electronic mail.",
    "encoding": "Character encoding, barcode symbology, and data encoding schemes.",
    "file-sharing": "Protocols for transferring and sharing files across networks.",
    "healthcare": "Communication protocols used in medical and healthcare IT systems.",
    "hpc": "Protocols optimized for high-performance and cluster computing.",
    "industrial": "Industrial control, SCADA, and building automation protocols.",
    "link-layer": "Data link layer (Layer 2) protocols for local network communication.",
    "media": "Streaming, broadcast, and media delivery protocols.",
    "messaging": "Message queuing, publish/subscribe, and event-driven protocols.",
    "mobile-sync": "Protocols for mobile device synchronization and management.",
    "monitoring": "Network management, monitoring, and observability protocols.",
    "naming": "Name resolution, addressing, and service discovery protocols.",
    "network-layer": "Network layer (Layer 3) protocols for packet routing and delivery.",
    "remote-access": "Protocols for remote login, desktop access, and terminal services.",
    "robotics": "Communication protocols used in robotics and autonomous systems.",
    "routing": "Routing protocols for path computation and network convergence.",
    "security": "Security, authentication, and cryptographic protocols.",
    "serial": "Serial communication protocols for point-to-point and multi-drop links.",
    "space": "Protocols designed for space communication and satellite networks.",
    "storage": "Storage area networking and block-level storage protocols.",
    "telecom": "Telecommunications signaling, switching, and transport protocols.",
    "transport-layer": "Transport layer (Layer 4) protocols for reliable and unreliable delivery.",
    "tunneling": "Tunneling and VPN protocols for encapsulation and secure transit.",
    "voip": "Voice over IP, real-time communication, and session control protocols.",
    "web": "Web application, API, and hypertext protocols.",
    "wireless": "Wireless LAN, PAN, and radio communication protocols.",
}


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def build_styles():
    """Create and return all ParagraphStyle objects used in the PDF."""
    ss = getSampleStyleSheet()

    styles = {
        # Cover page
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=ss["Title"],
            fontSize=36,
            leading=44,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=colors.HexColor("#1a237e"),
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=ss["Normal"],
            fontSize=16,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=8,
            textColor=colors.HexColor("#37474f"),
        ),
        "cover_detail": ParagraphStyle(
            "CoverDetail",
            parent=ss["Normal"],
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=colors.HexColor("#607d8b"),
        ),
        # TOC
        "toc_h1": ParagraphStyle(
            "TOCH1",
            parent=ss["Normal"],
            fontSize=13,
            leading=18,
            leftIndent=20,
            spaceBefore=4,
            spaceAfter=2,
            textColor=colors.HexColor("#1a237e"),
        ),
        "toc_h2": ParagraphStyle(
            "TOCH2",
            parent=ss["Normal"],
            fontSize=11,
            leading=15,
            leftIndent=40,
            spaceBefore=1,
            spaceAfter=1,
            textColor=colors.HexColor("#37474f"),
        ),
        # Category divider
        "cat_title": ParagraphStyle(
            "CatTitle",
            parent=ss["Title"],
            fontSize=28,
            leading=34,
            alignment=TA_LEFT,
            spaceAfter=14,
            textColor=colors.white,
        ),
        "cat_desc": ParagraphStyle(
            "CatDesc",
            parent=ss["Normal"],
            fontSize=13,
            leading=18,
            alignment=TA_LEFT,
            spaceAfter=6,
            textColor=colors.HexColor("#455a64"),
        ),
        # Protocol headings
        "h1": ParagraphStyle(
            "H1",
            parent=ss["Heading1"],
            fontSize=18,
            leading=24,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#1a237e"),
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=ss["Heading2"],
            fontSize=14,
            leading=19,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor("#283593"),
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=ss["Heading3"],
            fontSize=12,
            leading=16,
            spaceBefore=10,
            spaceAfter=4,
            textColor=colors.HexColor("#37474f"),
        ),
        # Body text
        "body": ParagraphStyle(
            "Body",
            parent=ss["Normal"],
            fontSize=9.5,
            leading=13,
            spaceBefore=2,
            spaceAfter=4,
        ),
        # Bullet list item
        "bullet": ParagraphStyle(
            "Bullet",
            parent=ss["Normal"],
            fontSize=9.5,
            leading=13,
            leftIndent=24,
            bulletIndent=12,
            spaceBefore=1,
            spaceAfter=1,
        ),
        # Nested bullet (indented further)
        "bullet2": ParagraphStyle(
            "Bullet2",
            parent=ss["Normal"],
            fontSize=9.5,
            leading=13,
            leftIndent=40,
            bulletIndent=28,
            spaceBefore=1,
            spaceAfter=1,
        ),
        # Code block
        "code": ParagraphStyle(
            "Code",
            parent=ss["Code"],
            fontSize=8,
            leading=10,
            fontName="Courier",
            leftIndent=12,
            rightIndent=12,
            spaceBefore=4,
            spaceAfter=4,
            backColor=colors.HexColor("#f5f5f5"),
        ),
        # Blockquote / info box
        "blockquote": ParagraphStyle(
            "Blockquote",
            parent=ss["Normal"],
            fontSize=9,
            leading=12.5,
            leftIndent=16,
            rightIndent=8,
            spaceBefore=6,
            spaceAfter=6,
            borderPadding=6,
            textColor=colors.HexColor("#37474f"),
            backColor=colors.HexColor("#e8eaf6"),
            borderColor=colors.HexColor("#3f51b5"),
            borderWidth=1.5,
            borderRadius=3,
        ),
        # Table header cell
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=ss["Normal"],
            fontSize=8.5,
            leading=11,
            alignment=TA_LEFT,
            textColor=colors.white,
        ),
        # Table body cell
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=ss["Normal"],
            fontSize=8.5,
            leading=11,
            alignment=TA_LEFT,
        ),
        # Footer
        "footer": ParagraphStyle(
            "Footer",
            parent=ss["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#9e9e9e"),
        ),
        # Mermaid placeholder
        "mermaid_placeholder": ParagraphStyle(
            "MermaidPlaceholder",
            parent=ss["Italic"],
            fontSize=9,
            leading=12,
            leftIndent=16,
            spaceBefore=4,
            spaceAfter=4,
            textColor=colors.HexColor("#9e9e9e"),
        ),
    }
    return styles


# ---------------------------------------------------------------------------
# Markdown parsing helpers
# ---------------------------------------------------------------------------

def _escape_xml(text: str) -> str:
    """Escape characters that are special in ReportLab's XML-like paragraph markup."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def _replace_unicode_fractions(text: str) -> str:
    """Replace problematic Unicode characters that ReportLab can't render."""
    # Replace common Unicode subscript/superscript characters with ASCII equivalents
    replacements = {
        "\u2080": "0", "\u2081": "1", "\u2082": "2", "\u2083": "3",
        "\u2084": "4", "\u2085": "5", "\u2086": "6", "\u2087": "7",
        "\u2088": "8", "\u2089": "9",
        "\u2070": "0", "\u00b9": "1", "\u00b2": "2", "\u00b3": "3",
        "\u2074": "4", "\u2075": "5", "\u2076": "6", "\u2077": "7",
        "\u2078": "8", "\u2079": "9",
        "\u207a": "+", "\u207b": "-", "\u207c": "=",
        "\u208a": "+", "\u208b": "-", "\u208c": "=",
        "\u2190": "<-", "\u2192": "->", "\u2194": "<->",
        "\u2264": "<=", "\u2265": ">=", "\u2260": "!=",
        "\u00d7": "x",  # multiplication sign
        "\u2013": "-",  # en dash
        "\u2014": "--", # em dash
        "\u2018": "'", "\u2019": "'",  # smart quotes
        "\u201c": '"', "\u201d": '"',
        "\u2026": "...",  # ellipsis
        "\u00a0": " ",  # non-breaking space
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


def _inline_markup(text: str) -> str:
    """Convert inline markdown (bold, italic, code, links) to ReportLab XML tags.

    Processes the text after XML-escaping so that ReportLab can render
    bold (<b>), italic (<i>), and code (<font face="Courier">) spans.
    Links are rendered as styled text (not clickable in PDF body text).
    """
    text = _replace_unicode_fractions(text)
    text = _escape_xml(text)

    # Inline code: `code` -> <font face="Courier" color="#c62828">code</font>
    text = re.sub(
        r"`([^`]+)`",
        r'<font face="Courier" color="#c62828">\1</font>',
        text,
    )
    # Bold + italic: ***text*** or ___text___
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)
    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    # Italic: *text* or _text_ (but not inside words with underscores)
    text = re.sub(r"(?<!\w)\*([^*]+?)\*(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_([^_]+?)_(?!\w)", r"<i>\1</i>", text)
    # Links: [text](url) -> text (underlined)
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r'<u>\1</u>',
        text,
    )
    return text


def _parse_table_rows(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """Parse markdown table lines into a header row and data rows.

    Skips the separator line (|---|---|).
    Returns (header_cells, [row_cells, ...]).
    """
    if not lines:
        return [], []

    def split_row(line: str) -> list[str]:
        """Split a markdown table row on | and strip whitespace."""
        # Remove leading/trailing |
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [cell.strip() for cell in line.split("|")]

    header = split_row(lines[0])
    data_rows = []
    for line in lines[1:]:
        # Skip separator lines like |---|---|
        stripped = line.strip().replace("|", "").replace("-", "").replace(":", "").strip()
        if not stripped:
            continue
        data_rows.append(split_row(line))
    return header, data_rows


# ---------------------------------------------------------------------------
# Markdown -> Flowables conversion
# ---------------------------------------------------------------------------

def md_to_flowables(md_text: str, styles: dict, protocol_name: str = "") -> list:
    """Parse a markdown string and return a list of ReportLab flowables.

    Handles: headings, blockquotes, tables, bullet lists, code blocks,
    mermaid placeholders, and body paragraphs with inline markup.
    """
    flowables = []
    lines = md_text.split("\n")
    i = 0
    n = len(lines)

    # Track whether we've seen the H1 (protocol title) -- skip it since
    # we render protocol titles separately.
    seen_h1 = False

    while i < n:
        line = lines[i]

        # --- Code block (fenced) ---
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip().lower()
            code_lines = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```

            if lang == "mermaid":
                mermaid_code = "\n".join(code_lines)
                img = render_mermaid(mermaid_code)
                if img is not None:
                    flowables.append(Spacer(1, 4))
                    flowables.append(img)
                    flowables.append(Spacer(1, 4))
                else:
                    flowables.append(
                        Paragraph("[Diagram: see online version]", styles["mermaid_placeholder"])
                    )
            else:
                # Render code block as preformatted text with light gray background
                code_text = "\n".join(code_lines)
                code_text = _replace_unicode_fractions(code_text)
                code_text = _escape_xml(code_text)
                # Wrap in a table cell for background color
                code_para = Preformatted(code_text, styles["code"])
                code_table = Table(
                    [[code_para]],
                    colWidths=[PAGE_WIDTH - 2 * MARGIN - 4],
                )
                code_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]))
                flowables.append(Spacer(1, 4))
                flowables.append(code_table)
                flowables.append(Spacer(1, 4))
            continue

        # --- H1 heading ---
        if line.startswith("# ") and not line.startswith("## "):
            if not seen_h1:
                seen_h1 = True
                # Skip the H1 -- we render protocol titles ourselves
                i += 1
                continue
            text = _inline_markup(line[2:].strip())
            flowables.append(Paragraph(text, styles["h1"]))
            i += 1
            continue

        # --- H2 heading ---
        if line.startswith("## "):
            text = _inline_markup(line[3:].strip())
            flowables.append(Paragraph(text, styles["h2"]))
            i += 1
            continue

        # --- H3 heading ---
        if line.startswith("### "):
            text = _inline_markup(line[4:].strip())
            flowables.append(Paragraph(text, styles["h3"]))
            i += 1
            continue

        # --- H4+ heading (render as bold body) ---
        m = re.match(r"^(#{4,})\s+(.*)", line)
        if m:
            text = _inline_markup(m.group(2).strip())
            flowables.append(Paragraph(f"<b>{text}</b>", styles["body"]))
            i += 1
            continue

        # --- Blockquote ---
        if line.strip().startswith("> "):
            bq_lines = []
            while i < n and lines[i].strip().startswith("> "):
                bq_lines.append(lines[i].strip()[2:])
                i += 1
            bq_text = " ".join(bq_lines)
            bq_text = _inline_markup(bq_text)
            # Wrap in a table for the colored left border + background
            bq_para = Paragraph(bq_text, styles["blockquote"])
            bq_table = Table(
                [[bq_para]],
                colWidths=[PAGE_WIDTH - 2 * MARGIN - 4],
            )
            bq_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e8eaf6")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c5cae9")),
                ("LINEBEFOREDECOR", (0, 0), (0, -1), 3, colors.HexColor("#3f51b5")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            flowables.append(Spacer(1, 4))
            flowables.append(bq_table)
            flowables.append(Spacer(1, 6))
            continue

        # --- Table ---
        if line.strip().startswith("|") and "|" in line.strip()[1:]:
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            header, rows = _parse_table_rows(table_lines)
            if not header:
                continue

            # Build ReportLab Table
            num_cols = len(header)
            avail_width = PAGE_WIDTH - 2 * MARGIN - 8
            col_width = avail_width / num_cols

            # Header row
            header_cells = [
                Paragraph(_inline_markup(h), styles["table_header"]) for h in header
            ]
            table_data = [header_cells]

            # Data rows -- ensure each row has the right number of columns
            for row in rows:
                # Pad or trim to match header length
                while len(row) < num_cols:
                    row.append("")
                row = row[:num_cols]
                table_data.append([
                    Paragraph(_inline_markup(cell), styles["table_cell"]) for cell in row
                ])

            t = Table(table_data, colWidths=[col_width] * num_cols)
            style_cmds = [
                # Header row: dark background, white text
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                # Grid lines
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdbdbd")),
                # Padding
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                # Vertical alignment
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
            # Alternating row colors for data rows
            for row_idx in range(1, len(table_data)):
                if row_idx % 2 == 0:
                    style_cmds.append(
                        ("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#fafafa"))
                    )
                else:
                    style_cmds.append(
                        ("BACKGROUND", (0, row_idx), (-1, row_idx), colors.white)
                    )
            t.setStyle(TableStyle(style_cmds))
            flowables.append(Spacer(1, 4))
            flowables.append(t)
            flowables.append(Spacer(1, 6))
            continue

        # --- Bullet list item ---
        if re.match(r"^\s*[-*]\s+", line):
            # Determine indent level
            leading_spaces = len(line) - len(line.lstrip())
            bullet_match = re.match(r"^\s*[-*]\s+(.*)", line)
            if bullet_match:
                text = _inline_markup(bullet_match.group(1).strip())
                style_key = "bullet2" if leading_spaces >= 4 else "bullet"
                bullet_char = "\u2022"
                flowables.append(
                    Paragraph(
                        f"{bullet_char}  {text}",
                        styles[style_key],
                    )
                )
            i += 1
            continue

        # --- Numbered list item ---
        m = re.match(r"^\s*(\d+)\.\s+(.*)", line)
        if m:
            num = m.group(1)
            text = _inline_markup(m.group(2).strip())
            flowables.append(
                Paragraph(f"{num}.  {text}", styles["bullet"])
            )
            i += 1
            continue

        # --- Horizontal rule ---
        if re.match(r"^-{3,}$|^\*{3,}$|^_{3,}$", line.strip()):
            flowables.append(Spacer(1, 8))
            # Draw a thin line via a narrow table
            hr = Table([[""]], colWidths=[PAGE_WIDTH - 2 * MARGIN - 4], rowHeights=[1])
            hr.setStyle(TableStyle([
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor("#bdbdbd")),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            flowables.append(hr)
            flowables.append(Spacer(1, 8))
            i += 1
            continue

        # --- Empty line (paragraph break) ---
        if not line.strip():
            flowables.append(Spacer(1, 4))
            i += 1
            continue

        # --- Regular paragraph ---
        # Accumulate consecutive non-empty, non-special lines
        para_lines = []
        while i < n:
            l = lines[i]
            # Stop if we hit a special line
            if (
                not l.strip()
                or l.strip().startswith("#")
                or l.strip().startswith(">")
                or l.strip().startswith("|")
                or l.strip().startswith("```")
                or re.match(r"^\s*[-*]\s+", l)
                or re.match(r"^\s*\d+\.\s+", l)
                or re.match(r"^-{3,}$|^\*{3,}$|^_{3,}$", l.strip())
            ):
                break
            para_lines.append(l.strip())
            i += 1
        if para_lines:
            text = " ".join(para_lines)
            text = _inline_markup(text)
            try:
                flowables.append(Paragraph(text, styles["body"]))
            except Exception:
                # If markup parsing fails, fall back to escaped text
                safe = _escape_xml(" ".join(para_lines))
                safe = _replace_unicode_fractions(safe)
                flowables.append(Paragraph(safe, styles["body"]))
            continue

        # Fallback: advance
        i += 1

    return flowables


# ---------------------------------------------------------------------------
# Protocol name extraction
# ---------------------------------------------------------------------------

def _protocol_display_name(md_text: str, filename: str) -> str:
    """Extract a human-readable protocol name from the markdown H1 heading.

    Falls back to formatting the filename if no H1 is found.
    Example H1: '# HTTP (Hypertext Transfer Protocol)'
    Returns: 'HTTP -- Hypertext Transfer Protocol'
    """
    for line in md_text.split("\n")[:5]:
        if line.startswith("# ") and not line.startswith("## "):
            raw = line[2:].strip()
            # Try to parse "ABBREV (Full Name)" pattern
            m = re.match(r"^([^(]+)\(([^)]+)\)\s*$", raw)
            if m:
                abbrev = m.group(1).strip()
                full = m.group(2).strip()
                return f"{abbrev} -- {full}"
            return raw

    # Fallback: use filename
    name = filename.replace(".md", "").replace("-", " ").replace("_", " ")
    return name.upper()


# ---------------------------------------------------------------------------
# Document template with headers and footers
# ---------------------------------------------------------------------------

class ProtocolDocTemplate(BaseDocTemplate):
    """Custom document template that draws page headers and footers."""

    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.current_category = ""
        self.page_count_offset = 0  # For the cover/TOC pages

    def afterFlowable(self, flowable):
        """Hook called after each flowable is placed -- used for TOC entries."""
        # Detect TOC-triggering paragraphs by checking for special attributes
        if hasattr(flowable, "_toc_level"):
            level = flowable._toc_level
            text = flowable.getPlainText()
            key = flowable._toc_key
            self.notify("TOCEntry", (level, text, self.page, key))


def _header_footer_normal(canvas, doc):
    """Draw header (category name) and footer (page number) on normal pages."""
    canvas.saveState()

    # Footer: page number centered
    page_num = canvas.getPageNumber()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#9e9e9e"))
    canvas.drawCentredString(PAGE_WIDTH / 2, 0.45 * inch, str(page_num))

    # Header: category name right-aligned
    if doc.current_category:
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.setFillColor(colors.HexColor("#9e9e9e"))
        canvas.drawRightString(
            PAGE_WIDTH - MARGIN,
            PAGE_HEIGHT - 0.5 * inch,
            doc.current_category,
        )
        # Thin line below header
        canvas.setStrokeColor(colors.HexColor("#e0e0e0"))
        canvas.setLineWidth(0.5)
        canvas.line(
            MARGIN, PAGE_HEIGHT - 0.55 * inch,
            PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 0.55 * inch,
        )

    canvas.restoreState()


def _header_footer_cover(canvas, doc):
    """No header/footer on cover or divider pages."""
    pass


# ---------------------------------------------------------------------------
# Build functions
# ---------------------------------------------------------------------------

def build_cover_page(styles: dict) -> list:
    """Return flowables for the cover page."""
    flowables = []
    flowables.append(Spacer(1, 2.0 * inch))
    flowables.append(Paragraph("World of Protocols", styles["cover_title"]))
    flowables.append(Spacer(1, 0.3 * inch))
    flowables.append(
        Paragraph(
            "A comprehensive quick-reference for 274 protocols",
            styles["cover_subtitle"],
        )
    )
    flowables.append(Spacer(1, 0.15 * inch))
    flowables.append(
        Paragraph(
            "From physical layer to application layer",
            styles["cover_detail"],
        )
    )
    flowables.append(Spacer(1, 0.6 * inch))
    flowables.append(
        Paragraph(
            f"Generated on {date.today().strftime('%B %d, %Y')}",
            styles["cover_detail"],
        )
    )
    flowables.append(Spacer(1, 0.15 * inch))
    flowables.append(
        Paragraph(
            f'<link href="{GITHUB_URL}">{GITHUB_URL}</link>',
            styles["cover_detail"],
        )
    )
    flowables.append(PageBreak())
    return flowables


def build_toc() -> TableOfContents:
    """Return a configured TableOfContents object."""
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOCLevel0",
            fontSize=13,
            leading=20,
            leftIndent=20,
            spaceBefore=6,
            spaceAfter=2,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1a237e"),
        ),
        ParagraphStyle(
            "TOCLevel1",
            fontSize=10,
            leading=14,
            leftIndent=44,
            spaceBefore=1,
            spaceAfter=1,
            fontName="Helvetica",
            textColor=colors.HexColor("#455a64"),
        ),
    ]
    return toc


def build_category_divider(
    cat_key: str, styles: dict, protocol_count: int
) -> list:
    """Return flowables for a category divider page."""
    display_name = CATEGORY_NAMES.get(cat_key, cat_key.title())
    r, g, b = CATEGORY_COLORS.get(cat_key, (55, 71, 79))
    color = colors.Color(r / 255, g / 255, b / 255)
    description = CATEGORY_DESCRIPTIONS.get(cat_key, "")

    flowables = []
    flowables.append(Spacer(1, 1.5 * inch))

    # Colored bar with category name
    # Use a Table with colored background to create the bar effect
    title_para = Paragraph(display_name, styles["cat_title"])
    bar_table = Table(
        [[title_para]],
        colWidths=[PAGE_WIDTH - 2 * MARGIN],
        rowHeights=[60],
    )
    bar_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    flowables.append(bar_table)
    flowables.append(Spacer(1, 0.3 * inch))

    if description:
        flowables.append(Paragraph(description, styles["cat_desc"]))
        flowables.append(Spacer(1, 0.15 * inch))

    flowables.append(
        Paragraph(
            f"<i>{protocol_count} protocol{'s' if protocol_count != 1 else ''} in this section</i>",
            styles["cat_desc"],
        )
    )

    flowables.append(PageBreak())
    return flowables


def build_protocol_section(
    md_text: str, filename: str, styles: dict, cat_key: str
) -> list:
    """Return flowables for a single protocol's content."""
    display_name = _protocol_display_name(md_text, filename)
    r, g, b = CATEGORY_COLORS.get(cat_key, (55, 71, 79))
    accent = colors.Color(r / 255, g / 255, b / 255)

    flowables = []

    # Protocol title heading -- with a bookmark key for the TOC
    key = f"proto_{cat_key}_{filename}"
    title_text = _escape_xml(display_name)
    title_text = _replace_unicode_fractions(title_text)
    title_para = Paragraph(
        f'<a name="{key}"/>{title_text}',
        styles["h1"],
    )
    # Attach TOC metadata so afterFlowable can pick it up
    title_para._toc_level = 1
    title_para._toc_key = key
    flowables.append(title_para)

    # Thin accent line under the protocol title
    hr = Table([[""]], colWidths=[PAGE_WIDTH - 2 * MARGIN - 4], rowHeights=[2])
    hr.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 2, accent),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    flowables.append(hr)
    flowables.append(Spacer(1, 6))

    # Parse the rest of the markdown body
    body = md_to_flowables(md_text, styles, protocol_name=display_name)
    flowables.extend(body)

    # Add some space before next protocol
    flowables.append(Spacer(1, 16))

    return flowables


# ---------------------------------------------------------------------------
# Scanning and collecting protocol files
# ---------------------------------------------------------------------------

def scan_protocols(protocols_dir: Path) -> dict[str, list[Path]]:
    """Scan the protocols directory and return {category_key: [md_paths]} sorted."""
    categories = {}

    for subdir in sorted(protocols_dir.iterdir()):
        if not subdir.is_dir():
            continue
        cat_key = subdir.name
        if cat_key.startswith("_"):
            continue  # Skip _template etc.
        md_files = sorted(subdir.glob("*.md"))
        if md_files:
            categories[cat_key] = md_files

    return categories


# ---------------------------------------------------------------------------
# Main PDF generation
# ---------------------------------------------------------------------------

def generate_pdf(protocols_dir: Path, output_path: Path):
    """Generate the complete PDF from protocol markdown files."""
    styles = build_styles()

    print(f"Scanning protocols in: {protocols_dir}")
    categories = scan_protocols(protocols_dir)
    total_protocols = sum(len(files) for files in categories.values())
    print(f"Found {total_protocols} protocols in {len(categories)} categories")

    # --- Set up document ---
    doc = ProtocolDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="World of Protocols",
        author="World of Protocols",
        subject="Comprehensive Protocol Reference",
    )

    # Two page templates: one for cover/divider (no header/footer),
    # one for normal content pages (with header/footer)
    frame = Frame(
        MARGIN, MARGIN,
        PAGE_WIDTH - 2 * MARGIN,
        PAGE_HEIGHT - 2 * MARGIN,
        id="normal",
    )
    cover_template = PageTemplate(
        id="cover",
        frames=[frame],
        onPage=_header_footer_cover,
    )
    normal_template = PageTemplate(
        id="normal",
        frames=[frame],
        onPage=_header_footer_normal,
    )
    doc.addPageTemplates([cover_template, normal_template])

    # --- Build story ---
    story = []

    # Cover page (uses cover template -- no header/footer)
    story.extend(build_cover_page(styles))

    # Switch to normal template for TOC
    story.append(NextPageTemplate("normal"))

    # Table of Contents page
    toc_title = Paragraph("Table of Contents", styles["h1"])
    story.append(toc_title)
    story.append(Spacer(1, 0.2 * inch))
    toc = build_toc()
    story.append(toc)
    story.append(PageBreak())

    # --- Categories and protocols ---
    processed = 0
    for cat_key, md_files in categories.items():
        display_name = CATEGORY_NAMES.get(cat_key, cat_key.title())

        # Category divider page (uses cover template -- no header/footer)
        story.append(NextPageTemplate("cover"))
        story.append(PageBreak())

        # Create a TOC-triggering paragraph for the category
        cat_key_id = f"cat_{cat_key}"
        cat_toc_text = _escape_xml(display_name)
        cat_toc_para = Paragraph(
            f'<a name="{cat_key_id}"/><b>{cat_toc_text}</b>',
            ParagraphStyle("CatTOC", fontSize=1, leading=1, textColor=colors.white),
        )
        cat_toc_para._toc_level = 0
        cat_toc_para._toc_key = cat_key_id
        story.append(cat_toc_para)

        story.extend(build_category_divider(cat_key, styles, len(md_files)))

        # Switch back to normal template for protocol content
        story.append(NextPageTemplate("normal"))

        # Set the current category for the header
        doc.current_category = display_name

        for md_path in md_files:
            md_text = md_path.read_text(encoding="utf-8")
            try:
                protocol_flowables = build_protocol_section(
                    md_text, md_path.name, styles, cat_key
                )
                story.extend(protocol_flowables)
            except Exception as e:
                # If a protocol fails to parse, add an error note and continue
                print(f"  WARNING: Error processing {md_path.name}: {e}")
                story.append(
                    Paragraph(
                        f"<i>[Error processing {_escape_xml(md_path.name)}: {_escape_xml(str(e))}]</i>",
                        styles["body"],
                    )
                )
                story.append(Spacer(1, 12))

            processed += 1
            if processed % 25 == 0:
                print(f"  Processed {processed}/{total_protocols} protocols...")

    # --- Build PDF ---
    print(f"Building PDF ({total_protocols} protocols)...")

    # Multi-pass build for TOC page numbers
    doc.multiBuild(story)

    print(f"PDF generated: {output_path}")
    print(f"  Total protocols: {total_protocols}")
    print(f"  Categories: {len(categories)}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a PDF from World of Protocols markdown files."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output PDF path (default: maps/world-of-protocols.pdf)",
    )
    parser.add_argument(
        "--no-diagrams",
        action="store_true",
        help="Skip Mermaid diagram rendering (faster, uses placeholders)",
    )
    args = parser.parse_args()

    global SKIP_MERMAID
    if args.no_diagrams:
        SKIP_MERMAID = True

    # Resolve paths relative to the project root (parent of scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    protocols_dir = project_root / "protocols"
    if not protocols_dir.is_dir():
        print(f"ERROR: Protocols directory not found: {protocols_dir}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = Path(args.output).resolve()
    else:
        output_path = project_root / "maps" / "world-of-protocols.pdf"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generate_pdf(protocols_dir, output_path)


if __name__ == "__main__":
    main()
