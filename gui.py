"""
Графический интерфейс приложения
"""
import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime, timedelta
import threading

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tooltip import ToolTip

from config import (
    BASE_PATH_DEFAULT, SOURCE_FILE, EFIR_BASE, NEWS_EFIR25,
    CODER_SITE, CODER_25, EMAIL_VIDEOSERVER, EMAIL_25REGION,
    EFIR_TIMES, TYPE_STYLES, BUTTON_CONFIGS,
    load_settings, save_settings,
)
from file_utils import (
    prepare_folder_name, extract_date_from_filename,
    extract_file_name_without_prefix_and_date, extract_project_name_from_path,
    get_efir_destination_filename, dest_site2, dest_news_storage,
    dest_archive_stories, is_file_already_copied, find_files_by_date,
    normalize_path,
)


class MediaCopyApp:
    def __init__(self):
        self.root = ttk.Window(
            title="Медиа-менеджер | Создание и копирование",
            themename="litera",
            size=(1250, 850),
            minsize=(1250, 600),
        )
        self.root.place_window_center()

        self.current_view_date = datetime.today()

        # Загружаем сохранённые настройки
        self.settings = load_settings()

        # Переменные — берём из настроек или дефолтные
        self.project_base_var = tk.StringVar(
            value=self.settings.get("project_base", BASE_PATH_DEFAULT)
        )
        self.search_folder_var = tk.StringVar(
            value=self.settings.get("search_folder", BASE_PATH_DEFAULT)
        )
        self.additional_search_var = tk.StringVar(
            value=self.settings.get("additional_search", "")
        )
        self.source_file_var = tk.StringVar(
            value=self.settings.get("source_file", SOURCE_FILE)
        )
        self.project_name_var = tk.StringVar()

        # Автосохранение при изменении любого пути
        self.project_base_var.trace_add("write", self._on_settings_changed)
        self.search_folder_var.trace_add("write", self._on_settings_changed)
        self.additional_search_var.trace_add("write", self._on_settings_changed)
        self.source_file_var.trace_add("write", self._on_settings_changed)

        self._build_ui()
        self._bind_shortcuts()
        self.refresh_file_list()

    # =========================================================
    # СОХРАНЕНИЕ НАСТРОЕК
    # =========================================================
    def _on_settings_changed(self, *args):
        """Автосохранение при изменении любого пути"""
        self.settings = {
            "project_base": self.project_base_var.get(),
            "search_folder": self.search_folder_var.get(),
            "additional_search": self.additional_search_var.get(),
            "source_file": self.source_file_var.get(),
        }
        save_settings(self.settings)

    # =========================================================
    # ПОСТРОЕНИЕ ИНТЕРФЕЙСА
    # =========================================================
    def _build_ui(self):
        self._build_settings_panel()
        ttk.Separator(self.root, orient=HORIZONTAL).pack(fill=X, padx=15, pady=5)
        self._build_create_panel()
        ttk.Separator(self.root, orient=HORIZONTAL).pack(fill=X, padx=15, pady=5)
        self._build_navigation()
        self._build_file_list_area()

    def _build_settings_panel(self):
        """Сворачиваемая панель настроек"""
        self.settings_visible = tk.BooleanVar(value=False)

        toggle_frame = ttk.Frame(self.root)
        toggle_frame.pack(fill=X, padx=15, pady=(10, 0))

        self.toggle_btn = ttk.Button(
            toggle_frame,
            text="⚙  Настройки путей",
            bootstyle="link",
            command=self._toggle_settings,
        )
        self.toggle_btn.pack(anchor=W)

        self.settings_frame = ttk.Frame(self.root)

        paths = [
            ("Папка проекта:", self.project_base_var, "folder"),
            ("Файл-источник (.prproj):", self.source_file_var, "file"),
            ("Папка поиска файлов:", self.search_folder_var, "folder"),
            ("Доп. папка поиска:", self.additional_search_var, "folder"),
        ]

        for i, (label_text, var, browse_type) in enumerate(paths):
            ttk.Label(
                self.settings_frame, text=label_text, font=("Segoe UI", 9)
            ).grid(row=i, column=0, sticky=W, padx=(10, 5), pady=3)

            ttk.Entry(
                self.settings_frame, textvariable=var, width=65, font=("Segoe UI", 9)
            ).grid(row=i, column=1, padx=5, pady=3, sticky=EW)

            cmd = (
                (lambda v=var: self._browse_file(v))
                if browse_type == "file"
                else (lambda v=var: self._browse_folder(v))
            )
            ttk.Button(
                self.settings_frame, text="📂" if browse_type == "folder" else "📄",
                command=cmd, bootstyle="secondary-outline", width=4,
            ).grid(row=i, column=2, padx=5, pady=3)

        self.settings_frame.columnconfigure(1, weight=1)

    def _toggle_settings(self):
        if self.settings_visible.get():
            self.settings_frame.pack_forget()
            self.settings_visible.set(False)
            self.toggle_btn.configure(text="⚙  Настройки путей")
        else:
            self.settings_frame.pack(
                fill=X, padx=15, pady=(0, 5),
                after=self.toggle_btn.master
            )
            self.settings_visible.set(True)
            self.toggle_btn.configure(text="⚙  Скрыть настройки")

    def _build_create_panel(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill=X, padx=15, pady=5)

        ttk.Label(
            frame, text="Название проекта:", font=("Segoe UI", 10, "bold")
        ).pack(anchor=W)

        input_row = ttk.Frame(frame)
        input_row.pack(fill=X, pady=(4, 0))

        self.project_entry = ttk.Entry(
            input_row, textvariable=self.project_name_var, font=("Segoe UI", 11),
        )
        self.project_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

        create_btn = ttk.Button(
            input_row, text="  Создать проект", command=self.create_project,
            bootstyle="danger", width=20,
        )
        create_btn.pack(side=RIGHT)
        ToolTip(create_btn, text="Создать новостной проект с файлами-заглушками")

    def _build_navigation(self):
        nav = ttk.Frame(self.root)
        nav.pack(pady=8)

        ttk.Button(
            nav, text="◀  Назад", command=lambda: self._navigate_days(-1),
            bootstyle="secondary-outline", width=12,
        ).pack(side=LEFT, padx=4)

        self.date_btn = ttk.Button(
            nav, text=self.current_view_date.strftime("%d.%m.%Y"),
            command=self._reset_to_today, bootstyle="info", width=14,
        )
        self.date_btn.pack(side=LEFT, padx=4)
        ToolTip(self.date_btn, text="Нажмите, чтобы вернуться к сегодня")

        ttk.Button(
            nav, text="Вперёд  ▶", command=lambda: self._navigate_days(1),
            bootstyle="secondary-outline", width=12,
        ).pack(side=LEFT, padx=4)

        ttk.Button(
            nav, text="⟳  Обновить", command=self.refresh_file_list,
            bootstyle="success", width=14,
        ).pack(side=LEFT, padx=(15, 4))

    def _build_file_list_area(self):
        self.scroll_frame = ScrolledFrame(self.root, autohide=True, padding=(10, 10, 25, 10))
        self.scroll_frame.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))
        self.file_container = self.scroll_frame

    # =========================================================
    # НАВИГАЦИЯ ПО ДНЯМ
    # =========================================================
    def _navigate_days(self, direction: int):
        self.current_view_date = self._find_nearest_date(
            self.current_view_date, direction
        )
        self.date_btn.configure(text=self.current_view_date.strftime("%d.%m.%Y"))
        self.refresh_file_list()

    def _reset_to_today(self):
        self.current_view_date = datetime.today()
        self.date_btn.configure(text=self.current_view_date.strftime("%d.%m.%Y"))
        self.refresh_file_list()

    def _find_nearest_date(self, base_date, direction):
        check = base_date
        for _ in range(365):
            check += timedelta(days=direction)
            files = find_files_by_date(
                check,
                self.search_folder_var.get().strip(),
                self.additional_search_var.get().strip(),
            )
            if files:
                return check
        return base_date

    # =========================================================
    # ОТОБРАЖЕНИЕ ФАЙЛОВ
    # =========================================================
    def refresh_file_list(self):
        for w in self.file_container.winfo_children():
            w.destroy()

        files = find_files_by_date(
            self.current_view_date,
            self.search_folder_var.get().strip(),
            self.additional_search_var.get().strip(),
        )

        if not files:
            ttk.Label(
                self.file_container,
                text=f"За {self.current_view_date.strftime('%d.%m.%Y')} файлов не найдено",
                font=("Segoe UI", 11), bootstyle="secondary",
            ).pack(anchor=W, pady=20, padx=10)
            return

        by_folder = {}
        for fp in files:
            by_folder.setdefault(os.path.dirname(fp), []).append(fp)

        def safe_ctime(p):
            try:
                return os.path.getctime(p)
            except OSError:
                return 0

        for folder in sorted(by_folder, key=safe_ctime, reverse=True):
            self._render_folder_card(folder, by_folder[folder])

    def _render_folder_card(self, folder: str, file_paths: list):
        project_name = extract_project_name_from_path(folder)
        project_name_clean = re.sub(r'^\d{2}_\d{2}_', '', project_name)

        card = ttk.Labelframe(
            self.file_container, text=f"  {project_name_clean}  ",
            bootstyle="primary", padding=10,
        )
        card.pack(fill=X, padx=5, pady=6)

        groups = {"ПАНОРАМА": [], "ДАЙДЖЕСТ": [], "НОВОСТИ": [], "АРХИВ": []}
        for fp in sorted(file_paths):
            fname = os.path.basename(fp)
            if fname.startswith("ПАНОРАМА_ДАЙДЖЕСТ"):
                groups["ДАЙДЖЕСТ"].append(fp)
            elif fname.startswith("ПАНОРАМА"):
                groups["ПАНОРАМА"].append(fp)
            elif fname.startswith("НОВОСТИ"):
                groups["НОВОСТИ"].append(fp)
            elif re.match(r"^\d{2}_\d{2}_", fname):
                groups["АРХИВ"].append(fp)

        for file_type, paths in groups.items():
            for fpath in paths:
                self._render_file_row(card, fpath, file_type)

    def _render_file_row(self, parent, fpath: str, file_type: str):
        fname = os.path.basename(fpath)
        clean_name = extract_file_name_without_prefix_and_date(fname)
        mm, dd = extract_date_from_filename(fname)
        year = self.current_view_date.strftime("%Y")

        row = ttk.Frame(parent)
        row.pack(fill=X, pady=3)

        # Бейдж типа
        type_cfg = TYPE_STYLES.get(file_type, {"color": "#666", "bootstyle": "secondary"})
        ttk.Label(
            row, text=f" {file_type} ", font=("Segoe UI", 9, "bold"),
            foreground="white", background=type_cfg["color"],
            width=12, anchor=CENTER,
        ).pack(side=LEFT, padx=(0, 10))

        # Имя файла
        ttk.Label(
            row, text=clean_name, font=("Segoe UI", 9), anchor=W
        ).pack(side=LEFT, fill=X, expand=True, padx=(0, 8))

        if not mm or not dd:
            return

        # Блок кнопок справа
        btn_frame = ttk.Frame(row)
        btn_frame.pack(side=RIGHT)

        # Внутри btn_frame: галочка + кнопки
        inner = ttk.Frame(btn_frame)
        inner.pack(side=RIGHT)

        # Галочка
        primary_dest = self._get_primary_dest(fpath, fname, file_type, year, mm, dd)
        if primary_dest and os.path.exists(primary_dest) and is_file_already_copied(fpath, primary_dest):
            ttk.Label(
                btn_frame, text="✓", foreground="#43A047", font=("Segoe UI", 12, "bold")
            ).pack(side=LEFT, padx=(0, 4))

        # Кнопки
        self._render_action_buttons(btn_frame, fpath, fname, file_type, year, mm, dd)

    def _get_primary_dest(self, fpath, fname, file_type, year, mm, dd):
        if file_type in ("ПАНОРАМА", "ДАЙДЖЕСТ"):
            return os.path.join(dest_site2(year, mm, dd), fname)
        elif file_type == "НОВОСТИ":
            return os.path.join(dest_news_storage(year, mm), fname)
        elif file_type == "АРХИВ":
            return os.path.join(dest_archive_stories(year, mm), fname)
        return None

    def _render_action_buttons(self, parent, fpath, fname, file_type, year, mm, dd):
        if file_type in ("ПАНОРАМА", "ДАЙДЖЕСТ"):
            dst = dest_site2(year, mm, dd)
            if os.path.isdir(dst):
                self._action_btn(parent, "В Панораму",
                    lambda s=fpath, d=dst, f=fname: self._copy(s, os.path.join(d, f)))
            else:
                ttk.Label(parent, text="Нет пути", foreground="red",
                    font=("Segoe UI", 8)).pack(side=LEFT, padx=4)

            if os.path.isdir(EFIR_BASE):
                self._action_btn(parent, "В Эфир",
                    lambda s=fpath, ft=file_type: self._show_efir_selection(s, ft))

            if os.path.isdir(CODER_SITE):
                self._action_btn(parent, "Кодер Сайт",
                    lambda s=fpath, f=fname: self._copy(s, os.path.join(CODER_SITE, f)))

        elif file_type == "НОВОСТИ":
            dst_s = dest_news_storage(year, mm)
            if os.path.isdir(dst_s):
                self._action_btn(parent, "Хранение",
                    lambda s=fpath, d=dst_s, f=fname:
                    self._copy(s, os.path.join(d, f), copy_clip=True))
            if os.path.isdir(NEWS_EFIR25):
                self._action_btn(parent, "В Эфир 25",
                    lambda s=fpath, f=fname:
                    self._copy(s, os.path.join(NEWS_EFIR25, f), copy_clip=True))
            if os.path.isdir(CODER_25):
                self._action_btn(parent, "Кодер 25",
                    lambda s=fpath, f=fname:
                    self._copy(s, os.path.join(CODER_25, f), copy_clip=True))

        elif file_type == "АРХИВ":
            dst_a = dest_archive_stories(year, mm)
            if os.path.isdir(dst_a):
                self._action_btn(parent, "В Архив",
                    lambda s=fpath, d=dst_a, f=fname:
                    self._copy(s, os.path.join(d, f)))

    def _action_btn(self, parent, text: str, command):
        cfg = BUTTON_CONFIGS.get(text, {"bootstyle": "secondary-outline"})
        ttk.Button(
            parent, text=text, command=command,
            bootstyle=cfg["bootstyle"], width=11,
        ).pack(side=LEFT, padx=2)

    # =========================================================
    # КОПИРОВАНИЕ
    # =========================================================
    def _copy(self, src, dest, copy_clip=False):
        if not os.path.exists(src):
            messagebox.showerror("Ошибка", f"Файл не найден:\n{src}")
            return
    
        dest_dir = os.path.dirname(dest)
        if not os.path.isdir(dest_dir):
            messagebox.showerror("Ошибка", f"Папка не найдена:\n{dest_dir}")
            return
    
        if os.path.exists(dest):
            if is_file_already_copied(src, dest):
                if copy_clip:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(dest)
                    self.root.update()
                    messagebox.showinfo("Информация", f"Файл уже скопирован.\nПуть скопирован в буфер:\n{dest}")
                else:
                    messagebox.showinfo("Информация", f"Файл уже скопирован:\n{dest}")
                return
            if not messagebox.askyesno("Перезапись", f"Перезаписать?\n{dest}"):
                return
    
        progress_win = ttk.Toplevel(self.root)
        progress_win.title("Копирование")
        progress_win.geometry("420x120")
        progress_win.transient(self.root)
        progress_win.grab_set()
        progress_win.place_window_center()
    
        ttk.Label(
            progress_win, text=os.path.basename(src), font=("Segoe UI", 10, "bold"),
        ).pack(pady=(15, 5))
    
        bar = ttk.Progressbar(progress_win, mode="indeterminate", bootstyle="info-striped")
        bar.pack(fill=X, padx=30, pady=5)
        bar.start(12)
    
        ttk.Label(progress_win, text="Копирование…", font=("Segoe UI", 9)).pack()
    
        def _worker():
            try:
                shutil.copy2(src, dest)
    
                def _done():
                    progress_win.destroy()
                    if copy_clip:
                        self.root.clipboard_clear()
                        self.root.clipboard_append(dest)
                        self.root.update()
                        messagebox.showinfo("Готово", f"Путь в буфере:\n{dest}")
                    else:
                        messagebox.showinfo("Готово", f"Скопировано:\n{dest}")
                    self.refresh_file_list()
    
                self.root.after(0, _done)
    
            except Exception as e:
                self.root.after(0, lambda: progress_win.destroy())
                self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
    
        threading.Thread(target=_worker, daemon=True).start()


    # =========================================================
    # ВЫБОР ВРЕМЕНИ ЭФИРА
    # =========================================================
    def _show_efir_selection(self, src_path, file_type):
        if file_type not in EFIR_TIMES:
            return

        win = ttk.Toplevel(self.root)
        win.title(f"Время эфира — {file_type}")
        win.geometry("280x220")
        win.transient(self.root)
        win.grab_set()
        win.place_window_center()

        ttk.Label(
            win, text="Выберите время:", font=("Segoe UI", 11, "bold")
        ).pack(pady=(15, 10))

        for t in EFIR_TIMES[file_type]:
            ttk.Button(
                win, text=f"{t}:00", bootstyle="info-outline", width=10,
                command=lambda et=t: self._copy_efir(src_path, file_type, et, win),
            ).pack(pady=4)

        ttk.Button(
            win, text="Отмена", bootstyle="secondary", command=win.destroy
        ).pack(pady=(10, 0))

    def _copy_efir(self, src_path, file_type, efir_time, win):
        win.destroy()
        src_fn = os.path.basename(src_path)
        dest_fn = get_efir_destination_filename(src_fn, efir_time, file_type)
        dest = os.path.join(EFIR_BASE, dest_fn)
        self._copy(src_path, dest)

    # =========================================================
    # СОЗДАНИЕ ПРОЕКТА
    # =========================================================
    def create_project(self):
        base = normalize_path(self.project_base_var.get().strip() or BASE_PATH_DEFAULT)
        source = normalize_path(self.source_file_var.get().strip() or SOURCE_FILE)
        text = self.project_name_var.get().strip()

        if not text:
            messagebox.showerror("Ошибка", "Введите название проекта.")
            return

        today = datetime.today()
        date_folder = today.strftime("%d.%m.%Y")

        folder_name_text = prepare_folder_name(text, for_files=False).rstrip('_')
        folder_name = today.strftime("%m_%d_") + folder_name_text
        full_path = os.path.join(base, date_folder, folder_name)
        os.makedirs(full_path, exist_ok=True)

        try:
            shutil.copy2(source, os.path.join(full_path, f"{folder_name}.prproj"))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать проект:\n{e}")
            return

        files_name_text = prepare_folder_name(text, for_files=True)
        files_name = today.strftime("%m_%d_") + files_name_text
        news_date = today.strftime('%m%d')

        stub_files = [
            f"ПАНОРАМА_18_{files_name}.mp4",
            f"ПАНОРАМА_ДАЙДЖЕСТ_00_{files_name}.mp4",
            f"{files_name}.mp4",
            f"НОВОСТИ_{news_date}_{files_name_text}.mp4",
        ]

        try:
            for f in stub_files:
                with open(os.path.join(full_path, f), 'a'):
                    pass
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать файлы:\n{e}")
            return

        messagebox.showinfo("Готово", f"Проект создан:\n{full_path}")
        self.refresh_file_list()

    # =========================================================
    # ОБЗОР ПАПОК/ФАЙЛОВ
    # =========================================================
    def _browse_folder(self, var):
        folder = filedialog.askdirectory()
        if folder:
            var.set(normalize_path(folder))
            self.refresh_file_list()

    def _browse_file(self, var):
        path = filedialog.askopenfilename(
            filetypes=[("Premiere Project", "*.prproj")]
        )
        if path:
            var.set(normalize_path(path))

    # =========================================================
    # ГОРЯЧИЕ КЛАВИШИ
    # =========================================================
    def _bind_shortcuts(self):
        def handle_ctrl(event):
            widget = self.root.focus_get()
            if not isinstance(widget, (tk.Entry, ttk.Entry)):
                return
            if event.keycode == 86:  # Ctrl+V
                try:
                    clip = self.root.clipboard_get()
                    if widget.selection_present():
                        s = widget.index(tk.SEL_FIRST)
                        e = widget.index(tk.SEL_LAST)
                        widget.delete(s, e)
                        widget.insert(s, clip)
                    else:
                        widget.insert(tk.INSERT, clip)
                    return "break"
                except Exception:
                    pass
            elif event.keycode == 65:  # Ctrl+A
                widget.select_range(0, tk.END)
                return "break"

        self.root.bind_all('<Control-KeyPress>', handle_ctrl)

    # =========================================================
    # ЗАПУСК
    # =========================================================
    def run(self):
        self.root.mainloop()
