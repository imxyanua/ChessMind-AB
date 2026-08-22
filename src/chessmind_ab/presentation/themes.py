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
    text: str
    muted: str
    accent: str


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
        app_bg="#1b1d24",
        panel_bg="#252833",
        text="#e8ecf4",
        muted="#9aa3b5",
        accent="#7aa2ff",
    ),
    "light": UiTheme(
        name="light",
        app_bg="#eef1f6",
        panel_bg="#ffffff",
        text="#1f2430",
        muted="#667085",
        accent="#3b6ff0",
    ),
}
