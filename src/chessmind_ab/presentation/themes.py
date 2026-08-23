"""UI / board theme definitions."""

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


BOARD_THEMES = {
    "green": BoardTheme(
        name="green",
        light="#f0f1d6",
        dark="#769656",
        select="#f7f769",
        last="#cdd26a",
        check="#e35d6a",
        canvas_bg="#12141a",
        coord="#d5dae6",
        frame="#1a1e28",
        frame_border="#5a6478",
        hover="#ffffff",
        hint="#1f2a24",
        hint_capture="#111111",
    ),
    "wood": BoardTheme(
        name="wood",
        light="#f0d9b5",
        dark="#b58863",
        select="#f6f669",
        last="#e6c07b",
        check="#d94848",
        canvas_bg="#241c14",
        coord="#efe4d2",
        frame="#2f241a",
        frame_border="#8a6f52",
        hover="#ffffff",
        hint="#3a2a1c",
        hint_capture="#1a120c",
    ),
}

UI_THEMES = {
    "dark": UiTheme(
        name="dark",
        app_bg="#15171d",
        panel_bg="#15171d",
        card_bg="#222632",
        card_border="#3a4152",
        text="#e8ecf4",
        muted="#9aa3b5",
        accent="#7aa2ff",
        accent_soft="#2a3550",
        row_alt="#1c212c",
        list_bg="#1a1f2a",
    ),
    "light": UiTheme(
        name="light",
        app_bg="#e8ecf3",
        panel_bg="#e8ecf3",
        card_bg="#ffffff",
        card_border="#d5dbe8",
        text="#1f2430",
        muted="#667085",
        accent="#3b6ff0",
        accent_soft="#e8eefc",
        row_alt="#f4f6fb",
        list_bg="#f7f8fb",
    ),
}
