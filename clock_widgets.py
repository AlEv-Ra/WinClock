import tkinter as tk
from datetime import datetime
import pytz

class ClockWidget:
    def __init__(self, app):
        # Инициализация виджета часов
        self.app = app
        self.clock_widgets = []

    def load_clocks_from_cfg(self):
        # Загрузка часов из конфигурации
        for widget in self.clock_widgets:
            widget["frame"].destroy()
        self.clock_widgets.clear()

        for clock_cfg in self.app.cfg["clocks"]:
            frame = tk.Frame(self.app.container, bg='black')
            frame.pack(fill="x", padx=5, pady=(10, 15))

            title_label = tk.Label(frame, text=clock_cfg.get("title", "Часы"), bg='black', fg=clock_cfg.get("color", "#FFFFFF"))
            title_label.pack(anchor="w")

            date_label = None
            if clock_cfg.get("date_format", ""):
                date_label = tk.Label(frame, text="", bg='black', fg=clock_cfg.get("color", "#FFFFFF"))
                date_label.pack(anchor="w", pady=(2, 2))

            time_label = tk.Label(frame, text="", bg='black', fg=clock_cfg.get("color", "#FFFFFF"))
            time_label.pack(anchor="w")

            clock_dict = {
                "frame": frame,
                "title_label": title_label,
                "time_label": time_label
            }
            if date_label:
                clock_dict["date_label"] = date_label
            self.clock_widgets.append(clock_dict)

        self.app.adjust_window_size()