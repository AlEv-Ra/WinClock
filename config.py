import json
import os

# Путь к файлу конфигурации
CONFIG_FILE = "clock_config.json"
DEFAULT_FONT = "Arial"
DEFAULT_LANGUAGE = "ru"

# Словарь локализаций с днями недели, начиная с воскресенья (индекс 0)
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
        "alarm_date": "Enter date YYYY-MM-DD (optional):",
        "periodicity": "Periodicity:",
        "once": "Once",
        "daily": "Daily",
        "weekly": "Weekly",
        "monthly": "Monthly",
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
        "days_short": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],  # Короткие названия дней, начиная с воскресенья
        "days_full": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]  # Полные названия дней, начиная с воскресенья
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
        "alarm_date": "Введите дату ГГГГ-ММ-ДД (опционально):",
        "periodicity": "Периодичность:",
        "once": "Однократно",
        "daily": "Ежедневно",
        "weekly": "Еженедельно",
        "monthly": "Ежемесячно",
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
        "days_short": ["Вс", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"],  # Короткие названия дней, начиная с воскресенья
        "days_full": ["Воскресенье", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]  # Полные названия дней, начиная с воскресенья
    },
    "sr_latn": {
        "settings_title": "Podešavanja",
        "alarms_title": "Budilnici",
        "selected_clock": "Podešavanja izabranog sata:",
        "title": "Naslov:",
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
        "alarm_date": "Unesite datum GGGG-MM-DD (opciono):",
        "periodicity": "Periodičnost:",
        "once": "Jednom",
        "daily": "Dnevno",
        "weekly": "Nedeljno",
        "monthly": "Mesečno",
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
        "tooltip_time_format": "HH:mm:ss - 24-časovni, hh:mm:ss p - 12-časovni sa AM/PM",
        "reset_default": "Podrazumevano",
        "exit": "Закрыть программу",
        "confirm_exit": "Da li ste sigurni da želite zatvoriti program?",
        "days_short": ["Ned", "Pon", "Uto", "Sre", "Čet", "Pet", "Sub"],  # Короткие названия дней, начиная с воскресенья
        "days_full": ["Nedelja", "Ponedeljak", "Utorak", "Sreda", "Četvrtak", "Petak", "Subota"]  # Полные названия дней, начиная с воскресенья
    }
}

# Словарь флагов языков
LANGUAGE_FLAGS = {
    "en": "🇺🇸 English",
    "ru": "🇷🇺 Русский",
    "sr_latn": "🇷🇸 Srpski (latinica)"
}

def load_config():
    # Загрузка конфигурации из файла
    cfg = {
        "window": {"x": 100, "y": 100, "width": 300, "height": 200},
        "clocks": [
            {
                "title": "Москва",
                "font": DEFAULT_FONT,
                "font_size": 36,
                "title_font_size": 12,
                "date_font_size": 12,
                "color": "#FFFFFF",
                "timezone": "Europe/Moscow",
                "time_format": "HH:mm:ss",
                "date_format": "dd-MM-yyyy"
            }
        ],
        "alarms": [],
        "language": DEFAULT_LANGUAGE
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                cfg.update(loaded)
                for clock in cfg.get("clocks", []):
                    if "date_font_size" not in clock:
                        clock["date_font_size"] = 12
        except Exception as e:
            pass
    return cfg

def save_config(cfg):
    # Сохранение конфигурации в файл
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        pass