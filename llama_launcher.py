import os
import sys
import json
import yaml
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class LlamaLauncherApp:
    def __init__(self, root):
        self.root = root

        # Определение базовой директории (совместимо с PyInstaller)
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self.config_file = os.path.join(self.base_dir, "launcher_config.json")
        self.yaml_config_file = os.path.join(self.base_dir, "app_config.yaml")

        # 1. Загружаем статический конфиг YAML (все дефолты тут)
        self.yaml_data = self.load_yaml_config()

        # 2. Загружаем динамический конфиг пользователя
        self.config = self.load_config()

        # 3. Динамический поиск доступных языковых файлов возле EXE
        self.available_languages = self.discover_languages()

        # Определяем текущий язык (берем из конфига, либо первый доступный, либо ru по умолчанию)
        self.current_lang = self.config.get("language")
        if self.current_lang not in self.available_languages:
            self.current_lang = "ru" if "ru" in self.available_languages else (self.available_languages[0] if self.available_languages else "ru")

        self.translations = self.load_translations(self.current_lang)

        # 4. Базовые пути (ИСПРАВЛЕНО: если в JSON пусто, берем дефолты из YAML)
        self.llama_exe_path = self.config.get("llama_exe_path") or self.yaml_data.get("llama_exe_path", "")
        self.models_dir = self.config.get("models_dir") or self.yaml_data.get("models_dir", "")

        self.widgets_ref = {}

        # Параметры окна (ИСПРАВЛЕНО: ширина уменьшена до компактной)
        self.root.title("Llama.exe Serve Launcher")
        self.root.geometry("840x660")
        self.root.minsize(800, 600)

        self.create_widgets()
        self.scan_models_directory()

    def load_yaml_config(self):
        if os.path.exists(self.yaml_config_file):
            try:
                with open(self.yaml_config_file, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
        return {"flags": {}}

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f) or {}
            except Exception:
                pass
        return {}

    def save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def discover_languages(self):
        """Сканирует папку программы на наличие файлов lang_*.json и возвращает список кодов языков."""
        langs = []
        try:
            for file in os.listdir(self.base_dir):
                if file.startswith("lang_") and file.endswith(".json"):
                    lang_code = file[5:-5] # Вырезаем "lang_" и ".json"
                    if lang_code:
                        langs.append(lang_code)
        except Exception:
            pass
        return langs if langs else ["ru"]

    def load_translations(self, lang):
        lang_file = os.path.join(self.base_dir, f"lang_{lang}.json")
        if os.path.exists(lang_file):
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def t(self, key):
        return self.translations.get(key, key)
    def change_language(self, event=None):
        new_lang = self.lang_combo.get()
        if new_lang != self.current_lang:
            self.current_lang = new_lang
            self.config["language"] = new_lang
            self.save_config()
            self.translations = self.load_translations(new_lang)

            # Полная перерисовка интерфейса
            for w in self.root.winfo_children():
                w.destroy()
            self.create_widgets()
            self.scan_models_directory()

    def _get_dynamic_flag_value(self, flag, model_name, saved_value):
        """Единая точка для вычисления значений флагов с учетом сохраненных пресетов."""
        match flag:
            case "--alias":
                if not model_name or model_name == self.t("no_subdirs"):
                    return ""
                clean_alias = model_name.replace("-GGUF", "").strip()
                return clean_alias
            case _:
                return saved_value

    def browse_exe(self):
        p = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if p:
            self.llama_exe_path = p
            self.exe_entry.delete(0, tk.END)
            self.exe_entry.insert(0, p)
            self.config["llama_exe_path"] = p
            self.save_config()
            self.update_command_preview()

    def browse_models(self):
        d = filedialog.askdirectory()
        if d:
            self.models_dir = d
            self.models_entry.delete(0, tk.END)
            self.models_entry.insert(0, d)
            self.config["models_dir"] = d
            self.save_config()
            self.scan_models_directory()

    def create_widgets(self):
        # Верхняя панель (Пути и Выбор Языка)
        top_panel = ttk.Frame(self.root, padding=10)
        top_panel.pack(fill="x", side="top")

        # Пути: Используем ваши оригинальные title_exe и title_dir
        paths_frame = ttk.LabelFrame(top_panel, text=self.t("title_exe") + " / " + self.t("title_dir"), padding=10)
        paths_frame.pack(fill="x", side="left", expand=True, padx=(0, 10))

        ttk.Label(paths_frame, text=self.t("title_exe") + ":").grid(row=0, column=0, sticky="w", pady=2)
        self.exe_entry = ttk.Entry(paths_frame, width=40)
        self.exe_entry.insert(0, self.llama_exe_path)
        self.exe_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(paths_frame, text=self.t("btn_browse"), command=self.browse_exe).grid(row=0, column=2, padx=2, pady=2)

        ttk.Label(paths_frame, text=self.t("title_dir") + ":").grid(row=1, column=0, sticky="w", pady=2)
        self.models_entry = ttk.Entry(paths_frame, width=40)
        self.models_entry.insert(0, self.models_dir)
        self.models_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(paths_frame, text=self.t("btn_browse"), command=self.browse_models).grid(row=1, column=2, padx=2, pady=2)
        paths_frame.columnconfigure(1, weight=1)

        # Настройки языка: заголовок и метка динамические
        lang_frame = ttk.LabelFrame(top_panel, text=self.t("title_lang"), padding=10)
        lang_frame.pack(fill="y", side="right")

        ttk.Label(lang_frame, text=self.t("title_lang")).pack(side="left", padx=5)
        self.lang_combo = ttk.Combobox(lang_frame, values=self.available_languages, state="readonly", width=6)
        self.lang_combo.set(self.current_lang)
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_language)
        self.lang_combo.pack(side="left", padx=5)

        # Средняя панель управления моделями (title_model)
        mid_panel = ttk.Frame(self.root, padding=10)
        mid_panel.pack(fill="x", side="top")

        model_frame = ttk.LabelFrame(mid_panel, text=self.t("title_model"), padding=10)
        model_frame.pack(fill="x", expand=True)

        self.model_combo = ttk.Combobox(model_frame, state="readonly")
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_selected)
        self.model_combo.pack(fill="x", side="left", expand=True)

        # Секция флагов запуска (title_flags)
        flags_main_frame = ttk.LabelFrame(self.root, text=self.t("title_flags"), padding=5)
        flags_main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(flags_main_frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(flags_main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        # Нижняя панель (title_preview, btn_copy, btn_run)
        bottom_panel = ttk.Frame(self.root, padding=10)
        bottom_panel.pack(fill="x", side="bottom")

        preview_frame = ttk.LabelFrame(bottom_panel, text=self.t("title_preview"), padding=10)
        preview_frame.pack(fill="x", side="top", expand=True, pady=(0, 5))

        # Текстовое поле tk.Text без изменений стилей
        self.preview_text = tk.Text(preview_frame, height=3, wrap="word", font=("Consolas", 9))
        self.preview_text.pack(fill="x", side="left", expand=True, padx=(0, 5))
        self.preview_text.config(state="disabled")

        ttk.Button(preview_frame, text=self.t("btn_copy"), command=self.copy_command_to_clipboard).pack(side="right", fill="y")

        # Кнопка запуска со стандартным системным стилем
        self.run_btn = ttk.Button(bottom_panel, text=self.t("btn_run"), command=self.launch_server)
        self.run_btn.pack(fill="x", side="bottom", pady=5)

    def render_flags_inputs(self):
        for w in self.scrollable_frame.winfo_children(): w.destroy()
        self.widgets_ref = {}
        self.scrollable_frame.columnconfigure(0, weight=1, uniform="group1")
        self.scrollable_frame.columnconfigure(1, weight=1, uniform="group1")

        m = self.model_combo.get()

        def _on_mouse_wheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.scrollable_frame.bind_all("<MouseWheel>", _on_mouse_wheel)

        for idx, (fl, inf) in enumerate(self.yaml_data.get("flags", {}).items()):
            cell = ttk.Frame(self.scrollable_frame, padding=5)
            cell.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=10, pady=4)
            top_row = ttk.Frame(cell)
            top_row.pack(fill="x", side="top")

            cv = tk.BooleanVar(value=inf["active"])
            cv.trace_add("write", self.on_input_changed)

            display_name = fl.lstrip("-")
            ttk.Checkbutton(top_row, variable=cv, text=display_name).pack(side="left", anchor="w")

            # Фрейм-контейнер для ввода теперь расширяется fill="x", expand=True
            ifr = ttk.Frame(top_row)
            ifr.pack(side="right", fill="x", expand=True, padx=(15, 5))

            initial_val = self._get_dynamic_flag_value(fl, m, str(inf["value"]))
            vv = tk.StringVar(value=initial_val)
            vv.trace_add("write", self.on_input_changed)

            # Виджеты создаются с минимальной шириной, но растягиваются по сетке фрейма
            if inf["type"] == "combo":
                el = ttk.Combobox(ifr, textvariable=vv, values=inf["options"], width=8)
                el.config(state="normal" if fl == "--gpu-layers" else "readonly")
                el.bind("<<ComboboxSelected>>", self.on_input_changed)
                el.bind("<MouseWheel>", lambda e: "break")
            else:
                el = ttk.Entry(ifr, textvariable=vv, width=10)

            # Использование fill="x", expand=True делает поля ввода полностью гибкими (flexible)
            el.pack(fill="x", expand=True, side="right")

            ttk.Label(cell, text=self.t(inf["desc"]), font=("Arial", 8), foreground="#7f8c8d", wraplength=380).pack(side="top", anchor="w", pady=2)
            self.widgets_ref[fl] = {"check_var": cv, "value_var": vv}

    def scan_models_directory(self):
        if not self.models_dir or not os.path.exists(self.models_dir):
            self.model_combo["values"] = []
            self.render_flags_inputs()
            self.update_command_preview() # Чтобы превью не оставалось пустым
            return

        s = [d for d in os.listdir(self.models_dir) if os.path.isdir(os.path.join(self.models_dir, d))]
        self.model_combo["values"] = s

        if s:
            last_model = self.config.get("last_selected_model", "")
            if last_model in s:
                idx = s.index(last_model)
                self.model_combo.current(idx)
            else:
                self.model_combo.current(0)

            self.render_flags_inputs()
            self.on_model_selected()
        else:
            self.model_combo.set(self.t("no_subdirs"))
            self.render_flags_inputs()
            self.update_command_preview()

    def on_model_selected(self, event=None):
        m = self.model_combo.get()
        if not m or m == self.t("no_subdirs"): return
        st = self.config.get("models", {}).get(m, {}).get("flags", {})

        for fl in self.yaml_data.get("flags", {}):
            if fl in self.widgets_ref:
                try:
                    self.widgets_ref[fl]["check_var"].trace_remove("write", self.widgets_ref[fl]["check_var"].trace_info())
                    self.widgets_ref[fl]["value_var"].trace_remove("write", self.widgets_ref[fl]["value_var"].trace_info())
                except Exception: pass

                raw_val = st[fl]["value"] if fl in st else str(self.yaml_data["flags"][fl]["value"])
                final_val = self._get_dynamic_flag_value(fl, m, raw_val)

                self.widgets_ref[fl]["check_var"].set(st[fl]["active"] if fl in st else self.yaml_data["flags"][fl]["active"])
                self.widgets_ref[fl]["value_var"].set(final_val)

                self.widgets_ref[fl]["check_var"].trace_add("write", self.on_input_changed)
                self.widgets_ref[fl]["value_var"].trace_add("write", self.on_input_changed)

        self.config["last_selected_model"] = m
        self.save_config()
        self.update_command_preview()

    def on_input_changed(self, *args):
        self.update_command_preview()

    def find_largest_file(self, folder_path):
        if not os.path.exists(folder_path): return None
        lf = None
        ms = -1
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                fp = os.path.join(root, file)
                try:
                    sz = os.path.getsize(fp)
                    if sz > ms:
                        ms = sz
                        lf = fp
                except Exception:
                    pass
        return lf

    def generate_command_list(self, clean_exe=False):
        m = self.model_combo.get()
        if not m or m == self.t("no_subdirs"): return None
        if not self.models_dir or not os.path.exists(self.models_dir): return None

        mf = self.find_largest_file(os.path.join(self.models_dir, m))
        if not mf: return None

        cmds = ["llama.exe" if clean_exe else f'"{self.llama_exe_path}"', "serve"]

        for fl in self.yaml_data.get("flags", {}):
            if fl in self.widgets_ref and self.widgets_ref[fl]["check_var"].get():
                cmds.append(fl)
                current_ui_val = self.widgets_ref[fl]["value_var"].get().strip()
                v = self._get_dynamic_flag_value(fl, m, current_ui_val)
                if v: cmds.append(v)

        cmds.extend(["--model", f'"{mf}"'])
        return cmds

    def update_command_preview(self):
        cmds = self.generate_command_list(clean_exe=True)
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", tk.END)
        if cmds:
            self.preview_text.insert("1.0", " ".join(cmds))
        else:
            self.preview_text.insert("1.0", self.t("err_validation"))
        self.preview_text.config(state="disabled")

    def copy_command_to_clipboard(self):
        cmds = self.generate_command_list(clean_exe=True)
        if cmds:
            self.root.clipboard_clear()
            self.root.clipboard_append(" ".join(cmds))
            messagebox.showinfo("Success", self.t("copied"))

    def launch_server(self):
        if not self.llama_exe_path or not os.path.exists(self.llama_exe_path):
            messagebox.showerror("Error", self.t("err_validation"))
            return

        m = self.model_combo.get()
        if not m or m == self.t("no_subdirs"):
            messagebox.showerror("Error", self.t("err_validation"))
            return

        full_cmds = self.generate_command_list(clean_exe=False)
        clean_cmds = self.generate_command_list(clean_exe=True)

        # Если команда не собралась — значит внутри поддиректории нет файла весов
        if not full_cmds or not clean_cmds:
            messagebox.showerror("Error", self.t("err_no_model"))
            return

        if "models" not in self.config: self.config["models"] = {}
        if m not in self.config["models"]: self.config["models"][m] = {"flags": {}}

        for fl in self.yaml_data.get("flags", {}):
            if fl in self.widgets_ref:
                if "flags" not in self.config["models"][m]: self.config["models"][m]["flags"] = {}
                self.config["models"][m]["flags"][fl] = {
                    "active": self.widgets_ref[fl]["check_var"].get(),
                    "value": self.widgets_ref[fl]["value_var"].get().strip()
                }
        self.save_config()

        echo_cmd = " ".join(clean_cmds)
        real_cmd = " ".join(full_cmds)

        final_script = (
            f'@echo off\n'
            f'title Llama Serve API Server Local\n'
            f'echo =========================================================================\n'
            f'echo Launching server command:\n'
            f'echo {echo_cmd}\n'
            f'echo =========================================================================\n'
            f'echo.\n'
            f'{real_cmd}\n'
            f'pause'
        )

        try:
            bat_path = os.path.join(self.base_dir, "run_server_temp.bat")
            with open(bat_path, "w", encoding="cp866") as f:
                f.write(final_script)

            subprocess.Popen(f'start cmd /k "{bat_path}"', shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run server: {e}")
if __name__ == "__main__":
    root = tk.Tk()
    app = LlamaLauncherApp(root)
    root.mainloop()