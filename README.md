# Llama.exe Serve Launcher 🦙

A lightweight, simple GUI tool built with Python and Tkinter to help you manage and launch the local `llama.exe serve` command from **llama.cpp** on Windows. 

Instead of typing long console commands manually every time, this tool lets you toggle flags with checkboxes, save settings per model, and see the exact command line before running it.

---

## Features

* **Lightweight & Simple**: No heavy frameworks, no bloated UI. Just clean Tkinter fields arranged in two columns.
* **Smart Model Detection**: Scans your specified root directory, lists subfolders, and automatically selects the largest file (the `.gguf` weights) inside the selected folder.
* **Per-Model Presets**: Saves changes on the fly to `launcher_config.json` whenever you click "RUN". When you select a model again, its unique flag setup is automatically restored.
* **Flexible Flag Toggle**: Every flag has a checkbox. Active checkboxes include the flag in the startup command, inactive ones completely remove it.
* **Dynamic Preview**: The command line updates in real-time as you tweak values or change checkboxes. The file path is shortened to just `llama.exe` for cleaner preview.
* **Clean Terminal Output**: Opens a standard Windows command prompt (`cmd`) for the actual server, and echoes the exact clean command at the top of the terminal before displaying server logs.
* **Localization Support**: Easily switch languages on the fly. All UI texts and tooltips are stored separately in JSON files.

---

## Repository Contents

* `llama_launcher.py` — The core Python source code.
* `app_config.yaml` — Global configuration file containing default paths, flags, field types, and descriptions.
* `lang_ru.json` — Russian language pack and tooltips.
* `lang_en.json` — English language pack and tooltips.
* `llama_launcher_win.zip` — A pre-compiled portable archive containing `llama_launcher.exe` and default config files. You can unpack this anywhere and use it instantly without installing Python or compiling anything.

---

## How to Use the Pre-compiled Version

If you don't want to install Python and configure dependencies, you can use the ready-to-run `.exe` build:

1. Download **`llama_launcher_win.zip`** from this repository.
2. Unpack the contents of the ZIP archive into any convenient directory on your PC.
3. Open `app_config.yaml` in a text editor to set your default paths for `llama.exe` and your model folder (or change them later directly through the GUI).
4. Run `llama_launcher.exe`.

---

## How to Run from Source Code

If you prefer to run or modify the original script:

1. Install the required YAML dependency:
   ```bash
   pip install pyyaml
   ```
2. Make sure `llama_launcher.py`, `app_config.yaml`, and the `lang_*.json` files are all placed in the same folder.
3. Run the script:
   ```bash
   python llama_launcher.py
   ```

To compile it yourself into a single executable, you can use PyInstaller:
```bash
pip install pyinstaller
python -m PyInstaller --clean --noconsole --onefile llama_launcher.py
```
for compile without creating temp directory after launch .exe file use that:
```bash
python -m PyInstaller --clean --noconsole --onedir llama_launcher.py
```
*(Remember to copy `app_config.yaml` and the language files into the `dist` folder next to your newly created `.exe` file).*

---

## Environment Requirements

* **OS**: Windows 10 / 11
* **Language**: Python 3.10+ (only required if running from the source `.py` script)
* **Dependencies**: `PyYAML` (standard `tkinter` library is used for the GUI)

---

## License

This project is open-source and available under the [MIT License](LICENSE). Feel free to submit an issue or a pull request if you want to expand the default flag list or improve the layout!
