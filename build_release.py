import os
import shutil
import zipfile
import subprocess

def run_build():
    # Названия файлов
    script_name = "llama_launcher.py"
    exe_name = "llama_launcher.exe"
    zip_name = "llama_launcher_win.zip"

    # Файлы зависимостей конфигурации и локализации
    assets = ["app_config.yaml", "lang_en.json", "lang_ru.json"]

    # Определяем пути относительно текущего скрипта
    root_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(root_dir, "dist")
    final_zip_root_path = os.path.join(root_dir, zip_name)

    print("=== [1/4] Запуск компиляции PyInstaller ===")
    build_cmd = ["python", "-m", "PyInstaller", "--clean", "--noconsole", "--onefile", script_name]

    try:
        subprocess.run(build_cmd, check=True)
        print("Компиляция успешно завершена.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка компиляции PyInstaller: {e}")
        return
    except FileNotFoundError:
        print("Ошибка: Команда 'python' или библиотека PyInstaller не найдены в системе.")
        return

    print("\n=== [2/4] Копирование конфигурационных файлов в dist ===")
    for asset in assets:
        src = os.path.join(root_dir, asset)
        dst = os.path.join(dist_dir, asset)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Скопирован: {asset} -> dist/")
        else:
            print(f"Предупреждение: Файл {asset} не найден в корне, пропуск.")

    print("\n=== [3/4] Создание ZIP архива в директории dist ===")
    dist_zip_path = os.path.join(dist_dir, zip_name)
    files_to_pack = [exe_name] + assets

    try:
        with zipfile.ZipFile(dist_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files_to_pack:
                file_path = os.path.join(dist_dir, file)
                if os.path.exists(file_path):
                    # Записываем файл в корень архива без вложенных папок dist/
                    zipf.write(file_path, arcname=file)
                    print(f"Добавлен в архив: {file}")
                else:
                    print(f"Ошибка: Файл {file_path} отсутствует, архив может быть неполным.")
        print(f"Архив успешно создан: dist/{zip_name}")
    except Exception as e:
        print(f"Не удалось создать архив: {e}")
        return

    print("\n=== [4/4] Перемещение готового архива в корень проекта ===")
    try:
        # Если старый архив в корне существует, удаляем его перед заменой
        if os.path.exists(final_zip_root_path):
            os.remove(final_zip_root_path)
            print("Старый архив в корне удален.")

        # Вырезаем (перемещаем) созданный zip из dist в корень
        shutil.move(dist_zip_path, final_zip_root_path)
        print(f"Готово! Релизный архив перемещен в корень: {final_zip_root_path}")
    except Exception as e:
        print(f"Ошибка при перемещении архива: {e}")

if __name__ == "__main__":
    run_build()