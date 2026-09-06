"""
Basit "Ayarlar" penceresi (tkinter).

config.yaml dosyasini elle duzenlemek yerine, kurallari (kategori adi,
uzantilar, hedef klasor) gorsel olarak eklemek / duzenlemek / silmek /
siralamak icin kucuk bir pencere. tkinter Python ile birlikte gelir,
ekstra bir kutuphane kurulumu gerekmez.

Bu modul organizer.py / pystray'e BAGIMLI DEGILDIR -- sadece yaml ve
tkinter kullanir. Boylece tray_app.py disinda da (ör. test icin) tek
basina calisir.

Acik/koyu tema (light/dark mode) destegi `theme.py` modulunde --
pencere acildiginda config.yaml'daki `ui_theme` ayarina ("auto" /
"light" / "dark") gore uygulanir, ve pencerenin sag ustundeki kucuk
dugmeyle aninda degistirilebilir.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

import yaml

import theme
from config_writer import render_config_yaml
from i18n import t


def _split_csv(text: str) -> list:
    return [part.strip() for part in text.split(",") if part.strip()]


def _theme_button_key(preference: str) -> str:
    return {
        "light": "theme_mode_light",
        "dark": "theme_mode_dark",
    }.get(preference, "theme_mode_auto")


class RuleDialog(tk.Toplevel):
    """Tek bir kural eklemek/duzenlemek icin acilan alt pencere.
    Sonuc `self.result` alanina (dict ya da None) yazilir."""

    def __init__(self, parent, lang: str, rule: dict = None, theme_pref: str = "auto"):
        super().__init__(parent)
        self.lang = lang
        self.result = None
        rule = rule or {}

        self.title(
            t(lang, "rule_dialog_edit_title" if rule else "rule_dialog_add_title")
        )
        self.resizable(False, False)
        self.transient(parent)

        theme.apply_theme(self, theme_pref)

        container = ttk.Frame(self, padding=4)
        container.pack(fill="both", expand=True)

        pad = {"padx": 10, "pady": 4}

        ttk.Label(container, text=t(lang, "rule_field_name")).grid(
            row=0, column=0, sticky="w", **pad
        )
        self.name_var = tk.StringVar(value=rule.get("name", ""))
        ttk.Entry(container, textvariable=self.name_var, width=48).grid(
            row=0, column=1, columnspan=2, **pad
        )

        ttk.Label(container, text=t(lang, "rule_field_extensions")).grid(
            row=1, column=0, sticky="w", **pad
        )
        self.ext_var = tk.StringVar(value=", ".join(rule.get("extensions", [])))
        ttk.Entry(container, textvariable=self.ext_var, width=48).grid(
            row=1, column=1, columnspan=2, **pad
        )
        ttk.Label(
            container, text=t(lang, "rule_field_extensions_hint"), style="Muted.TLabel"
        ).grid(row=2, column=1, columnspan=2, sticky="w", padx=10)

        ttk.Label(container, text=t(lang, "rule_field_keywords")).grid(
            row=3, column=0, sticky="w", **pad
        )
        self.kw_var = tk.StringVar(value=", ".join(rule.get("name_contains", [])))
        ttk.Entry(container, textvariable=self.kw_var, width=48).grid(
            row=3, column=1, columnspan=2, **pad
        )
        ttk.Label(
            container, text=t(lang, "rule_field_keywords_hint"), style="Muted.TLabel"
        ).grid(row=4, column=1, columnspan=2, sticky="w", padx=10)

        ttk.Label(container, text=t(lang, "rule_field_destination")).grid(
            row=5, column=0, sticky="w", **pad
        )
        self.dest_var = tk.StringVar(value=rule.get("destination", ""))
        ttk.Entry(container, textvariable=self.dest_var, width=38).grid(
            row=5, column=1, sticky="w", **pad
        )
        ttk.Button(
            container, text=t(lang, "settings_browse"), command=self._browse
        ).grid(row=5, column=2, sticky="w", **pad)

        btns = ttk.Frame(container)
        btns.grid(row=6, column=0, columnspan=3, pady=12)
        ttk.Button(
            btns, text=t(lang, "settings_save"), width=12, command=self._ok
        ).pack(side="left", padx=6)
        ttk.Button(
            btns, text=t(lang, "settings_cancel"), width=12, command=self.destroy
        ).pack(side="left", padx=6)

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _browse(self):
        path = filedialog.askdirectory(parent=self)
        if path:
            self.dest_var.set(path)

    def _ok(self):
        name = self.name_var.get().strip()
        dest = self.dest_var.get().strip()
        extensions = _split_csv(self.ext_var.get())
        keywords = _split_csv(self.kw_var.get())

        if not name or not dest or (not extensions and not keywords):
            messagebox.showerror(
                t(self.lang, "rule_validation_error_title"),
                t(self.lang, "rule_validation_error_body"),
                parent=self,
            )
            return

        extensions = [e if e.startswith(".") else f".{e}" for e in extensions]

        self.result = {
            "name": name,
            "extensions": extensions,
            "name_contains": keywords,
            "destination": dest,
        }
        self.destroy()


class SettingsWindow(tk.Toplevel):
    """Ana Ayarlar penceresi. `on_saved` -- kaydedildiginde cagrilan,
    parametresiz bir callback (tray_app burada service.reload() ve
    menu yenilemesini tetikler)."""

    def __init__(self, root, config_path: Path, language: str, on_saved=None):
        super().__init__(root)
        self.config_path = Path(config_path)
        self.on_saved = on_saved

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f) or {}

        self.lang = self.data.get("language", language) or language or "tr"
        self.theme_pref = self.data.get("ui_theme") or "auto"
        if self.theme_pref not in theme.MODES:
            self.theme_pref = "auto"

        # config.yaml'daki her kural "match: {extensions, name_contains, ...}"
        # seklinde IC ICE yaziliyor (organizer.py'nin okudugu gercek sema).
        # GUI ve config_writer.py ise duz (flat) alanlarla calisiyor --
        # burada ic ice yapidan duze cevirip self.rules'a aliyoruz, yoksa
        # var olan kurallarin eslesme kosullari kaydederken kaybolur.
        self.rules = []
        for raw_rule in self.data.get("rules") or []:
            match = raw_rule.get("match") or {}
            self.rules.append(
                {
                    "name": raw_rule.get("name", ""),
                    "extensions": list(match.get("extensions") or []),
                    "name_contains": list(match.get("name_contains") or []),
                    "regex": match.get("regex"),
                    "older_than_days": match.get("older_than_days"),
                    "destination": raw_rule.get("destination", ""),
                }
            )

        self.title(t(self.lang, "settings_title"))
        self.geometry("700x600")
        self.minsize(620, 500)

        self.colors = theme.apply_theme(self, self.theme_pref)

        self._build()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.grab_set()

    # ------------------------------------------------------------- build

    def _build(self):
        lang = self.lang
        pad = {"padx": 10, "pady": 6}

        top = ttk.Frame(self)
        top.pack(fill="x", **pad)
        top.grid_columnconfigure(4, weight=1)

        ttk.Label(top, text=t(lang, "settings_language_label")).grid(
            row=0, column=0, sticky="w"
        )
        self.language_var = tk.StringVar(
            value="Türkçe" if self.data.get("language", "tr") == "tr" else "English"
        )
        lang_box = ttk.Combobox(
            top,
            textvariable=self.language_var,
            values=["Türkçe", "English"],
            state="readonly",
            width=15,
        )
        lang_box.grid(row=0, column=1, sticky="w", padx=6)

        self.theme_btn = ttk.Button(
            top,
            text=t(lang, _theme_button_key(self.theme_pref)),
            style="Toggle.TButton",
            command=self._toggle_theme,
        )
        self.theme_btn.grid(row=0, column=5, sticky="e")

        ttk.Label(top, text=t(lang, "settings_watch_folder_label")).grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )
        self.watch_folder_var = tk.StringVar(
            value=self.data.get("watch_folder", "~/Downloads")
        )
        ttk.Entry(top, textvariable=self.watch_folder_var, width=45).grid(
            row=1, column=1, columnspan=3, sticky="w", padx=6, pady=(8, 0)
        )
        ttk.Button(
            top, text=t(lang, "settings_browse"), command=self._browse_watch_folder
        ).grid(row=1, column=5, sticky="e", pady=(8, 0))

        # --- Kurallar ---
        ttk.Label(self, text=t(lang, "settings_rules_label")).pack(
            anchor="w", padx=10, pady=(10, 2)
        )

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10)

        columns = ("name", "match", "destination")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse"
        )
        self.tree.heading("name", text=t(lang, "settings_col_name"))
        self.tree.heading("match", text=t(lang, "settings_col_match"))
        self.tree.heading("destination", text=t(lang, "settings_col_destination"))
        self.tree.column("name", width=170, anchor="w")
        self.tree.column("match", width=220, anchor="w")
        self.tree.column("destination", width=220, anchor="w")

        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_col = ttk.Frame(self)
        btn_col.pack(fill="x", padx=10, pady=6)
        ttk.Button(
            btn_col, text=t(lang, "settings_add_rule"), command=self._add_rule
        ).pack(side="left", padx=3)
        ttk.Button(
            btn_col, text=t(lang, "settings_edit_rule"), command=self._edit_rule
        ).pack(side="left", padx=3)
        ttk.Button(
            btn_col, text=t(lang, "settings_delete_rule"), command=self._delete_rule
        ).pack(side="left", padx=3)
        ttk.Button(
            btn_col, text=t(lang, "settings_move_up"), command=lambda: self._move(-1)
        ).pack(side="left", padx=(20, 3))
        ttk.Button(
            btn_col, text=t(lang, "settings_move_down"), command=lambda: self._move(1)
        ).pack(side="left", padx=3)

        # --- Varsayilan hedef ---
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=(6, 2))
        ttk.Label(bottom, text=t(lang, "settings_default_destination_label")).grid(
            row=0, column=0, sticky="w"
        )
        self.default_dest_var = tk.StringVar(
            value=self.data.get("default_destination") or ""
        )
        ttk.Entry(bottom, textvariable=self.default_dest_var, width=45).grid(
            row=0, column=1, sticky="w", padx=6
        )
        ttk.Button(
            bottom,
            text=t(lang, "settings_browse"),
            command=lambda: self._browse_into(self.default_dest_var),
        ).grid(row=0, column=2, sticky="w")

        # --- Klasorleri de duzenle ---
        self.organize_folders_var = tk.BooleanVar(
            value=bool(self.data.get("organize_folders", False))
        )
        ttk.Checkbutton(
            bottom,
            text=t(lang, "settings_organize_folders_label"),
            variable=self.organize_folders_var,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        ttk.Label(bottom, text=t(lang, "settings_folders_destination_label")).grid(
            row=2, column=0, sticky="w"
        )
        self.folders_dest_var = tk.StringVar(
            value=self.data.get("folders_destination") or ""
        )
        ttk.Entry(bottom, textvariable=self.folders_dest_var, width=45).grid(
            row=2, column=1, sticky="w", padx=6
        )
        ttk.Button(
            bottom,
            text=t(lang, "settings_browse"),
            command=lambda: self._browse_into(self.folders_dest_var),
        ).grid(row=2, column=2, sticky="w")

        # --- Kaydet / Iptal ---
        action_row = ttk.Frame(self)
        action_row.pack(fill="x", padx=10, pady=12)
        ttk.Button(
            action_row, text=t(lang, "settings_save"), width=14, command=self._save
        ).pack(side="right", padx=4)
        ttk.Button(
            action_row,
            text=t(lang, "settings_cancel"),
            width=14,
            command=self.destroy,
        ).pack(side="right", padx=4)

        self._refresh_tree()

    # ------------------------------------------------------------ helpers

    def _toggle_theme(self):
        self.theme_pref = theme.next_preference(self.theme_pref)
        self.colors = theme.apply_theme(self, self.theme_pref)
        self.theme_btn.configure(text=t(self.lang, _theme_button_key(self.theme_pref)))
        self._refresh_tree()

    def _match_summary(self, rule: dict) -> str:
        parts = []
        if rule.get("extensions"):
            parts.append(", ".join(rule["extensions"]))
        if rule.get("name_contains"):
            parts.append("“" + ", ".join(rule["name_contains"]) + "”")
        return " / ".join(parts)

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.tree.tag_configure("oddrow", background=self.colors["tree_bg"])
        self.tree.tag_configure("evenrow", background=self.colors["tree_alt_bg"])
        for idx, rule in enumerate(self.rules):
            tag = "evenrow" if idx % 2 else "oddrow"
            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    rule.get("name", ""),
                    self._match_summary(rule),
                    rule.get("destination", ""),
                ),
                tags=(tag,),
            )

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _browse_watch_folder(self):
        path = filedialog.askdirectory(parent=self)
        if path:
            self.watch_folder_var.set(path)

    def _browse_into(self, string_var: tk.StringVar):
        path = filedialog.askdirectory(parent=self)
        if path:
            string_var.set(path)

    # ------------------------------------------------------------- rules

    def _add_rule(self):
        dialog = RuleDialog(self, self.lang, theme_pref=self.theme_pref)
        self.wait_window(dialog)
        if dialog.result:
            self.rules.append(dialog.result)
            self._refresh_tree()

    def _edit_rule(self):
        idx = self._selected_index()
        if idx is None:
            return
        dialog = RuleDialog(
            self, self.lang, rule=self.rules[idx], theme_pref=self.theme_pref
        )
        self.wait_window(dialog)
        if dialog.result:
            self.rules[idx] = dialog.result
            self._refresh_tree()

    def _delete_rule(self):
        idx = self._selected_index()
        if idx is None:
            return
        name = self.rules[idx].get("name", "")
        if messagebox.askyesno(
            t(self.lang, "settings_delete_confirm_title"),
            t(self.lang, "settings_delete_confirm_body", name=name),
            parent=self,
        ):
            del self.rules[idx]
            self._refresh_tree()

    def _move(self, direction: int):
        idx = self._selected_index()
        if idx is None:
            return
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self.rules):
            return
        self.rules[idx], self.rules[new_idx] = self.rules[new_idx], self.rules[idx]
        self._refresh_tree()
        self.tree.selection_set(str(new_idx))

    # -------------------------------------------------------------- save

    def _save(self):
        self.data["language"] = "tr" if self.language_var.get() == "Türkçe" else "en"
        self.data["ui_theme"] = self.theme_pref
        self.data["watch_folder"] = self.watch_folder_var.get().strip() or "~/Downloads"
        self.data["rules"] = self.rules
        self.data["default_destination"] = self.default_dest_var.get().strip() or None
        self.data["organize_folders"] = bool(self.organize_folders_var.get())
        self.data["folders_destination"] = self.folders_dest_var.get().strip() or None

        text = render_config_yaml(self.data)
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write(text)

        messagebox.showinfo(
            t(self.data["language"], "settings_saved_title"),
            t(self.data["language"], "settings_saved_body"),
            parent=self,
        )

        if self.on_saved:
            self.on_saved()

        self.destroy()
