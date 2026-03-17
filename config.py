"""
Константы, настройки по умолчанию, работа с файлом settings.json
"""
import os
import sys
import json

# -------------------------
# ПУТИ ПО УМОЛЧАНИЮ
# -------------------------
BASE_PATH_DEFAULT = r"D:\Projects\ПАНОРАМА"
SOURCE_FILE = r"\\Archive1\графичекое_оформление\Test.prproj"

PANORAMA_BASE = r"\\ARCHIVE2\Site2"
EFIR_BASE = r"\\Archive1\export\ПАНОРАМА"
NEWS_STORAGE = r"\\archive2\Архив_25К\НОВОСТИ"
NEWS_EFIR25 = r"\\Archive2\25k\25k\НОВОСТИ"
CODER_SITE = r"\\NEWS-ENCODER\Coder_SITE"
CODER_25 = r"\\News-encoder25k\25K"
ARCHIVE_STORIES = r"\\Archive2\сюжеты панорамы 2"

EMAIL_VIDEOSERVER = "videoserver@otvprim.tv"
EMAIL_25REGION = "25region@otvprim.tv"

# -------------------------
# ВРЕМЯ ЭФИРА
# -------------------------
EFIR_TIMES = {
    "ДАЙДЖЕСТ": ["07", "12", "14", "16"],
    "ПАНОРАМА": ["18", "20"]
}

# -------------------------
# МЕСЯЦЫ
# -------------------------
MONTHS = {
    "01": {"title": "Январь", "lower": "январь", "upper": "ЯНВАРЬ"},
    "02": {"title": "Февраль", "lower": "февраль", "upper": "ФЕВРАЛЬ"},
    "03": {"title": "Март", "lower": "март", "upper": "МАРТ"},
    "04": {"title": "Апрель", "lower": "апрель", "upper": "АПРЕЛЬ"},
    "05": {"title": "Май", "lower": "май", "upper": "МАЙ"},
    "06": {"title": "Июнь", "lower": "июнь", "upper": "ИЮНЬ"},
    "07": {"title": "Июль", "lower": "июль", "upper": "ИЮЛЬ"},
    "08": {"title": "Август", "lower": "август", "upper": "АВГУСТ"},
    "09": {"title": "Сентябрь", "lower": "сентябрь", "upper": "СЕНТЯБРЬ"},
    "10": {"title": "Октябрь", "lower": "октябрь", "upper": "ОКТЯБРЬ"},
    "11": {"title": "Ноябрь", "lower": "ноябрь", "upper": "НОЯБРЬ"},
    "12": {"title": "Декабрь", "lower": "декабрь", "upper": "ДЕКАБРЬ"},
}

ALLOWED_PREFIXES = ("ПАНОРАМА_ДАЙДЖЕСТ", "ПАНОРАМА", "НОВОСТИ")

# -------------------------
# СТИЛИ ИНТЕРФЕЙСА
# -------------------------
TYPE_STYLES = {
    "ПАНОРАМА": {"color": "#8E24AA", "bootstyle": "info"},
    "ДАЙДЖЕСТ": {"color": "#8E24AA", "bootstyle": "info"},
    "НОВОСТИ": {"color": "#E53935", "bootstyle": "danger"},
    "АРХИВ": {"color": "#43A047", "bootstyle": "success"},
}

BUTTON_CONFIGS = {
    "В Панораму": {"bootstyle": "info-outline", "icon": "📁"},
    "В Эфир": {"bootstyle": "danger", "icon": "📡"},
    "Кодер Сайт": {"bootstyle": "primary-outline", "icon": "🌐"},
    "Хранение": {"bootstyle": "warning", "icon": "💾"},
    "В Эфир 25": {"bootstyle": "danger", "icon": "📡"},
    "Кодер 25": {"bootstyle": "primary-outline", "icon": "🌐"},
    "В Архив": {"bootstyle": "success", "icon": "📦"},
}

# -------------------------
# СОХРАНЕНИЕ НАСТРОЕК
# -------------------------
def get_settings_path():
    """Путь к settings.json рядом с exe или скриптом"""
    if hasattr(sys, '_MEIPASS'):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "settings.json")


SETTINGS_FILE = get_settings_path()


def load_settings() -> dict:
    """Загружает настройки из файла"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_settings(settings: dict):
    """Сохраняет настройки в файл"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
