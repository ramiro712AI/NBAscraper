"""
Deterministic player color assignment.

Each player receives a unique light-pastel hex color derived from their
player_id.  The mapping is stable across runs: same player → same color.
Colors are chosen for readability against dark header text.

Column-category colors (for headers only):
  HITS  → HITS_HEADER_COLOR
  RUNS  → RUNS_HEADER_COLOR
  RBI   → RBI_HEADER_COLOR
"""
from __future__ import annotations

import hashlib

# ── Column-category header colors ────────────────────────────────────────────
HITS_HEADER_COLOR = "FFD966"    # Warm gold
RUNS_HEADER_COLOR = "92D050"    # Lime green
RBI_HEADER_COLOR  = "FF7070"    # Salmon red

# Neutral section header color
INFO_HEADER_COLOR = "4472C4"    # Corporate blue
GAME_HEADER_COLOR = "44546A"    # Steel blue-gray
AGG_HEADER_COLOR  = "7030A0"    # Deep purple (aggregates section)

# Header font color (always white for readability on dark backgrounds)
HEADER_FONT_COLOR = "FFFFFF"

# ── Player identity palette ───────────────────────────────────────────────────
# 30 distinct light pastels — enough for a full MLB game slate.
# Extended with 10 additional muted tones to handle large rosters.
_PALETTE: list[str] = [
    "FFF2CC",  # Light gold
    "E2EFDA",  # Light sage
    "DDEEFF",  # Light sky blue
    "FDE9D9",  # Light peach
    "EAD1DC",  # Light rose
    "D9EAD3",  # Light mint
    "CFE2F3",  # Soft cornflower
    "F4CCCC",  # Soft red
    "D9D2E9",  # Soft lavender
    "FCE5CD",  # Soft apricot
    "D0E0E3",  # Pale teal
    "EAD1DC",  # Dusty mauve
    "FFF9C4",  # Pale lemon
    "C9DAF8",  # Periwinkle
    "D9EAD3",  # Pale green
    "F9CB9C",  # Light tangerine
    "B6D7A8",  # Soft fern
    "A4C2F4",  # Light blue
    "EA9999",  # Soft coral
    "B4A7D6",  # Muted violet
    "F6B26B",  # Muted orange (slightly darker for contrast)
    "93C47D",  # Medium sage
    "76A5AF",  # Steel teal
    "E06666",  # Medium coral (use sparingly)
    "6FA8DC",  # Medium sky blue
    "FFE599",  # Canary
    "A9D18E",  # Fern
    "9FC5E8",  # Powder blue
    "F4CCCC",  # Blush
    "C27BA0",  # Dusty rose (darker — only for overflow)
    # Overflow — cycles back through lighter variants
    "FFFDE7",
    "E8F5E9",
    "E3F2FD",
    "FBE9E7",
    "F3E5F5",
    "E0F7FA",
    "FFF8E1",
    "F1F8E9",
    "E8EAF6",
    "FFF3E0",
]


def get_player_color(player_id: int) -> str:
    """
    Return a stable hex color string (without #) for a given player_id.

    The same player_id always maps to the same color regardless of
    execution order or date.
    """
    digest = hashlib.md5(str(player_id).encode()).hexdigest()
    index = int(digest[:8], 16) % len(_PALETTE)
    return _PALETTE[index]


def get_player_color_map(player_ids: list[int]) -> dict[int, str]:
    """Build a color map for a list of player IDs."""
    return {pid: get_player_color(pid) for pid in player_ids}
