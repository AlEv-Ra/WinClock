import tkinter as tk
from tkinter import ttk, messagebox
import pytz
from datetime import datetime
import time
import sys
from config import load_config, save_config, LANGUAGES, DEFAULT_FONT, DEFAULT_LANGUAGE
from clock_widgets import ClockWidget
from alarms import AlarmsSettingsWindow
from settings import SettingsWindow
import locale


class DigitalClockApp:
    def __init__(self, root):
        # Инициализация главного окна приложения
        self.root = root
        self.root.configure(bg='black')
        self.root.attributes('-transparentcolor', 'black')  # Установка прозрачного фона
        self.root.overrideredirect(True)  # Убираем рамку окна

        # Загрузка конфигурации
        self.cfg = load_config()
        self.language = self.cfg.get("language", DEFAULT_LANGUAGE)
        self.l10n = LANGUAGES.get(self.language, LANGUAGES["en"])

        # Установка локали
        try:
            locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8" if self.language == "ru" else "en_US.UTF-8")
        except locale.Error:
            locale.setlocale(locale.LC_TIME, "")

        w = self.cfg.get("window", {})
        self.x = w.get("x", 100)
        self.y = w.get("y", 100)
        self.width = w.get("width", 300)
        self.height = w.get("height", 200)
        self.root.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")

        self.dragging = False
        self.resizing = False
        self.start_x = 0
        self.start_y = 0

        # Создание контейнера для виджетов часов
        self.container = tk.Frame(self.root, bg='black')
        self.container.pack(expand=True, fill="both")

        # Фрейм для кнопок управления
        self.controls_frame = tk.Frame(self.root, bg='black')
        self.controls_frame.pack(side="bottom", fill="x", padx=5, pady=5)

        # Метка будильника
        self.bell_label = tk.Label(self.controls_frame, text="", font=("Arial", 20), bg='black', fg="white",
                                   cursor="hand2")
        self.bell_label.pack(side="left", padx=(0, 10))
        self.bell_label.bind("<Button-1>", lambda e: self.open_alarms_window())

        # Метка настроек
        self.gear_label = tk.Label(self.controls_frame, text="⚙️", font=("Arial", 20), bg='black', fg="white",
                                   cursor="hand2")
        self.gear_label.pack(side="right", padx=(10, 0))
        self.gear_label.bind("<Button-1>", lambda e: self.open_settings_window())

        # Привязка событий для перетаскивания окна
        self.root.bind("<Button-1>", self.start_drag_root)
        self.root.bind("<B1-Motion>", self.on_drag_root)
        self.root.bind("<ButtonRelease-1>", self.stop_drag_root)

        # Инициализация виджетов часов
        self.clock_widgets = ClockWidget(self)
        self.alarms = None  # Инициализация атрибута
        self.set_default_timezone()
        self.clock_widgets.load_clocks_from_cfg()
        self.update_bell_icon()
        self.update_time_loop()

    def open_alarms_window(self):
        if not hasattr(self, 'alarms') or self.alarms is None:
            try:
                self.alarms = AlarmsSettingsWindow(root=self.root, bell_label=self.bell_label, cfg=self.cfg,
                                                   l10n=self.l10n, update_callback=self.update_bell_icon)
            except Exception as e:
                print(f"Ошибка при создании окна будильников: {e}")
                return
        if self.alarms and hasattr(self.alarms, 'win'):
            self.alarms.win.deiconify()  # Показать окно, если оно было создано
        else:
            print("Окно будильников не инициализировано корректно")

    def set_default_timezone(self):
        # Установка часового пояса по умолчанию, если часы не настроены
        if not self.cfg.get("clocks"):
            try:
                local_tz = time.tzname[0]
                tz = pytz.timezone(local_tz) if local_tz in pytz.all_timezones else "Europe/Moscow"
            except:
                tz = "Europe/Moscow"
            self.cfg["clocks"] = [{
                "title": "Москва",
                "font": DEFAULT_FONT,
                "font_size": 36,
                "title_font_size": 12,
                "date_font_size": 12,
                "color": "#FFFFFF",
                "timezone": tz,
                "time_format": "HH:mm:ss",
                "date_format": "dd-MM-yyyy"
            }]
            save_config(self.cfg)

    def adjust_window_size(self):
        # Настройка размера окна на основе содержимого
        self.root.update_idletasks()
        req_width = self.container.winfo_reqwidth()
        req_height = self.container.winfo_reqheight() + self.controls_frame.winfo_reqheight()
        self.width = max(150, req_width)
        self.height = max(100, req_height)
        self.root.geometry(f"{self.width}x{self.height}+{self.x}+{self.y}")
        save_config(self.cfg)

    def start_drag_root(self, event):
        # Начало перетаскивания окна
        if event.widget in (self.bell_label, self.gear_label):
            return
        self.dragging = True
        geom = self.root.geometry()
        try:
            parts = geom.split("+")
            self.x = int(parts[1])
            self.y = int(parts[2])
        except:
            pass
        self.start_x = event.x_root - self.x
        self.start_y = event.y_root - self.y

    def on_drag_root(self, event):
        # Перетаскивание окна
        if self.dragging:
            self.x = event.x_root - self.start_x
            self.y = event.y_root - self.start_y
            self.root.geometry(f"+{self.x}+{self.y}")

    def stop_drag_root(self, event):
        # Завершение перетаскивания и сохранение позиции
        if self.dragging:
            self.dragging = False
            self.save_window_cfg()

    def save_window_cfg(self):
        # Сохранение параметров окна в конфигурацию
        self.cfg.setdefault("window", {})
        self.cfg["window"]["x"] = self.x
        self.cfg["window"]["y"] = self.y
        self.cfg["window"]["width"] = self.width
        self.cfg["window"]["height"] = self.height
        save_config(self.cfg)

    def convert_format(self, user_format, now):
        """Преобразование пользовательского формата в строку с текущими значениями времени/даты"""
        if not user_format:
            return ""
        # Получение базовых значений времени и даты
        hour_24 = now.strftime("%H")
        hour_12 = now.strftime("%I")
        minute = now.strftime("%M")
        second = now.strftime("%S")
        day = now.strftime("%d")
        month = now.strftime("%m")
        year_full = now.strftime("%Y")
        year_short = now.strftime("%y")

        # Определение AM/PM на основе 24-часового формата
        am_pm = "AM" if int(hour_24) < 12 else "PM"

        # Получение дней недели из словаря локализации
        days_short = LANGUAGES[self.language].get("days_short", ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"])
        days_full = LANGUAGES[self.language].get("days_full",
                                                 ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday",
                                                  "Friday"])
        weekday = now.weekday()
        # Корректировка индекса: weekday() возвращает 0 для понедельника, а массив начинается с субботы
        # Для воскресенья (6) должно быть 1, поэтому используем (weekday + 6) % 7
        adjusted_weekday = (weekday+1) % 7 #Не знаю почему, но нужно добавить 1
        day_short = days_short[adjusted_weekday]
        day_full = days_full[adjusted_weekday]

        # Замена токенов
        result = user_format
        result = result.replace("HH", hour_24).replace("H", hour_24)
        result = result.replace("hh", hour_12).replace("h", hour_12)
        result = result.replace("mm", minute).replace("m", minute)
        result = result.replace("ss", second).replace("s", second)
        # Обработка p в любом месте строки
        if "p" in result:
            result = result.replace("p", am_pm)
            # Применяем 12-часовой формат, если есть h/hh
            if "hh" in user_format or "h" in user_format:
                result = result.replace("HH", hour_12).replace("H", hour_12)
        result = result.replace("dd", day)
        result = result.replace("MM", month)
        result = result.replace("yyyy", year_full)
        result = result.replace("yy", year_short)
        result = result.replace("w", day_short)
        result = result.replace("W", day_full)
        return result

    def update_time_loop(self):
        # Обновление времени и даты для всех часов с учётом часового пояса
        for idx, cw in enumerate(self.clock_widgets.clock_widgets):
            if idx >= len(self.cfg["clocks"]):
                break
            clock_cfg = self.cfg["clocks"][idx]
            tz_name = clock_cfg.get("timezone", "Europe/Moscow")
            try:
                tz = pytz.timezone(tz_name)
                # Создаём now с учётом часового пояса
                now = datetime.now(tz)
                time_str = self.convert_format(clock_cfg.get("time_format", "HH:mm:ss"), now)
                date_str = self.convert_format(clock_cfg.get("date_format", "dd-MM-yyyy"), now)
            except pytz.exceptions.UnknownTimeZoneError:
                now = datetime.now()
                time_str = self.convert_format(clock_cfg.get("time_format", "HH:mm:ss"), now)
                date_str = self.convert_format(clock_cfg.get("date_format", "dd-MM-yyyy"), now)
            global_font = self.cfg.get("global_font", "Arial")
            date_font_size = clock_cfg.get("date_font_size", 12)
            if "date_label" in cw and date_str:
                cw["date_label"].config(
                    text=date_str,
                    font=(global_font, date_font_size),
                    fg=clock_cfg.get("color", "#FFFFFF")
                )
            elif "date_label" in cw:
                cw["date_label"].config(text="")
            cw["time_label"].config(
                text=time_str,
                font=(global_font, clock_cfg.get("font_size", 36)),
                fg=clock_cfg.get("color", "#FFFFFF")
            )
            cw["title_label"].config(
                font=(global_font, clock_cfg.get("title_font_size", 12), "bold"),
                fg=clock_cfg.get("color", "#FFFFFF")
            )
        self.adjust_window_size()
        self.root.after(1000, self.update_time_loop)

    def update_bell_icon(self):
        # Обновление значка будильника (🔔/🔕)
        active_any = False
        if self.alarms and hasattr(self.alarms, 'alarms'):
            active_any = any(a.get("active", False) for a in self.alarms.alarms)
        self.bell_label.config(text="🔔" if active_any else "🔕", fg="white", bg='black')

    def open_settings_window(self):
        # Открытие окна настроек
        def update_callback(cfg, reopen_settings=False):
            self.cfg = cfg
            self.language = self.cfg.get("language", DEFAULT_LANGUAGE)
            self.l10n = LANGUAGES.get(self.language, LANGUAGES["en"])
            try:
                locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8" if self.language == "ru" else "en_US.UTF-8")
            except locale.Error:
                locale.setlocale(locale.LC_TIME, "")
            save_config(self.cfg)
            self.clock_widgets.load_clocks_from_cfg()
            self.update_bell_icon()
            if reopen_settings:
                SettingsWindow(self.root, self.gear_label, self.cfg, self.l10n, update_callback,
                               exit_callback=self.exit_program)

        def exit_callback():
            self.root.destroy()
            sys.exit(0)

        SettingsWindow(self.root, self.gear_label, self.cfg, self.l10n, update_callback, exit_callback=exit_callback)

    def exit_program(self):
        # Закрытие программы
        self.root.destroy()
        sys.exit(0)


if __name__ == "__main__":
    root = tk.Tk()
    app = DigitalClockApp(root)
    root.mainloop()