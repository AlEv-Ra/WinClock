import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import pytz
import time
import copy
from config import LANGUAGES, LANGUAGE_FLAGS, DEFAULT_FONT, DEFAULT_LANGUAGE

class ToolTip:
    def __init__(self, widget, text):
        # Инициализация всплывающей подсказки
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        # Отображение всплывающей подсказки
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left", bg="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 8))
        label.pack()

    def hide_tip(self, event=None):
        # Скрытие всплывающей подсказки
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class SettingsWindow:
    def __init__(self, parent, gear_label, cfg, l10n, update_callback, exit_callback=None):
        # Инициализация окна настроек
        self.parent = parent
        self.gear_label = gear_label
        self.cfg = copy.deepcopy(cfg)
        self.l10n = l10n
        self.update_callback = update_callback
        self.exit_callback = exit_callback
        self.clocks = self.cfg.setdefault("clocks", [])
        self.selected_index = tk.IntVar(value=0 if self.clocks else -1)

        self.win = tk.Toplevel(self.parent)
        self.win.title(self.l10n.get("settings_title", "Настройки"))
        self.win.configure(bg='white')
        self.position_window()
        self.win.transient(self.parent)
        self.win.grab_set()
        self.win.protocol("WM_DELETE_WINDOW", self.on_close)

        self.create_widgets()
        self.load_selected()

    def position_window(self):
        # Позиционирование окна настроек
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        form_width = 550
        form_height = 650
        try:
            # Использование сохранённой геометрии
            geom = self.cfg.get("settings_window", "550x650+100+100")
            parts = geom.replace("x", "+").split("+")
            width, height, pos_x, pos_y = map(int, parts)
            # Проверка, что позиция в пределах экрана
            if (0 <= pos_x < screen_width - 50 and 0 <= pos_y < screen_height - 50 and
                width > 0 and height > 0):
                self.win.geometry(geom)
                return
        except:
            pass
        # Если сохранённая геометрия недоступна, позиционируем рядом с шестерёнкой
        try:
            gear_x = self.gear_label.winfo_rootx()
            gear_y = self.gear_label.winfo_rooty()
            gear_height = self.gear_label.winfo_height()
            positions = [
                (gear_x - form_width - 10, gear_y - form_height // 2),
                (gear_x - form_width - 10, gear_y + gear_height // 2),
                (gear_x + 10, gear_y - form_height // 2),
                (gear_x + 10, gear_y + gear_height // 2)
            ]
            best_position = None
            max_visible_area = 0
            for pos_x, pos_y in positions:
                if pos_x < 0:
                    pos_x = 0
                if pos_y < 0:
                    pos_y = 0
                if pos_x + form_width > screen_width:
                    pos_x = screen_width - form_width
                if pos_y + form_height > screen_height:
                    pos_y = screen_height - form_height
                visible_width = min(pos_x + form_width, screen_width) - max(pos_x, 0)
                visible_height = min(pos_y + form_height, screen_height) - max(pos_y, 0)
                visible_area = visible_width * visible_height
                if visible_area > max_visible_area:
                    max_visible_area = visible_area
                    best_position = (pos_x, pos_y)
            if best_position:
                self.win.geometry(f"550x650+{best_position[0]}+{best_position[1]}")
            else:
                self.win.geometry("550x650+100+100")
        except:
            self.win.geometry("550x650+100+100")

    def on_close(self):
        # Проверка и сохранение настроек перед закрытием
        for c in self.clocks:
            # Проверка размеров шрифта
            try:
                font_size = int(c.get("font_size", 36))
                if font_size < 8:
                    raise ValueError
                c["font_size"] = font_size
            except (ValueError, TypeError):
                c["font_size"] = 36
                if self.selected_index.get() < len(self.clocks) and self.clocks[self.selected_index.get()] is c:
                    self.sel_size.delete(0, "end")
                    self.sel_size.insert(0, "36")
            try:
                title_font_size = int(c.get("title_font_size", 12))
                if title_font_size < 8:
                    raise ValueError
                c["title_font_size"] = title_font_size
            except (ValueError, TypeError):
                c["title_font_size"] = 12
                if self.selected_index.get() < len(self.clocks) and self.clocks[self.selected_index.get()] is c:
                    self.sel_title_size.delete(0, "end")
                    self.sel_title_size.insert(0, "12")
            try:
                date_font_size = int(c.get("date_font_size", 12))
                if date_font_size < 8:
                    raise ValueError
                c["date_font_size"] = date_font_size
            except (ValueError, TypeError):
                c["date_font_size"] = 12
                if self.selected_index.get() < len(self.clocks) and self.clocks[self.selected_index.get()] is c:
                    self.sel_date_size.delete(0, "end")
                    self.sel_date_size.insert(0, "12")
            # Проверка формата даты
            date_format = c.get("date_format", "dd-MM-yyyy")
            if date_format.strip():
                if not any(token in date_format for token in ["w", "W", "dd", "MM", "yyyy", "yy"]):
                    c["date_format"] = "dd-MM-yyyy"
                    if self.selected_index.get() < len(self.clocks) and self.clocks[self.selected_index.get()] is c:
                        self.sel_date_format.delete(0, "end")
                        self.sel_date_format.insert(0, "dd-MM-yyyy")
            else:
                c["date_format"] = ""
            # Проверка формата времени
            time_format = c.get("time_format", "HH:mm:ss")
            if time_format.strip():
                if not any(token in time_format for token in ["H", "HH", "h", "hh", "m", "mm", "s", "ss", "p"]):
                    c["time_format"] = "HH:mm:ss"
                    if self.selected_index.get() < len(self.clocks) and self.clocks[self.selected_index.get()] is c:
                        self.sel_time_format.delete(0, "end")
                        self.sel_time_format.insert(0, "HH:mm:ss")
            else:
                c["time_format"] = "HH:mm:ss"

        self.cfg["clocks"] = self.clocks
        self.cfg["settings_window"] = self.win.geometry()
        self.update_callback(self.cfg)
        self.win.destroy()

    def exit_program(self):
        # Закрытие программы с подтверждением
        if messagebox.askyesno(self.l10n.get("settings_title", "Настройки"), self.l10n.get("confirm_exit", "Вы действительно хотите закрыть программу?"), parent=self.win):
            if self.exit_callback:
                self.exit_callback()
            self.win.destroy()

    def create_widgets(self):
        # Создание элементов интерфейса окна настроек
        canvas = tk.Canvas(self.win, bg='white')
        scrollbar = ttk.Scrollbar(self.win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        main_frame = tk.Frame(scrollable_frame, bg='white')
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)

        top_frame = tk.Frame(scrollable_frame, bg='white')
        top_frame.pack(fill="x", padx=8, pady=(8, 0), before=main_frame)
        self.title_label = tk.Label(top_frame, text=self.l10n.get("settings_title", "Настройки"), bg='white', font=("Arial", 12, "bold"))
        self.title_label.pack(side="left", expand=True)
        self.language_var = tk.StringVar(value=LANGUAGE_FLAGS.get(self.cfg.get("language", "ru"), "🇷🇺 Русский"))
        self.language_menu = ttk.Combobox(top_frame, textvariable=self.language_var, values=list(LANGUAGE_FLAGS.values()), state="readonly")
        self.language_menu.pack(side="right", padx=(0, 5))
        self.language_menu.bind("<<ComboboxSelected>>", self.update_language)

        left = tk.Frame(main_frame, bg='white')
        left.pack(side="left", fill="y", padx=(0, 8))

        def add_clock():
            # Добавление новых часов
            base_name = "Часы"
            existing_names = [c.get("title", "") for c in self.clocks]
            index = 1
            title = base_name
            while title in existing_names:
                title = f"{base_name} {index}"
                index += 1
            new_clock = {
                "title": title,
                "font": "Arial",
                "font_size": 36,
                "title_font_size": 12,
                "date_font_size": 12,
                "color": "#FFFFFF",
                "timezone": time.tzname[0] or "Europe/Moscow",
                "time_format": "HH:mm:ss",
                "date_format": "dd-MM-yyyy"
            }
            self.clocks.append(new_clock)
            self.cfg["clocks"] = self.clocks
            self.lb.insert("end", new_clock["title"])
            self.lb.selection_clear(0, tk.END)
            self.lb.select_set(len(self.clocks) - 1)
            self.selected_index.set(len(self.clocks) - 1)
            self.load_selected()

        def remove_clock():
            # Удаление выбранных часов
            if len(self.clocks) <= 1:
                messagebox.showwarning(self.l10n.get("settings_title", "Настройки"), "Нельзя удалить последние часы!", parent=self.win)
                return
            if self.selected_index.get() >= 0 and messagebox.askyesno(self.l10n.get("settings_title", "Настройки"), self.l10n.get("confirm_remove", "Удалить выбранные часы?"), parent=self.win):
                self.clocks.pop(self.selected_index.get())
                self.cfg["clocks"] = self.clocks
                self.lb.delete(self.selected_index.get())
                if self.clocks:
                    new_index = min(self.selected_index.get(), len(self.clocks) - 1)
                    self.lb.select_set(new_index)
                    self.selected_index.set(new_index)
                else:
                    self.selected_index.set(-1)
                self.load_selected()

        def move_clock(up):
            # Перемещение часов вверх или вниз
            i = self.selected_index.get()
            if i < 0 or not self.clocks:
                return
            if up:
                new_index = max(0, i - 1)
            else:
                new_index = min(len(self.clocks) - 1, i + 1)
            if new_index != i:
                self.clocks[i], self.clocks[new_index] = self.clocks[new_index], self.clocks[i]
                self.cfg["clocks"] = self.clocks
                self.lb.delete(0, tk.END)
                for c in self.clocks:
                    self.lb.insert("end", c.get('title', "Без названия"))
                self.lb.select_set(new_index)
                self.selected_index.set(new_index)
                self.load_selected()

        btn_click_frame = tk.Frame(left, bg='white', bd=2, relief="groove")
        btn_click_frame.pack(fill="x", padx=5, pady=5)
        btn_add = tk.Button(btn_click_frame, text="➕", command=add_clock, width=5, font=("Arial", 12), fg="green")
        btn_add.pack(side="left", padx=(5, 2), pady=5, ipadx=2, ipady=2)
        ToolTip(btn_add, self.l10n.get("tooltip_add", "Добавить новые часы"))
        btn_rem = tk.Button(btn_click_frame, text="➖", command=remove_clock, width=5, font=("Arial", 12), fg="red")
        btn_rem.pack(side="left", padx=(2, 2), pady=5, ipadx=2, ipady=2)
        ToolTip(btn_rem, self.l10n.get("tooltip_remove", "Удалить выбранные часы"))
        btn_up = tk.Button(btn_click_frame, text="⬆", command=lambda: move_clock(True), width=5, font=("Arial", 12), fg="blue")
        btn_up.pack(side="left", padx=(2, 2), pady=5, ipadx=2, ipady=2)
        ToolTip(btn_up, self.l10n.get("tooltip_move_up", "Переместить часы вверх"))
        btn_down = tk.Button(btn_click_frame, text="⬇", command=lambda: move_clock(False), width=5, font=("Arial", 12), fg="blue")
        btn_down.pack(side="left", padx=(2, 5), pady=5, ipadx=2, ipady=2)
        ToolTip(btn_down, self.l10n.get("tooltip_move_down", "Переместить часы вниз"))

        self.lb = tk.Listbox(left, width=25, height=10, exportselection=False)
        self.lb.pack(fill="both", expand=True, pady=(5, 0))
        for c in self.clocks:
            self.lb.insert("end", c.get('title', "Без названия"))
        if self.clocks:
            self.lb.select_set(0)
            self.selected_index.set(0)

        right = tk.Frame(main_frame, bg='white')
        right.pack(side="right", fill="both", expand=True)
        clock_settings_frame = tk.Frame(right, bg='white', bd=2, relief="ridge", highlightbackground="#d9d9d9", highlightcolor="#d9d9d9", highlightthickness=2)
        clock_settings_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.lbl_sel = tk.Label(clock_settings_frame, text=self.l10n.get("selected_clock", "Настройки выбранных часов:"), bg='white', font=("Arial", 10, "bold"))
        self.lbl_sel.pack(anchor="w", padx=5, pady=(5, 2))
        self.title_label = tk.Label(clock_settings_frame, text=self.l10n.get("title", "Заголовок:"), bg='white')
        self.title_label.pack(anchor="w", padx=5, pady=(6, 0))
        self.sel_title = tk.Entry(clock_settings_frame)
        self.sel_title.pack(fill="x", padx=5)
        self.sel_title.bind("<KeyRelease>", lambda e: self.save_changes())
        self.timezone_label = tk.Label(clock_settings_frame, text=self.l10n.get("timezone", "Часовой пояс:"), bg='white')
        self.timezone_label.pack(anchor="w", padx=5, pady=(6, 0))
        self.sel_timezone = ttk.Combobox(clock_settings_frame, values=sorted(pytz.all_timezones))
        self.sel_timezone.pack(fill="x", padx=5)
        self.sel_timezone.bind("<<ComboboxSelected>>", lambda e: self.save_changes())
        self.date_format_label = tk.Label(clock_settings_frame, text=self.l10n.get("date_format", "Формат даты"), bg='white')
        self.date_format_label.pack(anchor="w", padx=5, pady=(6, 0))
        self.sel_date_format = tk.Entry(clock_settings_frame)
        self.sel_date_format.pack(fill="x", padx=5)
        self.sel_date_format.bind("<KeyRelease>", lambda e: self.save_changes())
        ToolTip(self.sel_date_format, self.l10n.get("tooltip_date_format", "dd - день, MM - месяц, yyyy - год (4 цифры), yy - год (2 цифры), w - короткое название дня, W - полное название дня"))
        self.time_format_label = tk.Label(clock_settings_frame, text=self.l10n.get("time_format", "Формат времени"), bg='white')
        self.time_format_label.pack(anchor="w", padx=5, pady=(6, 0))
        self.sel_time_format = tk.Entry(clock_settings_frame)
        self.sel_time_format.pack(fill="x", padx=5)
        self.sel_time_format.bind("<KeyRelease>", lambda e: self.save_changes())
        ToolTip(self.sel_time_format, self.l10n.get("tooltip_time_format", "HH:mm:ss - 24-часовой, hh:mm:ss p - 12-часовой с AM/PM"))
        self.font_label = tk.Label(clock_settings_frame, text=self.l10n.get("font", "Шрифт (название):"), bg='white')
        self.font_label.pack(anchor="w", padx=5, pady=(6, 0))
        self.font_entry = tk.Entry(clock_settings_frame)
        self.font_entry.pack(fill="x", padx=5)
        self.font_entry.bind("<KeyRelease>", lambda e: self.save_changes())
        self.font_size_label = tk.Label(clock_settings_frame, text=self.l10n.get("font_size", "Размер шрифта:"), bg='white')
        self.font_size_label.pack(anchor="w", padx=5, pady=(6, 0))
        self.sel_size = tk.Spinbox(clock_settings_frame, from_=8, to=200)
        self.sel_size.pack(fill="x", padx=5)
        self.sel_size.bind("<KeyRelease>", lambda e: self.save_changes())
        self.sel_size.bind("<ButtonRelease-1>", lambda e: self.save_changes())
        self.title_font_size_label = tk.Label(clock_settings_frame, text=self.l10n.get("title_font_size", "Размер шрифта заголовка:"), bg='white')
        self.title_font_size_label.pack(anchor="w", padx=5, pady=(6, 0))
        self.sel_title_size = tk.Spinbox(clock_settings_frame, from_=8, to=200)
        self.sel_title_size.pack(fill="x", padx=5)
        self.sel_title_size.bind("<KeyRelease>", lambda e: self.save_changes())
        self.sel_title_size.bind("<ButtonRelease-1>", lambda e: self.save_changes())
        self.date_font_size_label = tk.Label(clock_settings_frame, text=self.l10n.get("date_font_size", "Размер шрифта даты:"), bg='white')
        self.date_font_size_label.pack(anchor="w", padx=5, pady=(6, 0))
        self.sel_date_size = tk.Spinbox(clock_settings_frame, from_=8, to=200)
        self.sel_date_size.pack(fill="x", padx=5)
        self.sel_date_size.bind("<KeyRelease>", lambda e: self.save_changes())
        self.sel_date_size.bind("<ButtonRelease-1>", lambda e: self.save_changes())
        self.color_label = tk.Label(clock_settings_frame, text=self.l10n.get("color", "Цвет:"), bg='white')
        self.color_label.pack(anchor="w", padx=5, pady=(6, 0))
        self.color_btn = tk.Button(clock_settings_frame, text="", command=self.choose_color, relief="flat")
        self.color_btn.pack(fill="x", padx=5, pady=(0, 5))
        self.reset_btn = tk.Button(clock_settings_frame, text=self.l10n.get("reset_default", "Сбросить на умолчанию"), command=self.reset_to_default, relief="flat")
        self.reset_btn.pack(fill="x", padx=5, pady=5)
        exit_frame = tk.Frame(scrollable_frame, bg='white')
        exit_frame.pack(fill="x", padx=8, pady=(0, 8))
        self.exit_btn = tk.Button(exit_frame, text=self.l10n.get("exit", "Закрыть программу"), command=self.exit_program)
        self.exit_btn.pack(anchor="e")
        self.lb.bind("<<ListboxSelect>>", self.on_listbox_select)

    def on_listbox_select(self, event):
        # Выбор часов из списка
        if self.lb.curselection():
            self.selected_index.set(self.lb.curselection()[0])
        else:
            self.selected_index.set(-1)
        self.load_selected()

    def reset_to_default(self):
        # Сброс настроек текущих часов на значения по умолчанию
        i = self.selected_index.get()
        if i < 0 or i >= len(self.clocks):
            return
        c = self.clocks[i]
        c["font"] = "Arial"
        c["font_size"] = 36
        c["title_font_size"] = 12
        c["date_font_size"] = 12
        c["color"] = "#FFFFFF"
        c["date_format"] = "dd-MM-yyyy"
        c["time_format"] = "HH:mm:ss"
        self.cfg["clocks"] = self.clocks
        self.load_selected()

    def choose_color(self):
        # Выбор цвета для часов
        c = colorchooser.askcolor(parent=self.win)
        if c and c[1]:
            self.color_btn.config(bg=c[1], activebackground=c[1])
            self.save_changes()

    def update_language(self, event=None):
        # Обновление языка интерфейса
        selected_flag = self.language_var.get()
        for lang, flag in LANGUAGE_FLAGS.items():
            if flag == selected_flag:
                self.cfg["language"] = lang
                break
        self.l10n = LANGUAGES.get(self.cfg["language"], LANGUAGES["en"])
        self.update_ui_texts()

    def update_ui_texts(self):
        # Обновление текстов интерфейса на основе выбранного языка
        self.win.title(self.l10n.get("settings_title", "Настройки"))
        self.title_label.config(text=self.l10n.get("settings_title", "Настройки"))
        self.lbl_sel.config(text=self.l10n.get("selected_clock", "Настройки выбранных часов:"))
        self.title_label.config(text=self.l10n.get("title", "Заголовок:"))
        self.timezone_label.config(text=self.l10n.get("timezone", "Часовой пояс:"))
        self.date_format_label.config(text=self.l10n.get("date_format", "Формат даты"))
        self.time_format_label.config(text=self.l10n.get("time_format", "Формат времени"))
        self.font_label.config(text=self.l10n.get("font", "Шрифт (название):"))
        self.font_size_label.config(text=self.l10n.get("font_size", "Размер шрифта:"))
        self.title_font_size_label.config(text=self.l10n.get("title_font_size", "Размер шрифта заголовка:"))
        self.date_font_size_label.config(text=self.l10n.get("date_font_size", "Размер шрифта даты:"))
        self.color_label.config(text=self.l10n.get("color", "Цвет:"))
        self.color_btn.config(text="")
        self.reset_btn.config(text=self.l10n.get("reset_default", "Сбросить на умолчанию"))
        self.exit_btn.config(text=self.l10n.get("exit", "Закрыть программу"))
        ToolTip(self.sel_date_format, self.l10n.get("tooltip_date_format", "dd - день, MM - месяц, yyyy - год (4 цифры), yy - год (2 цифры), w - короткое название дня, W - полное название дня"))
        ToolTip(self.sel_time_format, self.l10n.get("tooltip_time_format", "HH:mm:ss - 24-часовой, hh:mm:ss p - 12-часовой с AM/PM"))

    def load_selected(self):
        # Загрузка настроек выбранных часов
        i = self.selected_index.get()
        if i < 0 or i >= len(self.clocks):
            self.sel_title.delete(0, "end")
            self.sel_timezone.set("")
            self.font_entry.delete(0, "end")
            self.font_entry.insert(0, "Arial")
            self.sel_size.delete(0, "end")
            self.sel_size.insert(0, "36")
            self.sel_title_size.delete(0, "end")
            self.sel_title_size.insert(0, "12")
            self.sel_date_size.delete(0, "end")
            self.sel_date_size.insert(0, "12")
            self.sel_date_format.delete(0, "end")
            self.sel_date_format.insert(0, "dd-MM-yyyy")
            self.sel_time_format.delete(0, "end")
            self.sel_time_format.insert(0, "HH:mm:ss")
            self.color_btn.config(bg="#FFFFFF", activebackground="#FFFFFF")
            return
        c = self.clocks[i]
        self.sel_title.delete(0, "end")
        self.sel_title.insert(0, c.get("title", ""))
        self.sel_timezone.set(c.get("timezone", "Europe/Moscow"))
        self.font_entry.delete(0, "end")
        self.font_entry.insert(0, c.get("font", "Arial"))
        self.sel_size.delete(0, "end")
        self.sel_size.insert(0, c.get("font_size", 36))
        self.sel_title_size.delete(0, "end")
        self.sel_title_size.insert(0, c.get("title_font_size", 12))
        self.sel_date_size.delete(0, "end")
        self.sel_date_size.insert(0, c.get("date_font_size", 12))
        self.sel_date_format.delete(0, "end")
        self.sel_date_format.insert(0, c.get("date_format", "dd-MM-yyyy"))
        self.sel_time_format.delete(0, "end")
        self.sel_time_format.insert(0, c.get("time_format", "HH:mm:ss"))
        self.color_btn.config(bg=c.get("color", "#FFFFFF"), activebackground=c.get("color", "#FFFFFF"))

    def save_changes(self):
        # Сохранение изменений без валидации
        i = self.selected_index.get()
        if i < 0 or i >= len(self.clocks):
            return
        title = self.sel_title.get().strip()
        existing_names = [c.get("title", "") for c in self.clocks if c is not self.clocks[i]]
        base_title = title or "Часы"
        index = 1
        new_title = base_title
        while new_title in existing_names:
            new_title = f"{base_title} {index}"
            index += 1
        c = self.clocks[i]
        c["title"] = new_title
        c["date_format"] = self.sel_date_format.get().strip()
        c["time_format"] = self.sel_time_format.get().strip()
        c["timezone"] = self.sel_timezone.get().strip() or "Europe/Moscow"
        c["font"] = self.font_entry.get().strip() or "Arial"
        c["font_size"] = self.sel_size.get()
        c["title_font_size"] = self.sel_title_size.get()
        c["date_font_size"] = self.sel_date_size.get()
        c["color"] = self.color_btn.cget("bg") or "#FFFFFF"
        self.lb.delete(i)
        self.lb.insert(i, c["title"])
        self.lb.select_set(i)
        self.selected_index.set(i)
        self.cfg["clocks"] = self.clocks