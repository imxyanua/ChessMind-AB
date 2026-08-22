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
        light="#ebecd0",
        dark="#739552",
        select="#f6f669",
        last="#cdd26a",
        check="#e35d6a",
        canvas_bg="#14161c",
        coord="#c8cdd8",
    ),
    "wood": BoardTheme(
        name="wood",
        light="#f0d9b5",
        dark="#b58863",
        select="#f6f669",
        last="#e6c07b",
        check="#d94848",
        canvas_bg="#2a2118",
        coord="#e8dcc8",
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
