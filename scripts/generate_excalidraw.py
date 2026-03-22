#!/usr/bin/env python3
"""
Generate an Excalidraw protocol map with clickable links to GitHub.

Auto-discovers all .md files under protocols/ and organizes them into
OSI-like layer bands with color-coded category sub-groups.

Usage:
    python generate_excalidraw.py                         # default output
    python generate_excalidraw.py -o /tmp/map.excalidraw  # custom output
"""

import argparse
import json
import math
import random
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_BASE = "https://github.com/yepher/world_of_protocols/blob/main/protocols"

LAYER_MAP = {
    # Application layer (top)
    "web": "Application",
    "email": "Application",
    "naming": "Application",
    "voip": "Application",
    "media": "Application",
    "messaging": "Application",
    "database": "Application",
    "file-sharing": "Application",
    "monitoring": "Application",
    "healthcare": "Application",
    "mobile-sync": "Application",
    "remote-access": "Application",
    # Specialized
    "industrial": "Specialized",
    "automotive": "Specialized",
    "aviation": "Specialized",
    "space": "Specialized",
    "robotics": "Specialized",
    "hpc": "Specialized",
    "storage": "Specialized",
    # Security
    "security": "Security",
    # Transport
    "transport-layer": "Transport",
    # Network / Routing
    "network-layer": "Network",
    "routing": "Network",
    "tunneling": "Network",
    # Data Link
    "link-layer": "Data Link",
    # Wireless
    "wireless": "Wireless",
    # Telecom
    "telecom": "Telecom",
    # Physical / Bus / Serial
    "bus": "Physical",
    "serial": "Physical",
    # Data formats / Encoding
    "data-formats": "Data Formats",
    "encoding": "Data Formats",
}

# Order layers top-to-bottom (roughly OSI order)
LAYER_ORDER = [
    "Application",
    "Specialized",
    "Security",
    "Transport",
    "Network",
    "Data Link",
    "Wireless",
    "Telecom",
    "Physical",
    "Data Formats",
]

LAYER_COLORS = {
    "Application": ("#dbe4ff", "#4a9eed"),       # light blue
    "Security": ("#e5dbff", "#8b5cf6"),           # light purple
    "Transport": ("#d3f9d8", "#22c55e"),          # light green
    "Network": ("#fff3bf", "#f59e0b"),            # light yellow/amber
    "Data Link": ("#ffd8a8", "#c2410c"),          # light orange
    "Wireless": ("#a5d8ff", "#0ea5e9"),           # cyan
    "Telecom": ("#fce7f3", "#ec4899"),            # pink
    "Physical": ("#ffc9c9", "#ef4444"),           # light red
    "Specialized": ("#e5dbff", "#6d28d9"),        # purple
    "Data Formats": ("#f3f4f6", "#6b7280"),       # gray
}

# Per-category tint overrides within a layer so sub-groups are visually distinct.
# Each entry maps category -> (bg, stroke).  Categories not listed here fall back
# to a procedurally shifted tint of the parent layer colour.
_CATEGORY_TINTS: dict[str, tuple[str, str]] = {
    "web":            ("#a5d8ff", "#4a9eed"),
    "email":          ("#c3fae8", "#06b6d4"),
    "naming":         ("#bac8ff", "#3b82f6"),
    "voip":           ("#d0bfff", "#8b5cf6"),
    "media":          ("#c5f6fa", "#0891b2"),
    "messaging":      ("#b2f2bb", "#22c55e"),
    "database":       ("#99e9f2", "#0e7490"),
    "file-sharing":   ("#c3fae8", "#10b981"),
    "monitoring":     ("#a5d8ff", "#2563eb"),
    "healthcare":     ("#d3f9d8", "#059669"),
    "mobile-sync":    ("#eebefa", "#a855f7"),
    "remote-access":  ("#c3fae8", "#06b6d4"),
    "industrial":     ("#e5dbff", "#7c3aed"),
    "automotive":     ("#ddd6fe", "#6d28d9"),
    "aviation":       ("#c4b5fd", "#5b21b6"),
    "space":          ("#ede9fe", "#8b5cf6"),
    "robotics":       ("#f5d0fe", "#a21caf"),
    "hpc":            ("#d8b4fe", "#7e22ce"),
    "storage":        ("#e0e7ff", "#4f46e5"),
    "security":       ("#d0bfff", "#8b5cf6"),
    "transport-layer": ("#b2f2bb", "#15803d"),
    "network-layer":  ("#fff3bf", "#b45309"),
    "routing":        ("#fef9c3", "#ca8a04"),
    "tunneling":      ("#fde68a", "#d97706"),
    "link-layer":     ("#ffd8a8", "#c2410c"),
    "wireless":       ("#a5d8ff", "#0ea5e9"),
    "telecom":        ("#fce7f3", "#ec4899"),
    "bus":            ("#ffc9c9", "#dc2626"),
    "serial":         ("#fecaca", "#b91c1c"),
    "data-formats":   ("#e5e7eb", "#6b7280"),
    "encoding":       ("#d1d5db", "#4b5563"),
}

