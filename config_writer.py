"""
config.yaml dosyasini programatik olarak (Ayarlar penceresinden)
yeniden yazmak icin kullanilan sade bir YAML uretici.

Generic PyYAML dump() yerine elle bir sablon yaziyoruz, cunku:

1) Dosya, orijinal config.yaml ile ayni okunakli bicimde kalir.
2) Windows yollarindaki ters egik cizgiler (\\), CIFT tirnakli YAML
   string'lerinde kacis karakteri (escape) olarak yorumlanabilir --
   bu yuzden TEK tirnakli YAML skalerleri kullaniyoruz (YAML'de tek
   tirnak icinde backslash'in ozel bir anlami yoktur).

We hand-write the template instead of using PyYAML's generic dump()
because: (1) the file stays in the same readable shape as the
original config.yaml, and (2) backslashes in Windows paths could be
misread as escape sequences inside double-quoted YAML scalars -- so
we use single-quoted scalars instead (backslash has no special
meaning inside single quotes in YAML).
"""

from __future__ import annotations


def _sq(value) -> str:
    """Guvenli, tek-tirnakli bir YAML skaler degeri metni uretir."""
    s = "" if value is None else str(value)
    return "'" + s.replace("'", "''") + "'"


def render_config_yaml(data: dict) -> str:
    """`data` (yaml.safe_load ile okunmus/degistirilmis bir dict) icin
    yeni bir config.yaml metni uretir."""
    lines = []
    lines.append("# =============================================================")
    lines.append("# İndirilenler Klasörü Otomatik Düzenleyici - Kural Dosyası")
    lines.append("# Downloads Folder Auto-Organizer - Rules File")
    lines.append("# =============================================================")
    lines.append("# Bu dosya tepsi menüsündeki \"Ayarlar\" penceresinden")
    lines.append("# değiştirilebilir, ya da elle düzenlenebilir.")
    lines.append("# This file can be changed from the tray menu's \"Settings\"")
    lines.append("# window, or edited by hand.")
    lines.append("")

    lines.append(f"language: {_sq(data.get('language', 'tr'))}")
    lines.append("")

    lines.append(f"ui_theme: {_sq(data.get('ui_theme', 'auto'))}")
    lines.append("")

    lines.append(f"watch_folder: {_sq(data.get('watch_folder', '~/Downloads'))}")
    lines.append("")

    ignore_extensions = data.get("ignore_extensions") or []
    lines.append("ignore_extensions:")
    for ext in ignore_extensions:
        lines.append(f"  - {_sq(ext)}")
    lines.append("")

    lines.append(f"stability_check_seconds: {data.get('stability_check_seconds', 2)}")
    lines.append(f"poll_interval_seconds: {data.get('poll_interval_seconds', 1)}")
    lines.append("")

    lines.append("rules:")
    for rule in data.get("rules") or []:
        lines.append(f"  - name: {_sq(rule.get('name', ''))}")
        lines.append("    match:")
        extensions = rule.get("extensions") or []
        name_contains = rule.get("name_contains") or []
        regex = rule.get("regex")
        older_than_days = rule.get("older_than_days")

        if extensions:
            ext_inline = ", ".join(_sq(e) for e in extensions)
            lines.append(f"      extensions: [{ext_inline}]")
        if name_contains:
            kw_inline = ", ".join(_sq(k) for k in name_contains)
            lines.append(f"      name_contains: [{kw_inline}]")
        if regex:
            lines.append(f"      regex: {_sq(regex)}")
        if older_than_days is not None:
            lines.append(f"      older_than_days: {older_than_days}")

        lines.append(f"    destination: {_sq(rule.get('destination', ''))}")
        lines.append("")

    lines.append(f"default_destination: {_sq(data.get('default_destination') or '')}")
    lines.append(f"log_file: {_sq(data.get('log_file', '~/Downloads/.organizer_log.txt'))}")
    lines.append("")

    lines.append(f"organize_folders: {'true' if data.get('organize_folders') else 'false'}")
    lines.append(f"folders_destination: {_sq(data.get('folders_destination') or '')}")
    lines.append("")

    return "\n".join(lines)
