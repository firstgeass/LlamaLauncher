import os
import sys
import json
import yaml
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ОПРЕДЕЛЕНИЕ ПУТИ: Системный хак для PyInstaller.
# Если программа скомпилирована в .exe, берем папку с файлом .exe через sys.executable.
# Если запущен обычный .py скрипт, берем папку через __file__.
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "launcher_config.json")
YAML_CONFIG_FILE = os.path.join(BASE_DIR, "app_config.yaml")

class AdvancedLlamaLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Llama.exe Serve Launcher")
        self.root.geometry("1100x800")
        
        self.load_yaml_config()
        self.current_lang = self.yaml_data.get("default_lang", "en")
        self.translations = self.load_language_file(self.current_lang)
        self.config = self.load_user_config()
        self.widgets_ref = {}
        
        self.create_widgets()
        self.scan_models_directory()

    def load_yaml_config(self):
        if os.path.exists(YAML_CONFIG_FILE):
            try:
                with open(YAML_CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.yaml_data = yaml.safe_load(f)
                    if self.yaml_data and "flags" in self.yaml_data:
                        return
            except Exception as e:
                print(f"Error reading YAML: {e}")
        
        # Полный резервный дубль вашей конфигурации на случай сбоя чтения файла
        self.yaml_data = {
            "default_lang": "en",
            "models_dir": "D:\\Models\\lmstudio-community",
            "llama_exe_path": "C:\\llama.cpp\\llama.exe",
            "flags": {
                "--ctx-size": {"value": "262144", "active": True, "type": "entry", "desc": "desc_ctx"},
                "--gpu-layers": {"value": "999", "active": True, "type": "combo", "options": ["999", "0"], "desc": "desc_gpu"},
                "--batch-size": {"value": "512", "active": True, "type": "entry", "desc": "desc_batch"},
                "--ubatch-size": {"value": "256", "active": True, "type": "entry", "desc": "desc_ubatch"},
                "--flash-attn": {"value": "on", "active": True, "type": "combo", "options": ["on", "off", "auto"], "desc": "desc_flash"},
                "--temp": {"value": "0.6", "active": True, "type": "entry", "desc": "desc_temp"},
                "--top-k": {"value": "20", "active": True, "type": "entry", "desc": "desc_topk"},
                "--top-p": {"value": "0.95", "active": True, "type": "entry", "desc": "desc_topp"},
                "--repeat-penalty": {"value": "1.0", "active": True, "type": "entry", "desc": "desc_repeat"},
                "--presence-penalty": {"value": "0.0", "active": True, "type": "entry", "desc": "desc_presence"},
                "--spec-type": {"value": "draft-mtp", "active": False, "type": "combo", "options": ["draft-simple", "draft-eagle3", "draft-dflash", "draft-dspark", "draft-mtp", "ngram-cache", "ngram-simple", "ngram-map-k", "ngram-map-k4v", "ngram-mod"], "desc": "desc_spectype"},
                "--spec-draft-n-max": {"value": "2", "active": False, "type": "entry", "desc": "desc_specmax"},
                "--tensor-split": {"value": "1,1", "active": False, "type": "entry", "desc": "desc_tensor"},
                "--port": {"value": "3090", "active": True, "type": "entry", "desc": "desc_port"}
            }
        }

    def load_language_file(self, lang_code):
        lang_file = os.path.join(BASE_DIR, f"lang_{lang_code}.json")
        if os.path.exists(lang_file):
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception: pass
        return {"btn_browse": "Browse...", "btn_copy": "Copy", "copied": "Copied!"}

    def t(self, key): 
        return self.translations.get(key, key)

    def change_language(self, event=None):
        self.current_lang = self.lang_combo.get()
        self.translations = self.load_language_file(self.current_lang)
        for w in self.root.winfo_children(): w.destroy()
        self.create_widgets()
        self.scan_models_directory()
    def load_user_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.models_dir = data.get("models_dir", self.yaml_data["models_dir"])
                    self.llama_exe_path = data.get("llama_exe_path", self.yaml_data["llama_exe_path"])
                    return data
            except Exception: pass
        self.models_dir = self.yaml_data["models_dir"]
        self.llama_exe_path = self.yaml_data["llama_exe_path"]
        return {"models_dir": self.models_dir, "llama_exe_path": self.llama_exe_path, "models": {}}

    def save_user_config(self):
        self.config["models_dir"], self.config["llama_exe_path"] = self.models_dir, self.llama_exe_path
        with open(CONFIG_FILE, "w", encoding="utf-8") as f: 
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def create_widgets(self):
        top_bar = ttk.Frame(self.root, padding=5)
        top_bar.pack(fill="x", padx=10)
        ttk.Label(top_bar, text="Language / Язык:").pack(side="left", padx=5)
        self.lang_combo = ttk.Combobox(top_bar, values=["ru", "en"], state="readonly", width=5)
        self.lang_combo.set(self.current_lang)
        self.lang_combo.pack(side="left")
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_language)

        for t_key, p, c in [("title_exe", self.llama_exe_path, self.browse_exe_path), ("title_dir", self.models_dir, self.browse_directory)]:
            fr = ttk.LabelFrame(self.root, text=self.t(t_key), padding=10)
            fr.pack(fill="x", padx=10, pady=4)
            lbl = ttk.Label(fr, text=p, font=("Arial", 9, "italic"))
            lbl.pack(side="left", fill="x", expand=True)
            ttk.Button(fr, text=self.t("btn_browse"), command=c).pack(side="right")
            if "exe" in t_key: self.exe_label = lbl
            else: self.dir_label = lbl

        m_fr = ttk.LabelFrame(self.root, text=self.t("title_model"), padding=10)
        m_fr.pack(fill="x", padx=10, pady=4)
        self.model_combo = ttk.Combobox(m_fr, state="readonly")
        self.model_combo.pack(fill="x", expand=True)
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_selected)

        fl_fr = ttk.LabelFrame(self.root, text=self.t("title_flags"), padding=10)
        fl_fr.pack(fill="both", expand=True, padx=10, pady=5)
        self.canvas = tk.Canvas(fl_fr, borderwidth=0, highlightthickness=0)
        sb = ttk.Scrollbar(fl_fr, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.cv_win = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self.cv_win, width=e.width))
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        self.render_flags_inputs()

        cmd_fr = ttk.LabelFrame(self.root, text=self.t("title_preview"), padding=10)
        cmd_fr.pack(fill="x", padx=10, pady=5)
        self.cmd_preview_entry = ttk.Entry(cmd_fr, font=("Consolas", 9))
        self.cmd_preview_entry.pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(cmd_fr, text=self.t("btn_copy"), command=self.copy_command).pack(side="right", padx=2)
        tk.Button(self.root, text=self.t("btn_run"), bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), command=self.launch_server).pack(fill="x", padx=10, pady=10)
    
    def browse_exe_path(self):
        res = filedialog.askopenfilename(initialdir="C:\\", filetypes=[("Executable Files", "*.exe")])
        if res: self.llama_exe_path = os.path.normpath(res); self.exe_label.config(text=self.llama_exe_path); self.save_user_config(); self.update_command_preview()

    def browse_directory(self):
        res = filedialog.askdirectory(initialdir=self.models_dir)
        if res: self.models_dir = os.path.normpath(res); self.dir_label.config(text=self.models_dir); self.scan_models_directory(); self.save_user_config()

    def scan_models_directory(self):
        if not os.path.exists(self.models_dir): self.model_combo["values"] = []; return
        s = [d for d in os.listdir(self.models_dir) if os.path.isdir(os.path.join(self.models_dir, d))]
        self.model_combo["values"] = s
        if s: self.model_combo.current(0); self.on_model_selected()
        else: self.model_combo.set(self.t("no_subdirs"))

    def find_largest_file(self, folder_path):
        try:
            f = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]
            return max(f, key=os.path.getsize) if f else None
        except Exception: return None

    def on_input_changed(self, *args): self.update_command_preview()

    def render_flags_inputs(self):
        for w in self.scrollable_frame.winfo_children(): w.destroy()
        self.widgets_ref = {}
        self.scrollable_frame.columnconfigure(0, weight=1, uniform="group1")
        self.scrollable_frame.columnconfigure(1, weight=1, uniform="group1")
        
        for idx, (fl, inf) in enumerate(self.yaml_data.get("flags", {}).items()):
            cell = ttk.Frame(self.scrollable_frame, padding=5)
            cell.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=10, pady=4)
            top_row = ttk.Frame(cell)
            top_row.pack(fill="x", side="top")
            
            cv = tk.BooleanVar(value=inf["active"])
            cv.trace_add("write", self.on_input_changed)
            ttk.Checkbutton(top_row, variable=cv, text=fl).pack(side="left", anchor="w")
            
            ifr = ttk.Frame(top_row)
            ifr.pack(side="right", fill="x", expand=True, padx=5)
            
            vv = tk.StringVar(value=str(inf["value"]))
            vv.trace_add("write", self.on_input_changed)
            
            if inf["type"] == "combo":
                el = ttk.Combobox(ifr, textvariable=vv, values=inf["options"])
                el.config(state="normal" if fl == "--gpu-layers" else "readonly")
                el.bind("<<ComboboxSelected>>", self.on_input_changed)
            else: el = ttk.Entry(ifr, textvariable=vv)
            el.pack(fill="x", expand=True)
            
            ttk.Label(cell, text=self.t(inf["desc"]), font=("Arial", 8), foreground="#7f8c8d", wraplength=450).pack(side="top", anchor="w", pady=2)
            self.widgets_ref[fl] = {"check_var": cv, "value_var": vv}

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
                self.widgets_ref[fl]["check_var"].set(st[fl]["active"] if fl in st else self.yaml_data["flags"][fl]["active"])
                self.widgets_ref[fl]["value_var"].set(st[fl]["value"] if fl in st else self.yaml_data["flags"][fl]["value"])
                self.widgets_ref[fl]["check_var"].trace_add("write", self.on_input_changed)
                self.widgets_ref[fl]["value_var"].trace_add("write", self.on_input_changed)
        self.update_command_preview()

    def generate_command_list(self, clean_exe=False):
        m = self.model_combo.get()
        if not m or m == self.t("no_subdirs"): return None
        mf = self.find_largest_file(os.path.join(self.models_dir, m))
        if not mf: return None
        cmds = ["llama.exe" if clean_exe else f'"{self.llama_exe_path}"', "serve"]
        for fl in self.yaml_data.get("flags", {}):
            if fl in self.widgets_ref and self.widgets_ref[fl]["check_var"].get():
                cmds.append(fl)
                v = self.widgets_ref[fl]["value_var"].get().strip()
                if v: cmds.append(v)
        cmds.extend(["--model", f'"{mf}"'])
        return cmds

    def update_command_preview(self):
        cmds = self.generate_command_list(clean_exe=True)
        self.cmd_preview_entry.delete(0, tk.END)
        if cmds: self.cmd_preview_entry.insert(0, " ".join(cmds))

    def copy_command(self):
        cmd_text = self.cmd_preview_entry.get()
        if cmd_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(cmd_text)
            messagebox.showinfo("Success", self.t("copied"))

    def launch_server(self):
        m = self.model_combo.get()
        if not m or m == self.t("no_subdirs") or not os.path.exists(self.llama_exe_path):
            messagebox.showerror("Error", self.t("err_validation")); return
        cmds_real = self.generate_command_list(clean_exe=False)
        cmds_clean = self.generate_command_list(clean_exe=True)
        if not cmds_real: messagebox.showerror("Error", self.t("err_no_model")); return
        if "models" not in self.config: self.config["models"] = {}
        self.config["models"][m] = {"flags": {fl: {"active": self.widgets_ref[fl]["check_var"].get(), "value": self.widgets_ref[fl]["value_var"].get()} for fl in self.yaml_data["flags"] if fl in self.widgets_ref}}
        self.save_user_config()
        terminal_cmd = f'start cmd /k "echo =================================================== && echo {" ".join(cmds_clean)} && echo =================================================== && echo. && {" ".join(cmds_real)}"'
        try: subprocess.Popen(terminal_cmd, shell=True)
        except Exception as e: messagebox.showerror("Error", f"Failed to open terminal: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedLlamaLauncher(root)
    root.mainloop()
