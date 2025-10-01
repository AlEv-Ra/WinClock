import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pytz
import json
import copy
import os
from datetime import datetime, timedelta
from tkcalendar import DateEntry  # Требует установки: pip install tkcalendar
from config import load_config, save_config, LANGUAGES, DEFAULT_LANGUAGE

import platform
try:
    import winsound  # есть только на Windows
except ImportError:
    winsound = None

from utils import ToolTip, play_sound


# Путь к файлу конфигурации для отладки
CONFIG_FILE = "alarms_config.json"


class AlarmsSettingsWindow:
    def __init__(self, root=None, bell_label=None, cfg=None, l10n=None, update_callback=None):
        self.root = root or tk.Tk()
        self.bell_label = bell_label
        self.cfg = cfg or {}
        self.l10n = l10n or LANGUAGES.get(self.cfg.get("language", DEFAULT_LANGUAGE), LANGUAGES["ru"])
        self.alarms = copy.deepcopy(self.cfg.get("alarms", []))
        self.selected_index = tk.IntVar(value=0 if self.alarms else -1)
        self.update_callback = update_callback
        self.win = tk.Toplevel(self.root) if root else self.root
        self.win.title(self.l10n.get("alarms_title", "Будильники"))
        self.win.configure(bg='white')
        self.position_window()
        self.win.protocol("WM_DELETE_WINDOW", self.on_close)
        print("Виджеты создаются...")
        self.create_widgets()
        self.load_selected()
        print("Инициализация завершена")


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
        self.cfg["alarms"] = self.alarms
        self.cfg["alarms_window"] = self.win.geometry()
        if self.update_callback:
            try:
                self.update_callback()
            except Exception as e:
                print("update_callback error:", e)
        save_config(self.cfg)
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
        self.btn_timer = tk.Button(btn_frame, text="⏲️", command=self.open_timer_dialog, width=5, font=("Arial", 12),
                                   fg="blue")
        self.btn_timer.pack(side="left", padx=(2, 5), pady=5)
        ToolTip(self.btn_timer, self.l10n.get("timer", "Создать таймер"))

        self.alarm_list = tk.Listbox(left_frame, width=25, height=10, exportselection=False, bg='white')
        self.alarm_list.pack(fill="both", expand=True, pady=(5, 0))
        self.alarm_list.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.alarm_list.bind("<Button-3>", self.show_context_menu)  # Контекстное меню правой кнопкой
        self.update_alarm_list()

        # Правая часть: Настройки будильника
        right_frame = tk.Frame(main_frame, bg='white', bd=2, relief="ridge")
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Исправлена компоновка: все элементы в одной колонке
        self.name_label = tk.Label(right_frame, text=self.l10n.get("title", "Название:"), bg='white',
                                   font=("Arial", 10, "bold"))
        self.name_label.pack(anchor="w", padx=5, pady=(5, 2))
        self.name_entry = tk.Entry(right_frame)
        self.name_entry.pack(fill="x", padx=5, pady=(0, 5))
        self.name_entry.bind("<KeyRelease>", self.update_alarm_from_form)  # 🔥 сразу сохраняем

        # Активность как сдвигающийся переключатель в одной строке
        self.active_frame = tk.Frame(right_frame, bg='white')
        self.active_var = tk.BooleanVar(value=True)
        self.active_switch = ttk.Checkbutton(self.active_frame, variable=self.active_var, style='Switch.TCheckbutton')
        self.active_switch.pack(side="left", padx=2)
        self.active_label = tk.Label(self.active_frame, text=self.l10n.get("active", "Активность"), bg='white',
                                     font=("Arial", 10))
        self.active_label.pack(side="left", padx=2)
        self.active_frame.pack(anchor="w", padx=5, pady=(5, 2))
        self.active_switch.config(command=self.update_alarm_from_form)  # 🔥 сразу сохраняем
        self.active_var.trace('w', lambda *a: self.update_alarm_from_form())  # 🔥 сразу сохраняем

        self.time_label = tk.Label(right_frame, text=self.l10n.get("time", "Время:"), bg='white',
                                   font=("Arial", 10, "bold"))
        self.time_label.pack(anchor="w", padx=5, pady=(5, 2))
        self.time_frame = tk.Frame(right_frame, bg='white')

        self.hour_spin = tk.Spinbox(self.time_frame, from_=0, to=23, width=2, format="%02.0f", wrap=True,
                                    command=self.update_alarm_from_form)  # 🔥
        self.hour_spin.bind("<KeyRelease>", self.update_alarm_from_form)
        ToolTip(self.hour_spin, self.l10n.get("tooltip_hours", "Установить часы (00-23)"))
        self.hour_spin.pack(side="left", padx=2)

        tk.Label(self.time_frame, text=":", bg='white').pack(side="left", padx=1)

        self.min_spin = tk.Spinbox(self.time_frame, from_=0, to=59, width=2, format="%02.0f", wrap=True,
                                   command=self.update_alarm_from_form)  # 🔥
        self.min_spin.bind("<KeyRelease>", self.update_alarm_from_form)
        ToolTip(self.min_spin, self.l10n.get("tooltip_minutes", "Установить минуты (00-59)"))
        self.min_spin.pack(side="left", padx=2)

        self.time_frame.pack(anchor="w", padx=5, pady=(0, 5))

        self.timezone_label = tk.Label(right_frame, text=self.l10n.get("timezone", "Часовой пояс:"), bg='white',
                                       font=("Arial", 10, "bold"))
        self.timezone_label.pack(anchor="w", padx=5, pady=(5, 2))
        self.timezone_combo = ttk.Combobox(right_frame, values=[clock["timezone"] for clock in self.cfg.get("clocks", [
            {"timezone": "Europe/Moscow"}])])
        ToolTip(self.timezone_combo, self.l10n.get("tooltip_time_format", "HH:mm:ss - 24-часовой"))
        self.timezone_combo.pack(fill="x", padx=5, pady=(0, 5))
        self.timezone_combo.bind("<<ComboboxSelected>>", self.update_alarm_from_form)  # 🔥

        self.repeat_label = tk.Label(right_frame, text=self.l10n.get("periodicity", "Периодичность:"), bg='white',
                                     font=("Arial", 10, "bold"))
        self.repeat_label.pack(anchor="w", padx=5, pady=(5, 2))
        self.repeat_var = tk.StringVar(value="once")
        self.repeat_combo = ttk.Combobox(right_frame, textvariable=self.repeat_var,
                                         values=[self.l10n.get("once"), self.l10n.get("weekly"),
                                                 self.l10n.get("monthly"), self.l10n.get("yearly")], state="readonly")
        self.repeat_combo.pack(fill="x", padx=5, pady=(0, 5))
        self.repeat_combo.bind("<<ComboboxSelected>>", self.update_alarm_from_form)  # 🔥

        # Блок выбора даты/числа/дней под Повтор
        self.date_frame = tk.Frame(right_frame, bg='white')
        self.date_label = tk.Label(self.date_frame, text=self.l10n.get("alarm_date", "Дата"), bg='white')
        self.date_label.pack(side="top", pady=2)
        self.date_entry = DateEntry(self.date_frame, date_pattern="y-mm-dd", state="normal")
        self.date_entry.pack(side="top", pady=2)
        self.date_entry.bind("<<DateEntrySelected>>", self.update_alarm_from_form)  # 🔥
        self.date_frame.pack(anchor="w", padx=5, pady=(0, 5))

        self.weekly_frame = tk.Frame(right_frame, bg='white')
        self.days_labels = [tk.Label(self.weekly_frame, text=day, bg='white') for day in
                            self.l10n.get("days_short", ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"])]
        self.days_vars = [tk.BooleanVar() for _ in range(7)]
        for i, (label, var) in enumerate(zip(self.days_labels, self.days_vars)):
            label.pack(side="left", padx=2)
            chk = tk.Checkbutton(self.weekly_frame, variable=var, bg='white',
                                 command=self.update_alarm_from_form)  # 🔥 сразу сохраняем
            chk.pack(side="left", padx=2)
        self.weekly_frame.pack(anchor="w", padx=5, pady=(0, 5))

        self.monthly_frame = tk.Frame(right_frame, bg='white')
        self.monthly_label = tk.Label(self.monthly_frame, text=self.l10n.get("day_month", "День месяца:"), bg='white')
        self.monthly_label.pack(side="top", pady=2)
        self.day_month_spin = tk.Spinbox(self.monthly_frame, from_=1, to=31, width=5,
                                         command=self.update_alarm_from_form)  # 🔥
        self.day_month_spin.bind("<KeyRelease>", self.update_alarm_from_form)
        self.day_month_spin.pack(side="top", pady=2)
        self.monthly_frame.pack(anchor="w", padx=5, pady=(0, 5))

        self.yearly_frame = tk.Frame(right_frame, bg='white')
        self.yearly_label = tk.Label(self.yearly_frame, text=self.l10n.get("yearly_date", "Дата"), bg='white')
        self.yearly_label.pack(side="top", pady=2)
        self.yearly_date_entry = DateEntry(self.yearly_frame, date_pattern="y-mm-dd", state="normal")
        self.yearly_date_entry.pack(side="top", pady=2)
        self.yearly_date_entry.bind("<<DateEntrySelected>>", self.update_alarm_from_form)  # 🔥
        self.yearly_frame.pack(anchor="w", padx=5, pady=(0, 5))

        self.melody_label = tk.Label(right_frame, text=self.l10n.get("melody", "Мелодия:"), bg='white',
                                     font=("Arial", 10, "bold"))
        self.melody_label.pack(anchor="w", padx=5, pady=(5, 2))
        self.melody_var = tk.StringVar(value="default")
        self.melody_combo = ttk.Combobox(right_frame, textvariable=self.melody_var,
                                         values=["default", "bell1", "bell2"], state="readonly")
        ToolTip(self.melody_combo, self.l10n.get("tooltip_time_format", "Выберите мелодию"))
        self.melody_combo.pack(fill="x", padx=5, pady=(0, 5))
        self.melody_combo.bind("<<ComboboxSelected>>", self.update_alarm_from_form)  # 🔥
        self.choose_melody_btn = tk.Button(right_frame, text="Выбрать файл", command=self.choose_melody_file)
        ToolTip(self.choose_melody_btn, "Выберите MP3 файл")
        self.choose_melody_btn.pack(fill="x", padx=5, pady=(0, 5))

        self.notification_label = tk.Label(right_frame, text=self.l10n.get("notification", "Уведомление:"), bg='white',
                                           font=("Arial", 10, "bold"))
        self.notification_label.pack(anchor="w", padx=5, pady=(5, 2))
        self.notification_frame = tk.Frame(right_frame, bg='white')
        self.notification_entry = tk.Entry(self.notification_frame, width=20)
        self.notification_entry.pack(side="left", padx=5)
        self.notification_entry.bind("<KeyRelease>", self.update_alarm_from_form)  # 🔥
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
        self.alarm_list.delete(0, tk.END)
        for i, alarm in enumerate(self.alarms):
            self.alarm_list.insert(i, alarm["name"])
            self.alarm_list.itemconfig(i, {'fg': 'black' if alarm.get("active", True) else 'gray'})

        if self.alarms:
            if self.selected_index.get() < 0 or self.selected_index.get() >= len(self.alarms):
                self.selected_index.set(0)

            idx = self.selected_index.get()
            self.alarm_list.selection_clear(0, tk.END)
            self.alarm_list.selection_set(idx)
            self.alarm_list.activate(idx)
            self.alarm_list.see(idx)  # всегда видимая строка
            self.alarm_list.focus_set()

    def on_listbox_select(self, event=None):
        if not self.alarm_list.curselection():
            return
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

        self.timezone_combo.set(alarm.get("timezone", "Europe/Moscow"))
        self.repeat_var.set(alarm.get("repeat", "once"))

        for i, var in enumerate(self.days_vars):
            var.set(alarm.get("days", [False] * 7)[i])

        self.day_month_spin.delete(0, tk.END)
        self.day_month_spin.insert(0, alarm.get("day_month", "1"))

        self.date_entry.set_date(
            datetime.strptime(alarm.get("date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d").date())
        self.yearly_date_entry.set_date(
            datetime.strptime(alarm.get("date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d").date())

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
        geom = ToolTip.position_dialog(self, self.btn_timer)
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
        geom = ToolTip.position_dialog(self.edit_note_btn)
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
        if self.selected_index.get() < 0 or self.selected_index.get() >= len(self.alarms):
            # Нет будильников → чистим и блокируем
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, "")
            self.active_var.set(False)
            self.hour_spin.delete(0, tk.END)
            self.hour_spin.insert(0, "00")
            self.min_spin.delete(0, tk.END)
            self.min_spin.insert(0, "00")
            self.notification_entry.delete(0, tk.END)
            self.notification_entry.insert(0, "")
            self.set_form_state(False)  # тут блокировка
            return
        else:
            self.set_form_state(True)  # разблокировка
            self.on_listbox_select(None)

        """# Загрузка настроек выбранного будильника
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
            self.on_listbox_select(None)"""

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

    def update_alarm_from_form(self, event=None):
        if 0 <= self.selected_index.get() < len(self.alarms):
            alarm = self.alarms[self.selected_index.get()]
            alarm["name"] = self.name_entry.get()
            alarm["active"] = self.active_var.get()
            alarm["time"] = f"{self.hour_spin.get()}:{self.min_spin.get()}"
            alarm["timezone"] = self.timezone_combo.get()
            alarm["repeat"] = self.repeat_var.get()
            alarm["day_month"] = self.day_month_spin.get()
            alarm["date"] = str(self.date_entry.get_date())
            alarm["melody"] = self.melody_var.get()
            alarm["notification"] = self.notification_entry.get()
            alarm["days"] = [var.get() for var in self.days_vars]  # <-- добавь это!
            self.update_alarm_list()

    def set_form_state(self, enabled=True):
        state = "normal" if enabled else "disabled"
        widgets = [
            self.name_entry, self.hour_spin, self.min_spin, self.timezone_combo,
            self.repeat_combo, self.day_month_spin, self.date_entry,
            self.yearly_date_entry, self.melody_combo, self.choose_melody_btn,
            self.notification_entry, self.edit_note_btn
        ]
        for w in widgets:
            try:
                w.config(state=state)
            except Exception:
                pass

    def get_alarm_text(self, alarm):
        """Возвращает текст уведомления"""
        if alarm.get("notification"):
            return alarm["notification"]
        return f"{alarm.get('name', 'Будильник')} в {alarm.get('time', '00:00')}"

    def show_notification(self, alarm):
        """Показывает уведомление в правом нижнем углу с отступом ~1–1.5 см и запускает звук."""
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.configure(bg="white")

        # Размер уведомления
        width, height = 280, 120

        # Отступ 1–1.5 см (умножаем сантиметры в пиксели)
        try:
            cm = self.root.winfo_fpixels('1c')  # пикселей в 1 см
        except Exception:
            cm = 38  # запасной вариант ~1см на 96dpi
        margin = int(cm * 1.3)  # ~1.3 см

        # Позиция (правый нижний угол)
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        x = screen_w - width - margin
        y = screen_h - height - margin
        win.geometry(f"{width}x{height}+{x}+{y}")

        # Текст уведомления
        text = self.get_alarm_text(alarm)
        tk.Label(win, text=text, bg="white", font=("Arial", 12), wraplength=width - 20, justify="left").pack(padx=10,
                                                                                                             pady=10,
                                                                                                             fill="x")

        btns = tk.Frame(win, bg="white")
        btns.pack(fill="x", padx=10, pady=(0, 10))

        # Кнопка Стоп: останавливает звук И закрывает окно
        tk.Button(btns, text="Стоп",
                  command=lambda: self.stop_alarm(win)).pack(side="left", expand=True, fill="x", padx=(0, 5))

        # Кнопка Отложить: сдвигает время, останавливает звук И закрывает окно
        tk.Button(btns, text="Отложить на 5 мин",
                  command=lambda: self.snooze_alarm(alarm, 5, win)).pack(side="right", expand=True, fill="x",
                                                                         padx=(5, 0))

        # Запускаем звук
        play_sound(alarm.get("melody"), self.root)

    def snooze_alarm(self, alarm, minutes, win):
        """Сдвигает время будильника на указанное число минут, останавливает звук и закрывает уведомление."""
        try:
            # если в alarm["date"] нет даты — ставим сегодня
            if not alarm.get("date"):
                alarm["date"] = datetime.now().strftime("%Y-%m-%d")

            # сдвигаем
            dt = datetime.now() + timedelta(minutes=minutes)
            alarm["time"] = dt.strftime("%H:%M")
            alarm["date"] = dt.strftime("%Y-%m-%d")
        except Exception as e:
            print("Ошибка snooze:", e)

        # стоп звука и закрытие окна
        self.stop_alarm_sound()
        if win and win.winfo_exists():
            win.destroy()

        self.update_alarm_list()
        # при желании можно сразу сохранить:
        self.cfg["alarms"] = self.alarms
        save_config(self.cfg)

    def stop_alarm(self, notif_win):
        """Обработчик кнопки Стоп: остановить звук и закрыть окно уведомления."""
        self.stop_alarm_sound()
        if notif_win and notif_win.winfo_exists():
            notif_win.destroy()

    def stop_alarm_sound(self):
        """Останавливает звук будильника."""
        if platform.system() == "Windows" and winsound:
            winsound.PlaySound(None, 0)  # стоп SND_ASYNC/SND_LOOP

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