# Layout tunables
BOX_H = 32
BOX_GAP_X = 8
BOX_GAP_Y = 6
MAX_COLS = 18          # max boxes per row inside a category group
CATEGORY_GAP = 20      # horizontal gap between category groups within a band
BAND_PAD_TOP = 30      # vertical padding inside band (above first row, below label)
BAND_PAD_BOTTOM = 12
BAND_PAD_LEFT = 160    # leave room for layer label on the left
BAND_PAD_RIGHT = 30
FONT_PROTO = 14
FONT_LAYER_LABEL = 18
FONT_CAT_LABEL = 12

# ---------------------------------------------------------------------------
# Protocol discovery
# ---------------------------------------------------------------------------

def discover_protocols(protocols_dir: Path) -> dict[str, dict[str, list[dict]]]:
    """
    Walk *protocols_dir* and return a nested mapping:

        { layer_name: { category: [ {name, filename, category, layer, path}, ... ] } }

    Protocols are sorted by name within each category.
    """
    layers: dict[str, dict[str, list[dict]]] = {}

    for md_path in sorted(protocols_dir.rglob("*.md")):
        if md_path.name == "_template.md":
            continue

        category = md_path.parent.name
        layer = LAYER_MAP.get(category)
        if layer is None:
            # Unmapped category -- put into Specialized as a fallback
            layer = "Specialized"

        # Extract protocol display name from the first H1 heading
        name = _extract_h1(md_path) or md_path.stem.upper()

        rel = md_path.relative_to(protocols_dir)  # e.g. web/http.md
        entry = {
            "name": name,
            "filename": md_path.name,
            "category": category,
            "layer": layer,
            "rel_path": str(rel),
        }

        layers.setdefault(layer, {}).setdefault(category, []).append(entry)

    # Sort protocols inside each category by name
    for layer_cats in layers.values():
        for cat_list in layer_cats.values():
            cat_list.sort(key=lambda p: p["name"].lower())

    return layers


def _extract_h1(path: Path) -> str | None:
    """Return the text of the first ``# ...`` line, or None."""
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"^#\s+(.+)$", line.strip())
                if m:
                    return m.group(1).strip()
    except OSError:
        pass
    return None


# ---------------------------------------------------------------------------
# Excalidraw element helpers
# ---------------------------------------------------------------------------

_id_counter = 0


def _next_id(prefix: str = "el") -> str:
    global _id_counter
    _id_counter += 1
    return f"{prefix}_{_id_counter}"


def _seed() -> int:
    return random.randint(1, 999_999)


