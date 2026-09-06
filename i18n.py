"""
Basit iki dilli metin sozlugu (Turkce / Ingilizce).
Simple bilingual string dictionary (Turkish / English).

Uygulamanin tum sabit metinleri (tepsi menusu, log mesajlari, konsol
ciktilari) buradan gelir. Hangi dilin kullanilacagi config.yaml
icindeki `language: "tr"` veya `language: "en"` ayariyla belirlenir.

All fixed strings in the app (tray menu, log messages, console output)
come from here. Which language is used is controlled by the
`language: "tr"` / `language: "en"` setting in config.yaml.
"""

from __future__ import annotations

STRINGS = {
    "tr": {
        "app_name": "İndirilenler Düzenleyici",
        "started": "Başlatıldı. İzlenen klasör: {folder} ({count} kural yüklendi)",
        "stopped": "Durduruldu.",
        "reloading": "Kurallar yeniden yükleniyor...",
        "paused": "Duraklatıldı.",
        "resumed": "Devam ettirildi.",
        "moved": "Taşındı [{rule}]: {name} -> {dest}",
        "skipped_writing": "Atlandı (hâlâ yazılıyor olabilir): {name}",
        "move_error": "HATA - {name} taşınamadı: {error}",
        "default_rule_label": "(varsayılan)",
        "folder_label": "Klasör",
        "menu_status_running": "Durum: Çalışıyor",
        "menu_status_paused": "Durum: Duraklatıldı",
        "menu_pause": "Duraklat",
        "menu_resume": "Devam Et",
        "menu_reload": "Kuralları Yeniden Yükle",
        "menu_open_folder": "İndirilenler Klasörünü Aç",
        "menu_open_rules": "Kuralları Düzenle (config.yaml)",
        "menu_open_log": "Logları Aç",
        "menu_organize_now": "Şimdi Düzenle (Mevcut Dosyalar)",
        "menu_autostart": "Bilgisayar Açılışında Başlat",
        "menu_quit": "Çıkış",
        "tray_title_running": "{app} - Çalışıyor",
        "tray_title_paused": "{app} - Duraklatıldı",
        "config_not_found": "HATA: config.yaml bulunamadı: {path}",
        "running_hint": "Çalışıyor. Durdurmak için Ctrl+C.",
        "scan_started": "Mevcut dosyalar taranıyor...",
        "scan_done": "Tarama tamamlandı: {count} dosya taşındı.",
        "autostart_enabled": "Bilgisayar açılışında otomatik başlatma AÇILDI.",
        "autostart_disabled": "Bilgisayar açılışında otomatik başlatma KAPATILDI.",
        "autostart_failed": "Otomatik başlatma ayarı değiştirilemedi.",
        "menu_settings": "Ayarlar",
        "settings_title": "Ayarlar - İndirilenler Düzenleyici",
        "settings_language_label": "Arayüz Dili:",
        "settings_watch_folder_label": "İzlenen Klasör:",
        "settings_rules_label": "Kurallar (yukarıdan aşağıya sırayla kontrol edilir):",
        "settings_col_name": "Kural Adı",
        "settings_col_match": "Eşleşme Koşulu",
        "settings_col_destination": "Hedef Klasör",
        "settings_add_rule": "Ekle...",
        "settings_edit_rule": "Düzenle...",
        "settings_delete_rule": "Sil",
        "settings_move_up": "Yukarı ↑",
        "settings_move_down": "Aşağı ↓",
        "settings_default_destination_label": "Eşleşmeyen Dosyalar İçin Varsayılan Klasör:",
        "settings_organize_folders_label": "Klasörleri de düzenle (dikkatli kullanın)",
        "settings_folders_destination_label": "Klasörler İçin Hedef:",
        "settings_save": "Kaydet",
        "settings_cancel": "İptal",
        "settings_browse": "Gözat...",
        "settings_saved_title": "Kaydedildi",
        "settings_saved_body": "Ayarlar kaydedildi ve kurallar yeniden yüklendi.",
        "settings_delete_confirm_title": "Kural silinsin mi?",
        "settings_delete_confirm_body": '"{name}" kuralı silinsin mi?',
        "rule_dialog_add_title": "Yeni Kural",
        "rule_dialog_edit_title": "Kuralı Düzenle",
        "rule_field_name": "Kural Adı:",
        "rule_field_extensions": "Dosya Uzantıları (virgülle ayırın):",
        "rule_field_extensions_hint": "Örnek: .jpg, .png, .pdf",
        "rule_field_keywords": "Dosya Adında Geçen Kelimeler (opsiyonel):",
        "rule_field_keywords_hint": "Örnek: fatura, invoice, makbuz",
        "rule_field_destination": "Hedef Klasör:",
        "rule_validation_error_title": "Eksik Bilgi",
        "rule_validation_error_body": "Lütfen bir kural adı, bir hedef klasör ve en az bir uzantı ya da kelime girin.",
        "tkinter_unavailable": "UYARI: Bu Python kurulumunda 'tkinter' bulunamadı. 'Ayarlar' penceresi kullanılamıyor; menüdeki 'Kuralları Düzenle' seçeneği bunun yerine config.yaml'ı metin editöründe açacak.",
        "theme_mode_auto": "🖥️ Tema: Otomatik",
        "theme_mode_light": "☀️ Tema: Açık",
        "theme_mode_dark": "🌙 Tema: Koyu",
    },
    "en": {
        "app_name": "Downloads Organizer",
        "started": "Started. Watching folder: {folder} ({count} rules loaded)",
        "stopped": "Stopped.",
        "reloading": "Reloading rules...",
        "paused": "Paused.",
        "resumed": "Resumed.",
        "moved": "Moved [{rule}]: {name} -> {dest}",
        "skipped_writing": "Skipped (may still be writing): {name}",
        "move_error": "ERROR - could not move {name}: {error}",
        "default_rule_label": "(default)",
        "folder_label": "Folder",
        "menu_status_running": "Status: Running",
        "menu_status_paused": "Status: Paused",
        "menu_pause": "Pause",
        "menu_resume": "Resume",
        "menu_reload": "Reload Rules",
        "menu_open_folder": "Open Downloads Folder",
        "menu_open_rules": "Edit Rules (config.yaml)",
        "menu_open_log": "Open Logs",
        "menu_organize_now": "Organize Now (Existing Files)",
        "menu_autostart": "Start at Computer Login",
        "menu_quit": "Quit",
        "tray_title_running": "{app} - Running",
        "tray_title_paused": "{app} - Paused",
        "config_not_found": "ERROR: config.yaml not found: {path}",
        "running_hint": "Running. Press Ctrl+C to stop.",
        "scan_started": "Scanning existing files...",
        "scan_done": "Scan complete: moved {count} file(s).",
        "autostart_enabled": "Start-at-login was turned ON.",
        "autostart_disabled": "Start-at-login was turned OFF.",
        "autostart_failed": "Could not change the start-at-login setting.",
        "menu_settings": "Settings",
        "settings_title": "Settings - Downloads Organizer",
        "settings_language_label": "Interface Language:",
        "settings_watch_folder_label": "Watched Folder:",
        "settings_rules_label": "Rules (checked from top to bottom):",
        "settings_col_name": "Rule Name",
        "settings_col_match": "Match Condition",
        "settings_col_destination": "Destination Folder",
        "settings_add_rule": "Add...",
        "settings_edit_rule": "Edit...",
        "settings_delete_rule": "Delete",
        "settings_move_up": "Move Up ↑",
        "settings_move_down": "Move Down ↓",
        "settings_default_destination_label": "Default Folder for Unmatched Files:",
        "settings_organize_folders_label": "Also organize folders (use with care)",
        "settings_folders_destination_label": "Destination for Folders:",
        "settings_save": "Save",
        "settings_cancel": "Cancel",
        "settings_browse": "Browse...",
        "settings_saved_title": "Saved",
        "settings_saved_body": "Settings saved and rules reloaded.",
        "settings_delete_confirm_title": "Delete this rule?",
        "settings_delete_confirm_body": 'Delete the rule "{name}"?',
        "rule_dialog_add_title": "New Rule",
        "rule_dialog_edit_title": "Edit Rule",
        "rule_field_name": "Rule Name:",
        "rule_field_extensions": "File Extensions (comma-separated):",
        "rule_field_extensions_hint": "Example: .jpg, .png, .pdf",
        "rule_field_keywords": "Keywords in File Name (optional):",
        "rule_field_keywords_hint": "Example: invoice, receipt",
        "rule_field_destination": "Destination Folder:",
        "rule_validation_error_title": "Missing Information",
        "rule_validation_error_body": "Please enter a rule name, a destination folder, and at least one extension or keyword.",
        "tkinter_unavailable": "WARNING: 'tkinter' was not found in this Python install. The 'Settings' window is unavailable; the 'Edit Rules' menu item will open config.yaml in a text editor instead.",
        "theme_mode_auto": "🖥️ Theme: Auto",
        "theme_mode_light": "☀️ Theme: Light",
        "theme_mode_dark": "🌙 Theme: Dark",
    },
}

DEFAULT_LANG = "tr"


def normalize_lang(lang: str | None) -> str:
    if not lang:
        return DEFAULT_LANG
    lang = lang.strip().lower()
    return lang if lang in STRINGS else DEFAULT_LANG


def t(lang: str, key: str, **kwargs) -> str:
    lang = normalize_lang(lang)
    template = STRINGS.get(lang, {}).get(key)
    if template is None:
        template = STRINGS[DEFAULT_LANG].get(key, key)
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template
