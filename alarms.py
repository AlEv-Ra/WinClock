import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pytz
import json
import copy
import os
from datetime import datetime, timedelta
from tkcalendar import DateEntry  # Требует установки: pip install tkcalendar

# Путь к файлу конфигурации для отладки
CONFIG_FILE = "alarms_config.json"

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
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
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

    def position_dialog(self, widget):
        # Позиционирование диалога рядом с кнопкой с контролем границ
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + 5
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        dialog_width = 200
        dialog_height = 150
        if x + dialog_width > screen_width:
            x = screen_width - dialog_width
        if y + dialog_height > screen_height:
            y = widget.winfo_rooty() - dialog_height - 5
        if y < 0:
            y = 0
        return f"{dialog_width}x{dialog_height}+{x}+{y}"

class AlarmsSettingsWindow:
    def __init__(self, root=None, bell_label=None, cfg=None, l10n=None, update_callback=None):
        print("Инициализация AlarmsSettingsWindow...")
        self.root = root or tk.Tk()
        print(f"root: {self.root}")
        self.bell_label = bell_label
        print(f"bell_label: {self.bell_label}")
        self.cfg = cfg or self.load_config()
        print(f"cfg: {self.cfg}")
        self.l10n = l10n or self.load_l10n()
        print(f"l10n: {self.l10n}")
        self.alarms = copy.deepcopy(self.cfg.get("alarms", []))
        print(f"alarms: {self.alarms}")
        self.selected_index = tk.IntVar(value=0 if self.alarms else -1)
        print(f"selected_index: {self.selected_index.get()}")
        self.update_callback = update_callback
        print(f"update_callback: {self.update_callback}")

        self.win = tk.Toplevel(self.root) if root else self.root
        print(f"win создан: {self.win}")
        self.win.title(self.l10n.get("alarms_title", "Будильники"))
        self.win.configure(bg='white')
        self.position_window()
        self.win.protocol("WM_DELETE_WINDOW", self.on_close)
        print("Виджеты создаются...")
        self.create_widgets()
        self.load_selected()
        self.win.withdraw()  # Скрываем окно при создании
        print("Инициализация завершена")

    def load_config(self):
        # Загрузка конфигурации для отладки
        cfg = {
            "alarms": [],
            "alarms_window": "420x320+100+100",
            "language": "ru",
            "clocks": [{"timezone": "Europe/Moscow"}]  # Для отладки, по умолчанию первый часовой пояс
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    cfg.update(loaded)
            except Exception:
                pass
        return cfg

    def save_config(self, cfg):
        # Сохранение конфигурации для отладки
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_l10n(self):
        # Загрузка локализации для отладки (дополняем существующий словарь)
        LANGUAGES = {
            "en": {
                "settings_title": "Settings",
                "alarms_title": "Alarms",
                "selected_clock": "Selected clock settings:",
                "title": "Title:",
                "font": "Font (name):",
                "font_size": "Font size:",
                "title_font_size": "Title font size:",
                "date_font_size": "Date font size:",
                "color": "Color:",
                "timezone": "Timezone:",
                "choose_color": "Choose color",
                "save_changes": "Save changes",
                "add": "Add",
                "remove": "Remove",
                "language": "Language:",
                "alarm_time": "Enter time HH:MM",
                "alarm_date": "Date",
                "periodicity": "Periodicity:",
                "once": "Once",
                "weekly": "Weekly",
                "monthly": "Monthly",
                "yearly": "Yearly",
                "toggle": "Toggle On/Off",
                "alarm": "Alarm",
                "melody": "Melody:",
                "default": "default",
                "stop": "Stop",
                "snooze": "Snooze 5 min",
                "invalid_time": "Invalid time format",
                "invalid_date": "Invalid date format",
                "confirm_remove": "Remove selected clock?",
                "saved": "Settings saved",
                "select_clock": "Select a clock first",
                "tooltip_add": "Add a new clock",
                "tooltip_remove": "Remove selected clock",
                "tooltip_move_up": "Move clock up",
                "tooltip_move_down": "Move clock down",
                "date_format": "Date format",
                "time_format": "Time format",
                "tooltip_date_format": "dd - day, MM - month, yyyy - year (4 digits), yy - year (2 digits), w - short day name, W - full day name",
                "tooltip_time_format": "HH:mm:ss - 24-hour, hh:mm:ss p - 12-hour with AM/PM",
                "reset_default": "Reset to default",
                "exit": "Закрыть программу",
                "confirm_exit": "Are you sure you want to close the program?",
                "days_short": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],  # С понедельника
                "days_full": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],  # С понедельника
                # Новые ключи для формы будильников
                "notification": "Notification:",
                "timer": "Timer",
                "export": "Export",
                "import": "Import",
                "clear_all": "Clear All",
                "confirm_clear": "Clear all alarms?",
                "day_month": "Day of Month:",
                "yearly_date": "Date",
                "tooltip_hours": "Set hours (00-23)",
                "tooltip_minutes": "Set minutes (00-59)",
                "tooltip_edit_note": "Edit notification text"
            },
            "ru": {
                "settings_title": "Настройки",
                "alarms_title": "Будильники",
                "selected_clock": "Настройки выбранных часов:",
                "title": "Название:",
                "font": "Шрифт (имя):",
                "font_size": "Размер шрифта:",
                "title_font_size": "Размер шрифта заголовка:",
                "date_font_size": "Размер шрифта даты:",
                "color": "Цвет:",
                "timezone": "Часовой пояс:",
                "choose_color": "Выбрать цвет",
                "save_changes": "Сохранить изменения",
                "add": "Добавить",
                "remove": "Удалить",
                "language": "Язык:",
                "alarm_time": "Введите время ЧЧ:ММ",
                "alarm_date": "Дата",
                "periodicity": "Периодичность:",
                "once": "Однократно",
                "weekly": "Еженедельно",
                "monthly": "Ежемесячно",
                "yearly": "Ежегодно",
                "toggle": "Вкл/Выкл",
                "alarm": "Будильник",
                "melody": "Мелодия:",
                "default": "по умолчанию",
                "stop": "Стоп",
                "snooze": "Отложить на 5 мин",
                "invalid_time": "Неверный формат времени",
                "invalid_date": "Неверный формат даты",
                "confirm_remove": "Удалить выбранные часы?",
                "saved": "Настройки сохранены",
                "select_clock": "Сначала выберите часы",
                "tooltip_add": "Добавить новые часы",
                "tooltip_remove": "Удалить выбранные часы",
                "tooltip_move_up": "Переместить часы вверх",
                "tooltip_move_down": "Переместить часы вниз",
                "date_format": "Формат даты",
                "time_format": "Формат времени",
                "tooltip_date_format": "dd - день, MM - месяц, yyyy - год (4 цифры), yy - год (2 цифры), w - короткое название дня, W - полное название дня",
                "tooltip_time_format": "HH:mm:ss - 24-часовой, hh:mm:ss p - 12-часовой с AM/PM",
                "reset_default": "По умолчанию",
                "exit": "Закрыть программу",
                "confirm_exit": "Вы действительно хотите закрыть программу?",
                "days_short": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],  # С понедельника
                "days_full": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],  # С понедельника
                # Новые ключи для формы будильников
                "notification": "Уведомление:",
                "timer": "Таймер",
                "export": "Экспорт",
                "import": "Импорт",
                "clear_all": "Очистить все",
                "confirm_clear": "Очистить все будильники?",
                "day_month": "День месяца:",
                "yearly_date": "Дата",
                "tooltip_hours": "Установить часы (00-23)",
                "tooltip_minutes": "Установить минуты (00-59)",
                "tooltip_edit_note": "Редактировать текст уведомления"
            },
            "sr_latn": {
                "settings_title": "Podešavanja",
                "alarms_title": "Budilnici",
                "selected_clock": "Podešavanja izabranog sata:",
                "title": "Naziv:",
                "font": "Font (ime):",
                "font_size": "Veličina fonta:",
                "title_font_size": "Veličina fonta naslova:",
                "date_font_size": "Veličina fonta datuma:",
                "color": "Boja:",
                "timezone": "Vremenska zona:",
                "choose_color": "Izaberi boju",
                "save_changes": "Sačuvaj promene",
                "add": "Dodaj",
                "remove": "Ukloni",
                "language": "Jezik:",
                "alarm_time": "Unesite vreme ČČ:MM",
                "alarm_date": "Datum",
                "periodicity": "Periodičnost:",
                "once": "Jednom",
                "weekly": "Nedeljno",
                "monthly": "Mesečno",
                "yearly": "Godišnje",
                "toggle": "Uklj/Isklj",
                "alarm": "Budilnik",
                "melody": "Melodija:",
                "default": "podrazumevano",
                "stop": "Stop",
                "snooze": "Odloži 5 min",
                "invalid_time": "Nevažeći format vremena",
                "invalid_date": "Nevažeći format datuma",
                "confirm_remove": "Ukloniti izabrani sat?",
                "saved": "Podešavanja sačuvana",
                "select_clock": "Prvo izaberite sat",
                "tooltip_add": "Dodaj novi sat",
                "tooltip_remove": "Ukloni izabrani sat",
                "tooltip_move_up": "Pomeri sat gore",
                "tooltip_move_down": "Pomeri sat dole",
                "date_format": "Format datuma",
                "time_format": "Format vremena",
                "tooltip_date_format": "dd - dan, MM - mesec, yyyy - godina (4 cifre), yy - godina (2 cifre), w - kratki naziv dana, W - puni naziv dana",
                "tooltip_time_format": "HH:mm:ss - 24-časovni, hh:mm:ss p - 12-часovni sa AM/PM",
                "reset_default": "Podrazumevano",
                "exit": "Закрыть программу",
                "confirm_exit": "Da li ste sigurni da želite zatvoriti program?",
                "days_short": ["Pon", "Uto", "Sre", "Čet", "Pet", "Sub", "Ned"],  # С понедельника
                "days_full": ["Ponedeljak", "Utorak", "Sreda", "Četvrtak", "Petak", "Subota", "Nedelja"],  # С понедельника
                # Новые ключи для формы будильников
                "notification": "Obaveštenje:",
                "timer": "Tajmer",
                "export": "Izvoz",
                "import": "Uvoz",
                "clear_all": "Očisti sve",
                "confirm_clear": "Očistiti sve budilnike?",
                "day_month": "Dan meseca:",
                "yearly_date": "Datum",
                "tooltip_hours": "Postavi sate (00-23)",
                "tooltip_minutes": "Postavi minute (00-59)",
                "tooltip_edit_note": "Uredi tekst obaveštenja"
            }
        }
        return LANGUAGES.get(self.cfg.get("language", "ru"), LANGUAGES["ru"])

    def position_window(self):
        # Позиционирование формы будильников
        screen_width = self.win.winfo_screenwidth()
        screen_height = self.win.winfo_screenheight()
        form_width = 420
        form_height = 320
        try:
            geom = self.cfg.get("alarms_window", "420x320+100+100")
            parts = geom.replace("x", "+").split("+")
            width, height, pos_x, pos_y = map(int, parts)
            if (0 <= pos_x < screen_width - 50 and 0 <= pos_y < screen_height - 50 and
                width > 0 and height > 0):
                self.win.geometry(geom)
                return
        except:
            pass
        # Позиция рядом с кнопкой (если задана)
        if self.bell_label:
            try:
                bell_x = self.bell_label.winfo_rootx()
                bell_y = self.bell_label.winfo_rooty()
                bell_height = self.bell_label.winfo_height()
                positions = [
                    (bell_x - form_width - 10, bell_y - form_height // 2),
                    (bell_x - form_width - 10, bell_y + bell_height // 2),
                    (bell_x + 10, bell_y - form_height // 2),
                    (bell_x + 10, bell_y + bell_height // 2)
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
                    self.win.geometry(f"420x320+{best_position[0]}+{best_position[1]}")
                else:
                    self.win.geometry("420x320+100+100")
            except:
                self.win.geometry("420x320+100+100")

    def on_close(self):
        # ... твоя валидация и сбор cfg выше ...

        self.cfg["alarms"] = self.alarms
        self.cfg["alarms_window"] = self.win.geometry()

        # безопасный вызов колбэка с учётом сигнатуры
        if hasattr(self, 'update_callback') and self.update_callback:
            try:
                import inspect
                sig = inspect.signature(self.update_callback)
                if len(sig.parameters) == 0:
                    self.update_callback()  # колбэк без аргументов
                else:
                    self.update_callback(self.cfg)  # если вдруг он ожидает cfg
            except Exception as e:
                print(f"update_callback error: {e}")

        self.save_config(self.cfg)
        self.win.destroy()

    def create_widgets(self):
        # Создание элементов интерфейса формы будильников
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

        # Левая часть: Список будильников
        left_frame = tk.Frame(main_frame, bg='white')
        left_frame.pack(side="left", fill="y", padx=(0, 8))

        btn_frame = tk.Frame(left_frame, bg='white')
        btn_frame.pack(fill="x", padx=5, pady=5)
        btn_add = tk.Button(btn_frame, text="➕", command=self.add_alarm, width=5, font=("Arial", 12), fg="green")
        btn_add.pack(side="left", padx=(5, 2), pady=5)
        ToolTip(btn_add, self.l10n.get("tooltip_add", "Добавить будильник"))
        btn_remove = tk.Button(btn_frame, text="➖", command=self.remove_alarm, width=5, font=("Arial", 12), fg="red")
        btn_remove.pack(side="left", padx=(2, 2), pady=5)
        ToolTip(btn_remove, self.l10n.get("tooltip_remove", "Удалить выбранный будильник"))
        btn_clear = tk.Button(btn_frame, text="🗑️", command=self.clear_all, width=5, font=("Arial", 12), fg="darkred")
        btn_clear.pack(side="left", padx=(2, 2), pady=5)
        ToolTip(btn_clear, self.l10n.get("clear_all", "Очистить все будильники"))
        menu_btn = tk.Menubutton(btn_frame, text="...", relief="raised", font=("Arial", 10))
        menu_btn.pack(side="left", padx=(2, 2), pady=5)
        menu = tk.Menu(menu_btn, tearoff=0)
        menu.add_command(label=self.l10n.get("export", "Экспорт"), command=self.export_alarms)
        menu.add_command(label=self.l10n.get("import", "Импорт"), command=self.import_alarms)
        menu_btn.config(menu=menu)
        ToolTip(menu_btn, "Файл (Экспорт/Импорт)")
        btn_timer = tk.Button(btn_frame, text="⏲️", command=self.open_timer_dialog, width=5, font=("Arial", 12), fg="blue")
        btn_timer.pack(side="left", padx=(2, 5), pady=5)
        ToolTip(btn_timer, self.l10n.get("timer", "Создать таймер"))

        self.alarm_list = tk.Listbox(left_frame, width=25, height=10, exportselection=True, bg='white')
        self.alarm_list.pack(fill="both", expand=True, pady=(5, 0))
        self.alarm_list.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.alarm_list.bind("<Button-3>", self.show_context_menu)  # Контекстное меню правой кнопкой
        self.update_alarm_list()

        # Правая часть: Настройки будильника
        right_frame = tk.Frame(main_frame, bg='white', bd=2, relief="ridge")
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Исправлена компоновка: все элементы в одной колонке
        self.name_label = tk.Label(right_frame, text=self.l10n.get("title", "Название:"), bg='white', font=("Arial", 10, "bold"))
        self.name_label.pack(anchor="w", padx=5, pady=(5, 2))
        self.name_entry = tk.Entry(right_frame)
        self.name_entry.pack(fill="x", padx=5, pady=(0, 5))

        # Активность как сдвигающийся переключатель в одной строке
        self.active_frame = tk.Frame(right_frame, bg='white')
        self.active_var = tk.BooleanVar(value=True)
        self.active_switch = ttk.Checkbutton(self.active_frame, variable=self.active_var, style='Switch.TCheckbutton')
        self.active_switch.pack(side="left", padx=2)
        self.active_label = tk.Label(self.active_frame, text=self.l10n.get("active", "Активность"), bg='white', font=("Arial", 10))
        self.active_label.pack(side="left", padx=2)
        self.active_frame.pack(anchor="w", padx=5, pady=(5, 2))
        self.active_switch.config(command=self.update_active_color)
        self.active_var.trace('w', self.update_active_color)

        self.time_label = tk.Label(right_frame, text=self.l10n.get("time", "Время:"), bg='white', font=("Arial", 10, "bold"))
        self.time_label.pack(anchor="w", padx=5, pady=(5, 2))
        self.time_frame = tk.Frame(right_frame, bg='white')
        self.hour_spin = tk.Spinbox(self.time_frame, from_=0, to=23, width=2, format="%02.0f")
        ToolTip(self.hour_spin, self.l10n.get("tooltip_hours", "Установить часы (00-23)"))
        self.hour_spin.pack(side="left", padx=2)
        tk.Label(self.time_frame, text=":", bg='white').pack(side="left", padx=1)
        self.min_spin = tk.Spinbox(self.time_frame, from_=0, to=59, width=2, format="%02.0f")
        ToolTip(self.min_spin, self.l10n.get("tooltip_minutes", "Установить минуты (00-59)"))
        self.min_spin.pack(side="left", padx=2)
        self.time_frame.pack(anchor="w", padx=5, pady=(0, 5))

        self.timezone_label = tk.Label(right_frame, text=self.l10n.get("timezone", "Часовой пояс:"), bg='white', font=("Arial", 10, "bold"))
        self.timezone_label.pack(anchor="w", padx=5, pady=(5, 2))
        self.timezone_combo = ttk.Combobox(right_frame, values=[clock["timezone"] for clock in self.cfg.get("clocks", [{"timezone": "Europe/Moscow"}])])
        ToolTip(self.timezone_combo, self.l10n.get("tooltip_time_format", "HH:mm:ss - 24-часовой"))
        self.timezone_combo.pack(fill="x", padx=5, pady=(0, 5))

        self.repeat_label = tk.Label(right_frame, text=self.l10n.get("periodicity", "Периодичность:"), bg='white', font=("Arial", 10, "bold"))
        self.repeat_label.pack(anchor="w", padx=5, pady=(5, 2))
        self.repeat_var = tk.StringVar(value="once")
        self.repeat_combo = ttk.Combobox(right_frame, textvariable=self.repeat_var, values=[self.l10n.get("once"), self.l10n.get("weekly"), self.l10n.get("monthly"), self.l10n.get("yearly")], state="readonly")
        self.repeat_combo.pack(fill="x", padx=5, pady=(0, 5))
        self.repeat_combo.bind("<<ComboboxSelected>>", self.update_repeat_fields)

        # Блок выбора даты/числа/дней под Повтор
        self.date_frame = tk.Frame(right_frame, bg='white')
        self.date_label = tk.Label(self.date_frame, text=self.l10n.get("alarm_date", "Дата"), bg='white')
        self.date_label.pack(side="top", pady=2)
        self.date_entry = DateEntry(self.date_frame, date_pattern="y-mm-dd", state="normal")
        self.date_entry.pack(side="top", pady=2)
        self.date_frame.pack(anchor="w", padx=5, pady=(0, 5))

        self.weekly_frame = tk.Frame(right_frame, bg='white')
        self.days_labels = [tk.Label(self.weekly_frame, text=day, bg='white') for day in self.l10n.get("days_short", ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"])]
        self.days_vars = [tk.BooleanVar() for _ in range(7)]
        for i, (label, var) in enumerate(zip(self.days_labels, self.days_vars)):
            label.pack(side="left", padx=2)
            chk = tk.Checkbutton(self.weekly_frame, variable=var, bg='white')
            chk.pack(side="left", padx=2)
        self.weekly_frame.pack(anchor="w", padx=5, pady=(0, 5))

        self.monthly_frame = tk.Frame(right_frame, bg='white')
        self.monthly_label = tk.Label(self.monthly_frame, text=self.l10n.get("day_month", "День месяца:"), bg='white')
        self.monthly_label.pack(side="top", pady=2)
        self.day_month_spin = tk.Spinbox(self.monthly_frame, from_=1, to=31, width=5)
        self.day_month_spin.delete(0, tk.END)
        self.day_month_spin.insert(0, "1")
        self.day_month_spin.pack(side="top", pady=2)
        self.monthly_frame.pack(anchor="w", padx=5, pady=(0, 5))

        self.yearly_frame = tk.Frame(right_frame, bg='white')
        self.yearly_label = tk.Label(self.yearly_frame, text=self.l10n.get("yearly_date", "Дата"), bg='white')
        self.yearly_label.pack(side="top", pady=2)
        self.yearly_date_entry = DateEntry(self.yearly_frame, date_pattern="y-mm-dd", state="normal")
        self.yearly_date_entry.pack(side="top", pady=2)
        self.yearly_frame.pack(anchor="w", padx=5, pady=(0, 5))

        self.melody_label = tk.Label(right_frame, text=self.l10n.get("melody", "Мелодия:"), bg='white', font=("Arial", 10, "bold"))
        self.melody_label.pack(anchor="w", padx=5, pady=(5, 2))
        self.melody_var = tk.StringVar(value="default")
        self.melody_combo = ttk.Combobox(right_frame, textvariable=self.melody_var, values=["default", "bell1", "bell2"], state="readonly")
        ToolTip(self.melody_combo, self.l10n.get("tooltip_time_format", "Выберите мелодию"))
        self.melody_combo.pack(fill="x", padx=5, pady=(0, 5))
        self.choose_melody_btn = tk.Button(right_frame, text="Выбрать файл", command=self.choose_melody_file)
        ToolTip(self.choose_melody_btn, "Выберите MP3 файл")
        self.choose_melody_btn.pack(fill="x", padx=5, pady=(0, 5))

        self.notification_label = tk.Label(right_frame, text=self.l10n.get("notification", "Уведомление:"), bg='white', font=("Arial", 10, "bold"))
        self.notification_label.pack(anchor="w", padx=5, pady=(5, 2))
        self.notification_frame = tk.Frame(right_frame, bg='white')
        self.notification_entry = tk.Entry(self.notification_frame, width=20)
        self.notification_entry.pack(side="left", padx=5)
        self.edit_note_btn = tk.Button(self.notification_frame, text="...", command=self.edit_notification)
        ToolTip(self.edit_note_btn, self.l10n.get("tooltip_edit_note", "Редактировать текст уведомления"))
        self.edit_note_btn.pack(side="left", padx=5)
        self.notification_frame.pack(fill="x", padx=5, pady=(0, 5))

        self.update_repeat_fields()

    def update_repeat_fields(self, event=None):
        # Обновление полей в зависимости от типа повтора
        repeat = self.repeat_var.get()
        self.date_frame.pack_forget()
        self.weekly_frame.pack_forget()
        self.monthly_frame.pack_forget()
        self.yearly_frame.pack_forget()
        if repeat == self.l10n.get("once"):
            self.date_frame.pack(anchor="w", padx=5, pady=(0, 5))
        elif repeat == self.l10n.get("weekly"):
            self.weekly_frame.pack(anchor="w", padx=5, pady=(0, 5))
        elif repeat == self.l10n.get("monthly"):
            self.monthly_frame.pack(anchor="w", padx=5, pady=(0, 5))
        elif repeat == self.l10n.get("yearly"):
            self.yearly_frame.pack(anchor="w", padx=5, pady=(0, 5))

    def update_active_color(self, *args):
        # Обновление цвета переключателя активности
        if self.active_var.get():
            self.active_switch.configure(style='Switch.On.TCheckbutton')
        else:
            self.active_switch.configure(style='Switch.Off.TCheckbutton')

    def update_alarm_list(self):
        # Обновление списка будильников без Вкл/Выкл
        self.alarm_list.delete(0, tk.END)
        for i, alarm in enumerate(self.alarms):
            self.alarm_list.insert(i, alarm["name"])
            self.alarm_list.itemconfig(i, {'fg': 'black' if alarm.get("active", True) else 'gray'})

    def on_listbox_select(self, event):
        # Обновление настроек при выборе будильника
        if self.alarm_list.curselection():
            idx = self.alarm_list.curselection()[0]
            self.selected_index.set(idx)
            alarm = self.alarms[idx]
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, alarm.get("name", "Будильник"))
            self.active_var.set(alarm.get("active", True))
            time_parts = alarm.get("time", "00:00").split(":")
            self.hour_spin.delete(0, tk.END)
            self.hour_spin.insert(0, time_parts[0])
            self.min_spin.delete(0, tk.END)
            self.min_spin.insert(0, time_parts[1])
            self.timezone_combo.set(alarm.get("timezone", self.cfg["clocks"][0]["timezone"] if self.cfg.get("clocks") else "Europe/Moscow"))
            self.repeat_var.set(alarm.get("repeat", "once"))
            if "days" in alarm:
                for i, var in enumerate(self.days_vars):
                    var.set(alarm["days"][i] if i < len(alarm["days"]) else False)
            self.day_month_spin.delete(0, tk.END)
            self.day_month_spin.insert(0, alarm.get("day_month", "1"))
            self.date_entry.set_date(datetime.strptime(alarm.get("date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d").date() if alarm.get("date") else datetime.now().date())
            self.yearly_date_entry.set_date(datetime.strptime(alarm.get("date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d").date() if alarm.get("date") else datetime.now().date())
            self.melody_var.set(alarm.get("melody", "default"))
            self.notification_entry.delete(0, tk.END)
            self.notification_entry.insert(0, alarm.get("notification", ""))
            self.update_active_color()
            self.update_repeat_fields()

    def add_alarm(self):
        # Добавление нового будильника с временем +1 час
        base_name = "Будильник"
        existing_names = [a["name"] for a in self.alarms]
        index = 1
        new_name = base_name
        while new_name in existing_names:
            new_name = f"{base_name} {index}"
            index += 1
        # Установка времени текущим + 1 час
        tz_name = self.timezone_combo.get() or self.cfg["clocks"][0]["timezone"] if self.cfg.get("clocks") else "Europe/Moscow"
        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        future_time = now + timedelta(hours=1)
        alarm_time = future_time.strftime("%H:%M")
        default_date = now.strftime("%Y-%m-%d")
        if now.strftime("%H:%M") > alarm_time:
            default_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        new_alarm = {
            "name": new_name,
            "active": True,
            "time": alarm_time,
            "timezone": tz_name,
            "repeat": "once",
            "days": [False] * 7,
            "day_month": "1",
            "date": default_date,
            "melody": "default",
            "notification": ""
        }
        self.alarms.append(new_alarm)
        self.update_alarm_list()
        self.alarm_list.select_set(len(self.alarms) - 1)
        self.selected_index.set(len(self.alarms) - 1)
        self.on_listbox_select(None)

    def remove_alarm(self):
        # Удаление выбранного будильника
        if self.selected_index.get() >= 0 and messagebox.askyesno(self.l10n.get("alarms_title", "Будильники"), self.l10n.get("confirm_remove", "Удалить будильник?")):
            self.alarms.pop(self.selected_index.get())
            self.update_alarm_list()
            if self.alarms:
                new_index = min(self.selected_index.get(), len(self.alarms) - 1)
                self.alarm_list.select_set(new_index)
                self.selected_index.set(new_index)
            else:
                self.selected_index.set(-1)
            self.load_selected()

    def clear_all(self):
        # Очистка всех будильников
        if messagebox.askyesno(self.l10n.get("alarms_title", "Будильники"), self.l10n.get("confirm_clear", "Очистить все будильники?")):
            self.alarms.clear()
            self.update_alarm_list()
            self.selected_index.set(-1)
            self.load_selected()

    def export_alarms(self):
        # Экспорт будильников в файл
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.alarms, f, ensure_ascii=False, indent=2)

    def import_alarms(self):
        # Импорт будильников из файла
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    imported_alarms = json.load(f)
                    for alarm in imported_alarms:
                        self.alarms.append(alarm)
                    self.update_alarm_list()
                    if self.alarms:
                        self.alarm_list.select_set(len(self.alarms) - 1)
                        self.selected_index.set(len(self.alarms) - 1)
                        self.on_listbox_select(None)
            except Exception as e:
                messagebox.showerror("Error", f"Invalid file format: {e}")

    def choose_melody_file(self):
        # Выбор пользовательского файла мелодии
        file_path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        if file_path:
            self.melody_var.set(file_path)

    def open_timer_dialog(self):
        # Открытие диалога для создания таймера
        dialog = tk.Toplevel(self.win)
        dialog.title(self.l10n.get("timer", "Таймер"))
        dialog.configure(bg='white')
        geom = ToolTip.position_dialog(self, btn_timer)
        dialog.geometry(geom)
        dialog.transient(self.win)

        tk.Label(dialog, text="Часы:", bg='white').pack(pady=5)
        hours_spin = tk.Spinbox(dialog, from_=0, to=23, width=5)
        hours_spin.pack(pady=5)
        hours_spin.delete(0, tk.END)
        hours_spin.insert(0, "1")

        tk.Label(dialog, text="Минуты:", bg='white').pack(pady=5)
        mins_spin = tk.Spinbox(dialog, from_=0, to=59, width=5)
        mins_spin.pack(pady=5)
        mins_spin.delete(0, tk.END)
        mins_spin.insert(0, "0")

        def start_timer():
            hours = int(hours_spin.get())
            mins = int(mins_spin.get())
            total_mins = hours * 60 + mins
            if total_mins > 0:
                tz_name = self.timezone_combo.get() or self.cfg["clocks"][0]["timezone"] if self.cfg.get("clocks") else "Europe/Moscow"
                tz = pytz.timezone(tz_name)
                now = datetime.now(tz)
                current_time = f"{now.hour:02d}:{now.minute:02d}"
                future_time = now + timedelta(minutes=total_mins)
                default_date = now.strftime("%Y-%m-%d")
                if current_time > f"{future_time.hour:02d}:{future_time.minute:02d}":
                    default_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
                new_alarm = {
                    "name": "Таймер",
                    "active": True,
                    "time": future_time.strftime("%H:%M"),
                    "timezone": tz_name,
                    "repeat": "once",
                    "days": [False] * 7,
                    "day_month": "1",
                    "date": default_date,
                    "melody": "default",
                    "notification": "Таймер сработал"
                }
                self.alarms.append(new_alarm)
                self.update_alarm_list()
                self.alarm_list.select_set(len(self.alarms) - 1)
                self.selected_index.set(len(self.alarms) - 1)
                self.on_listbox_select(None)
                dialog.destroy()

        tk.Button(dialog, text="Старт", command=start_timer).pack(pady=10)
        tk.Button(dialog, text="Отмена", command=dialog.destroy).pack(pady=5)

    def edit_notification(self):
        # Открытие окна для редактирования многострочного уведомления
        dialog = tk.Toplevel(self.win)
        dialog.title(self.l10n.get("notification", "Уведомление:"))
        dialog.configure(bg='white')
        geom = ToolTip.position_dialog(self, self.edit_note_btn)
        dialog.geometry(geom)
        dialog.transient(self.win)

        text = tk.Text(dialog, height=10, width=40, bg='white')
        text.pack(padx=5, pady=5)
        text.insert(tk.END, self.notification_entry.get())

        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.config(yscrollcommand=scrollbar.set)

        def save_text():
            self.notification_entry.delete(0, tk.END)
            self.notification_entry.insert(0, text.get("1.0", tk.END).strip())
            dialog.destroy()

        tk.Button(dialog, text="Сохранить", command=save_text).pack(pady=5)
        tk.Button(dialog, text="Отмена", command=dialog.destroy).pack(pady=5)

    def load_selected(self):
        # Загрузка настроек выбранного будильника
        if self.selected_index.get() < 0 or self.selected_index.get() >= len(self.alarms):
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, "Будильник")
            self.active_var.set(True)
            self.hour_spin.delete(0, tk.END)
            self.hour_spin.insert(0, "00")
            self.min_spin.delete(0, tk.END)
            self.min_spin.insert(0, "00")
            self.timezone_combo.set(self.cfg["clocks"][0]["timezone"] if self.cfg.get("clocks") else "Europe/Moscow")
            self.repeat_var.set("once")
            for var in self.days_vars:
                var.set(False)
            self.day_month_spin.delete(0, tk.END)
            self.day_month_spin.insert(0, "1")
            self.date_entry.set_date(datetime.now().date())
            self.yearly_date_entry.set_date(datetime.now().date())
            self.melody_var.set("default")
            self.notification_entry.delete(0, tk.END)
            self.notification_entry.insert(0, "")
            self.update_active_color()
            self.update_repeat_fields()
        else:
            self.on_listbox_select(None)

    def show_context_menu(self, event):
        # Контекстное меню для списка будильников
        if not self.alarm_list.curselection():
            return
        context_menu = tk.Menu(self.win, tearoff=0)
        context_menu.add_command(label="Установить активность", command=self.set_active)
        context_menu.add_command(label="Снять активность", command=self.unset_active)
        context_menu.add_command(label="Копировать", command=self.copy_alarms)
        context_menu.post(event.x_root, event.y_root)

    def set_active(self):
        # Установка активности для выделенных будильников
        for idx in self.alarm_list.curselection():
            self.alarms[idx]["active"] = True
        self.update_alarm_list()

    def unset_active(self):
        # Снятие активности для выделенных будильников
        for idx in self.alarm_list.curselection():
            self.alarms[idx]["active"] = False
        self.update_alarm_list()

    def copy_alarms(self):
        # Копирование выделенных будильников
        selected_indices = self.alarm_list.curselection()
        copied_alarms = [copy.deepcopy(self.alarms[i]) for i in selected_indices]
        for alarm in copied_alarms:
            base_name = alarm["name"] + " (копия)"
            existing_names = [a["name"] for a in self.alarms]
            if base_name in existing_names:
                index = 1
                new_name = f"{base_name} {index}"
                while new_name in existing_names:
                    index += 1
                    new_name = f"{base_name} {index}"
                alarm["name"] = new_name
            self.alarms.append(alarm)
        self.update_alarm_list()
        if self.alarms:
            self.alarm_list.select_set(len(self.alarms) - len(copied_alarms), len(self.alarms) - 1)
            self.selected_index.set(len(self.alarms) - len(copied_alarms))

    def start_move(self, event):
        print("Начало перетаскивания...")
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        print("Перетаскивание...")
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.win.winfo_x() + deltax
        y = self.win.winfo_y() + deltay
        self.win.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    # Самостоятельная отладка формы
    root = tk.Tk()
    style = ttk.Style()
    style.configure('Switch.TCheckbutton', background='white')
    style.map('Switch.TCheckbutton',
              background=[('active', 'green'), ('!active', 'gray')],
              foreground=[('active', 'white'), ('!active', 'black')])
    app = AlarmsSettingsWindow(root)
    root.mainloop()