def make_rect(
    x: float, y: float, w: float, h: float,
    bg: str, stroke: str, label: str,
    font: int = FONT_PROTO, link: str | None = None, opacity: int = 100,
) -> list[dict]:
    """Return [rectangle, bound-text] elements."""
    rid = _next_id("rect")
    tid = _next_id("text")
    rect = {
        "type": "rectangle",
        "id": rid,
        "x": x, "y": y,
        "width": w, "height": h,
        "backgroundColor": bg,
        "fillStyle": "solid",
        "strokeColor": stroke,
        "strokeWidth": 1,
        "roundness": {"type": 3},
        "opacity": opacity,
        "angle": 0,
        "roughness": 1,
        "seed": _seed(),
        "boundElements": [{"type": "text", "id": tid}],
    }
    if link:
        rect["link"] = link
    text = {
        "type": "text",
        "id": tid,
        "x": x + 4, "y": y + 4,
        "width": w - 8, "height": h - 8,
        "text": label,
        "fontSize": font,
        "fontFamily": 1,
        "textAlign": "center",
        "verticalAlign": "middle",
        "strokeColor": "#1e1e1e",
        "containerId": rid,
        "angle": 0,
        "roughness": 1,
        "seed": _seed(),
    }
    return [rect, text]


def make_text(
    x: float, y: float, text: str,
    font: int = 18, color: str = "#1e1e1e",
) -> dict:
    return {
        "type": "text",
        "id": _next_id("txt"),
        "x": x, "y": y,
        "width": len(text) * font * 0.6,
        "height": font + 4,
        "text": text,
        "fontSize": font,
        "fontFamily": 1,
        "textAlign": "left",
        "verticalAlign": "top",
        "strokeColor": color,
        "angle": 0,
        "roughness": 1,
        "seed": _seed(),
    }


def make_band(
    x: float, y: float, w: float, h: float,
    bg: str, stroke: str, opacity: int = 40,
) -> dict:
    return {
        "type": "rectangle",
        "id": _next_id("band"),
        "x": x, "y": y,
        "width": w, "height": h,
        "backgroundColor": bg,
        "fillStyle": "solid",
        "strokeColor": stroke,
        "strokeWidth": 1,
        "opacity": opacity,
        "angle": 0,
        "roughness": 1,
        "seed": _seed(),
    }


# ---------------------------------------------------------------------------
# Layout engine
# ---------------------------------------------------------------------------

def _box_width(name: str) -> float:
    """Compute box width from the protocol display name."""
    return max(len(name) * 8, 80)


def _category_display(category: str) -> str:
    """Pretty-print a category directory name."""
    return category.replace("-", " ").title()


def _category_colors(category: str) -> tuple[str, str]:
    """Return (bg, stroke) for a protocol box in *category*."""
    if category in _CATEGORY_TINTS:
        return _CATEGORY_TINTS[category]
    layer = LAYER_MAP.get(category, "Specialized")
    return LAYER_COLORS.get(layer, ("#f3f4f6", "#6b7280"))


def layout_band(
    categories: dict[str, list[dict]],
    start_x: float,
    start_y: float,
) -> tuple[list[dict], float]:
    """
    Lay out all protocol boxes for one layer band.

    Returns (elements, band_content_height).
    """
    elements: list[dict] = []
    cx = start_x  # current x cursor
    cy = start_y  # current y cursor (top of first row in this band)
    band_max_y = cy  # track the lowest point

    # Sort categories alphabetically for stable output
    sorted_cats = sorted(categories.keys())

    for cat in sorted_cats:
        protos = categories[cat]
        bg, stroke = _category_colors(cat)
        cat_label = _category_display(cat)

        # Category label
        elements.append(make_text(cx, cy - 16, cat_label, FONT_CAT_LABEL, stroke))

        # Lay out protocol boxes in rows within this category group
        col = 0
        row_x = cx
        row_y = cy
        row_max_x = cx

        for proto in protos:
            bw = _box_width(proto["name"])
            link = f"{GITHUB_BASE}/{proto['rel_path']}"

            if col >= MAX_COLS:
                # Wrap to next row
                col = 0
                row_x = cx
                row_y += BOX_H + BOX_GAP_Y

            elements.extend(make_rect(row_x, row_y, bw, BOX_H, bg, stroke, proto["name"], FONT_PROTO, link))

            row_x += bw + BOX_GAP_X
            row_max_x = max(row_max_x, row_x)
            col += 1

        # Advance for next category group
        bottom = row_y + BOX_H
        band_max_y = max(band_max_y, bottom)

        # Move cx right past this category group; reset to start_x if
        # the next group wouldn't fit (we'll just wrap to the next line).
        cx = row_max_x + CATEGORY_GAP

        # If the accumulated x is very wide, wrap to start a new row group
        # within the same band.  We'll use a generous width threshold.
        if cx > start_x + 3600:
            cx = start_x
            cy = band_max_y + BOX_GAP_Y + 18  # space for next cat label
            band_max_y = cy

    content_height = band_max_y - start_y + BAND_PAD_BOTTOM
    return elements, content_height


