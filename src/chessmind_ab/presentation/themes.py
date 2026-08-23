"""UI / board theme definitions (shared by Qt GUI)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoardTheme:
    name: str
    light: str
    dark: str
    select: str
    last: str
    check: str
    canvas_bg: str
    coord: str
    frame: str
    frame_border: str
    hover: str
    hint: str
    hint_capture: str


@dataclass(frozen=True, slots=True)
class UiTheme:
    name: str
    app_bg: str
    panel_bg: str
    card_bg: str
    card_border: str
    text: str
    muted: str
    accent: str
    accent_soft: str
    row_alt: str
    list_bg: str
    input_bg: str
    input_border: str
    button_bg: str
    button_hover: str


# Board canvas colors are aligned with the matching UI app background family.
BOARD_THEMES = {
    "green": BoardTheme(
        name="green",
        light="#e8edc5",
        dark="#5f8f4a",
        select="#f4e04d",
        last="#b8c85a",
        check="#e05260",
        canvas_bg="#12151c",
        coord="#c5cddc",
        frame="#1b2030",
        frame_border="#6b778f",
        hover="#ffffff",
        hint="#1a2e22",
        hint_capture="#101820",
    ),
    "wood": BoardTheme(
        name="wood",
        light="#f3dfc1",
        dark="#a06b45",
        select="#f0d264",
        last="#d4b06a",
        check="#d64545",
        canvas_bg="#1a1511",
        coord="#e8dcc8",
        frame="#2a211a",
        frame_border="#9a7b5a",
        hover="#ffffff",
        hint="#3a2a1c",
        hint_capture="#1a120c",
    ),
}

UI_THEMES = {
    "dark": UiTheme(
        name="dark",
        app_bg="#12151c",
        panel_bg="#12151c",
        card_bg="#1c2230",
        card_border="#4a5568",
        text="#f0f3fa",
        muted="#a8b2c5",
        accent="#7aa2ff",
        accent_soft="#243352",
        row_alt="#171c28",
        list_bg="#151a26",
        input_bg="#151a26",
        input_border="#5a657a",
        button_bg="#252c3c",
        button_hover="#2f3850",
    ),
    "light": UiTheme(
        name="light",
        app_bg="#e7ebf3",
        panel_bg="#e7ebf3",
        card_bg="#ffffff",
        card_border="#b8c0d0",
        text="#151a24",
        muted="#5b6578",
        accent="#2f62e4",
        accent_soft="#dce6fb",
        row_alt="#eef2f8",
        list_bg="#f5f7fb",
        input_bg="#ffffff",
        input_border="#9aa6bb",
        button_bg="#eef2f8",
        button_hover="#e2e8f4",
    ),
}

# Preferred pairing: green board with dark UI, wood with either.
DEFAULT_BOARD_FOR_UI = {
    "dark": "green",
    "light": "wood",
}
