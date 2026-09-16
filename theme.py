"""
Ayarlar penceresi icin acik/koyu tema (dark mode / light mode) destegi.
Light / dark mode theming support for the Settings window.

Bu modul organizer.py / pystray'e BAGIMLI DEGILDIR -- sadece tkinter
kullanir. `mode` "auto" ise, isletim sisteminin acik/koyu tema tercihi
okunmaya calisilir (su an icin sadece Windows'ta guvenilir sekilde
tespit edilebiliyor; diger platformlarda "light" varsayilir).

This module does NOT depend on organizer.py / pystray -- it only uses
tkinter. When `mode` is "auto", we try to read the OS's light/dark
preference (currently only reliably detectable on Windows; other
platforms default to "light").
"""

from __future__ import annotations

from tkinter import ttk

from platform_backend import backend

MODES = ("auto", "light", "dark")

_PALETTES = {
    "light": {
        "bg": "#f3f3f3",
        "surface": "#ffffff",
        "fg": "#1a1a1a",
        "muted_fg": "#6b6b6b",
        "entry_bg": "#ffffff",
        "entry_fg": "#1a1a1a",
        "border": "#c9c9c9",
        "select_bg": "#0a66c2",
        "select_fg": "#ffffff",
        "button_bg": "#e6e6e6",
        "button_active_bg": "#d8d8d8",
        "accent": "#0a66c2",
        "tree_bg": "#ffffff",
        "tree_alt_bg": "#f3f6fa",
        "tree_fg": "#1a1a1a",
        "heading_bg": "#e6e6e6",
        "heading_fg": "#1a1a1a",
    },
    "dark": {
        "bg": "#1e1f22",
        "surface": "#2b2d30",
        "fg": "#e6e6e6",
        "muted_fg": "#a0a0a0",
        "entry_bg": "#323438",
        "entry_fg": "#e6e6e6",
        "border": "#45474a",
        "select_bg": "#3f8cd6",
        "select_fg": "#ffffff",
        "button_bg": "#3a3c40",
        "button_active_bg": "#47494e",
        "accent": "#5aa3e0",
        "tree_bg": "#2b2d30",
        "tree_alt_bg": "#313336",
        "tree_fg": "#e6e6e6",
        "heading_bg": "#3a3c40",
        "heading_fg": "#e6e6e6",
    },
}


def detect_system_theme() -> str:
    """Isletim sisteminin acik/koyu tema tercihini tespit etmeye calisir.
    Basarisiz olursa ya da platform desteklenmiyorsa "light" doner.
    (Platforma ozel tespit mantigi artik platform_backend paketinde.)"""
    try:
        return backend.detect_system_theme()
    except Exception:
        return "light"


def resolve_mode(preference: str) -> str:
    """"auto" / "light" / "dark" tercihini gercek "light"/"dark" degerine
    cevirir."""
    preference = (preference or "auto").strip().lower()
    if preference == "dark":
        return "dark"
    if preference == "light":
        return "light"
    return detect_system_theme()


def next_preference(preference: str) -> str:
    """Tema tercihini dongusel olarak bir sonrakine gecirir:
    auto -> light -> dark -> auto ..."""
    preference = (preference or "auto").strip().lower()
    if preference not in MODES:
        preference = "auto"
    idx = MODES.index(preference)
    return MODES[(idx + 1) % len(MODES)]


def colors_for(preference: str) -> dict:
    mode = resolve_mode(preference)
    return _PALETTES[mode]


def apply_theme(widget, preference: str) -> dict:
    """Verilen tk widget'inin (Tk ya da Toplevel) ait oldugu ttk.Style'i
    ve kendi arka plan rengini `preference` ("auto"/"light"/"dark")
    degerine gore ayarlar. Kullanilan renk sozlugunu geri doner."""
    colors = colors_for(preference)
    style = ttk.Style(widget)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "TFrame", background=colors["bg"], borderwidth=0
    )
    style.configure(
        "TLabel", background=colors["bg"], foreground=colors["fg"]
    )
    style.configure(
        "Muted.TLabel", background=colors["bg"], foreground=colors["muted_fg"]
    )
    style.configure(
        "TCheckbutton",
        background=colors["bg"],
        foreground=colors["fg"],
        focuscolor=colors["bg"],
    )
    style.map(
        "TCheckbutton",
        background=[("active", colors["bg"])],
        foreground=[("active", colors["fg"])],
    )
    style.configure(
        "TButton",
        background=colors["button_bg"],
        foreground=colors["fg"],
        borderwidth=1,
        focuscolor=colors["bg"],
        padding=6,
    )
    style.map(
        "TButton",
        background=[("active", colors["button_active_bg"]), ("pressed", colors["button_active_bg"])],
        foreground=[("disabled", colors["muted_fg"])],
    )
    style.configure(
        "Toggle.TButton",
        background=colors["surface"],
        foreground=colors["fg"],
        borderwidth=1,
        padding=4,
    )
    style.map(
        "Toggle.TButton",
        background=[("active", colors["button_active_bg"])],
    )
    style.configure(
        "TEntry",
        fieldbackground=colors["entry_bg"],
        foreground=colors["entry_fg"],
        background=colors["entry_bg"],
        insertcolor=colors["fg"],
        bordercolor=colors["border"],
    )
    style.configure(
        "TCombobox",
        fieldbackground=colors["entry_bg"],
        foreground=colors["entry_fg"],
        background=colors["entry_bg"],
        arrowcolor=colors["fg"],
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", colors["entry_bg"])],
        foreground=[("readonly", colors["entry_fg"])],
        selectbackground=[("readonly", colors["entry_bg"])],
        selectforeground=[("readonly", colors["entry_fg"])],
    )
    style.configure(
        "Treeview",
        background=colors["tree_bg"],
        fieldbackground=colors["tree_bg"],
        foreground=colors["tree_fg"],
        bordercolor=colors["border"],
        rowheight=24,
    )
    style.map(
        "Treeview",
        background=[("selected", colors["select_bg"])],
        foreground=[("selected", colors["select_fg"])],
    )
    style.configure(
        "Treeview.Heading",
        background=colors["heading_bg"],
        foreground=colors["heading_fg"],
        borderwidth=1,
        relief="flat",
    )
    style.map(
        "Treeview.Heading",
        background=[("active", colors["button_active_bg"])],
    )
    style.configure(
        "Vertical.TScrollbar",
        background=colors["button_bg"],
        troughcolor=colors["bg"],
        bordercolor=colors["border"],
        arrowcolor=colors["fg"],
    )

    try:
        widget.configure(bg=colors["bg"])
    except Exception:
        pass

    return colors