# ---------------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------------

def generate(protocols_dir: Path, output_path: Path) -> None:
    layers = discover_protocols(protocols_dir)

    total_protocols = sum(
        len(p) for cats in layers.values() for p in cats.values()
    )

    elements: list[dict] = []

    # --- Title ---
    elements.append(make_text(600, -55, "The World of Protocols", 36, "#1e1e1e"))
    elements.append(
        make_text(
            520, -8,
            f"{total_protocols} protocols  |  github.com/yepher/world_of_protocols",
            16, "#757575",
        )
    )

    # --- Build each layer band ---
    y_cursor = 50.0  # starting Y for the first band
    BAND_GAP = 14     # vertical gap between bands

    for layer_name in LAYER_ORDER:
        if layer_name not in layers:
            continue

        categories = layers[layer_name]
        layer_bg, layer_stroke = LAYER_COLORS[layer_name]

        # Pre-compute the content so we know the height
        content_y = y_cursor + BAND_PAD_TOP
        content_elements, content_h = layout_band(categories, BAND_PAD_LEFT, content_y)

        band_h = BAND_PAD_TOP + content_h
        if band_h < 60:
            band_h = 60

        # Compute band width: find the rightmost element
        max_right = 0.0
        for el in content_elements:
            r = el.get("x", 0) + el.get("width", 0)
            if r > max_right:
                max_right = r
        band_w = max(max_right + BAND_PAD_RIGHT, 800)

        # Band background rectangle
        elements.append(make_band(0, y_cursor, band_w, band_h, layer_bg, layer_stroke, 40))

        # Layer label (left side, vertically near top of band)
        elements.append(
            make_text(
                8, y_cursor + 6,
                layer_name.upper(),
                FONT_LAYER_LABEL,
                layer_stroke,
            )
        )

        # Protocol boxes & category labels
        elements.extend(content_elements)

        y_cursor += band_h + BAND_GAP

    # --- Footer ---
    elements.append(
        make_text(
            600, y_cursor + 10,
            f"github.com/yepher/world_of_protocols  |  {total_protocols} protocols",
            18, "#757575",
        )
    )

    # --- Assemble Excalidraw document ---
    excalidraw = {
        "type": "excalidraw",
        "version": 2,
        "source": "world-of-protocols",
        "elements": elements,
        "appState": {
            "viewBackgroundColor": "#ffffff",
            "gridSize": None,
        },
        "files": {},
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(excalidraw, fh, indent=2)

    link_count = sum(1 for e in elements if e.get("link"))
    print(f"Generated {output_path}")
    print(f"  Total elements : {len(elements)}")
    print(f"  Protocol boxes : {link_count}")
    print(f"  Protocols found: {total_protocols}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an Excalidraw protocol map from protocols/ markdown files.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output .excalidraw file path (default: ../maps/protocol-map.excalidraw relative to this script)",
    )
    parser.add_argument(
        "-p", "--protocols-dir",
        type=Path,
        default=None,
        help="Root protocols/ directory (default: auto-detect relative to this script)",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    protocols_dir = args.protocols_dir or (script_dir.parent / "protocols")
    output_path = args.output or (script_dir.parent / "maps" / "protocol-map.excalidraw")

    if not protocols_dir.is_dir():
        parser.error(f"Protocols directory not found: {protocols_dir}")

    generate(protocols_dir, output_path)


if __name__ == "__main__":
    main()
