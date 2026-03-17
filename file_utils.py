"""
Парсинг имён файлов, работа с путями, копирование
"""
import os
import re
import shutil
from datetime import datetime

from config import MONTHS, ALLOWED_PREFIXES, PANORAMA_BASE, NEWS_STORAGE, ARCHIVE_STORIES


# -------------------------
# РАБОТА С МЕСЯЦАМИ
# -------------------------
def month_names(mm: str):
    return MONTHS.get(mm, {"title": f"{mm}", "lower": f"{mm}", "upper": f"{mm}"})


# -------------------------
# ПАРСИНГ ДАТ ИЗ ИМЁН ФАЙЛОВ
# -------------------------
def parse_mm_dd_panorama(fname: str):
    patterns = [
        r"^ПАНОРАМА_ДАЙДЖЕСТ_00_(\d{2})_(\d{2})_",
        r"^ПАНОРАМА_18_(\d{2})_(\d{2})_",
        r"^ПАНОРАМА_(\d{2})_(\d{2})_"
    ]
    for pattern in patterns:
        match = re.match(pattern, fname)
        if match:
            mm, dd = match.groups()
            if re.fullmatch(r"\d{2}", mm) and re.fullmatch(r"\d{2}", dd):
                return mm, dd
    return None, None


def parse_mm_news(fname: str):
    patterns = [
        r"^НОВОСТИ(?:_[A-ЯA-Z])?_?(\d{2})(\d{2})_",
        r"^НОВОСТИ_(\d{4})_",
        r"^НОВОСТИ(?:_[A-ЯA-Z])?_(\d{6})_",
    ]
    for pattern in patterns:
        match = re.match(pattern, fname)
        if match:
            if len(match.groups()) == 2:
                mm, dd = match.groups()
                return mm, dd
            elif len(match.groups()) == 1:
                date_str = match.group(1)
                if len(date_str) == 4:
                    mm, dd = date_str[2:4], "01"
                elif len(date_str) == 6:
                    mm, dd = date_str[2:4], date_str[4:6]
                else:
                    continue
                if re.fullmatch(r"\d{2}", mm) and re.fullmatch(r"\d{2}", dd):
                    return mm, dd
    return None, None


def parse_mm_dd_generic(fname: str):
    match = re.match(r"^(\d{2})_(\d{2})_", fname)
    if match:
        mm, dd = match.groups()
        if re.fullmatch(r"\d{2}", mm) and re.fullmatch(r"\d{2}", dd):
            return mm, dd
    return None, None


def extract_date_from_filename(fname: str):
    """Извлекает (mm, dd) из имени файла"""
    for parser in [parse_mm_dd_panorama, parse_mm_news, parse_mm_dd_generic]:
        mm, dd = parser(fname)
        if mm and dd:
            return mm, dd
    return None, None


def is_specific_date_file_by_name(fname: str, target_date: datetime) -> bool:
    """Проверяет, соответствует ли файл указанной дате"""
    mm, dd = extract_date_from_filename(fname)
    if not mm or not dd:
        return False
    return mm == target_date.strftime("%m") and dd == target_date.strftime("%d")


# -------------------------
# ПОДГОТОВКА ИМЁН
# -------------------------
def prepare_folder_name(text: str, for_files: bool = False) -> str:
    """Формирует имя папки/файла из текста проекта"""
    clean = re.sub(r'[\"«»]', '', text)

    bracket_word = ""
    open_bracket_pos = clean.find('(')
    if open_bracket_pos != -1:
        close_bracket_pos = clean.find(')', open_bracket_pos)
        if close_bracket_pos != -1:
            bracket_content = clean[open_bracket_pos + 1:close_bracket_pos]
            clean = clean[:open_bracket_pos] + clean[close_bracket_pos + 1:]
        else:
            bracket_content = clean[open_bracket_pos + 1:]
            clean = clean[:open_bracket_pos]
        first_part = bracket_content.split(',')[0]
        words_in_brackets = first_part.split()
        if words_in_brackets:
            bracket_word = words_in_brackets[0]

    # Удаляем только технические суффиксы типа "КР-25", "ВП-130" в конце
    clean = re.sub(r'[,\s]+[A-ZА-ЯЁ]{1,5}[-–—]\d+\s*$', '', clean)

    clean = re.sub(r'[\(\),]', ' ', clean)
    clean = ' '.join(clean.split())

    words = clean.split()
    processed_words = []
    for word in words:
        if any(c.isdigit() for c in word):
            processed_words.append(word)
        elif any(c.isupper() for c in word):
            processed_words.append(word)
        else:
            processed_words.append(word.capitalize())

    main_part = ''.join(processed_words)
    result = f"{main_part}_{bracket_word}" if bracket_word else main_part

    if for_files:
        result += "_"
    return result


def extract_file_name_without_prefix_and_date(fname: str) -> str:
    """Убирает префикс типа и дату из имени файла"""
    name, ext = os.path.splitext(fname)
    patterns = [
        r"^ПАНОРАМА_ДАЙДЖЕСТ_00_\d{2}_\d{2}_(.*)$",
        r"^ПАНОРАМА_18_\d{2}_\d{2}_(.*)$",
        r"^ПАНОРАМА_\d{2}_\d{2}_(.*)$",
        r"^НОВОСТИ(?:_[A-ЯA-Z])?_?\d{4}_(.*)$",
        r"^НОВОСТИ(?:_[A-ЯA-Z])?_?\d{2}\d{2}_(.*)$",
        r"^\d{2}_\d{2}_(.*)$"
    ]
    for pattern in patterns:
        match = re.match(pattern, name)
        if match:
            return match.group(1) + ext
    return fname


def extract_project_name_from_path(path: str) -> str:
    """Извлекает имя проекта из пути к папке"""
    match = re.search(r'\\(\d{2}\.\d{2}\.\d{4})\\(.*)$', path)
    if match:
        return match.group(2)
    return os.path.basename(path)


def get_efir_destination_filename(src_filename, efir_time, file_type):
    """Генерирует имя файла для эфира"""
    mm, dd = extract_date_from_filename(src_filename)
    if not mm or not dd:
        return src_filename
    base_name = extract_file_name_without_prefix_and_date(src_filename)
    if file_type == "ДАЙДЖЕСТ":
        return f"ПАНОРАМА_ДАЙДЖЕСТ_{efir_time}_{mm}_{dd}_{base_name}"
    elif file_type == "ПАНОРАМА":
        return f"ПАНОРАМА_{efir_time}_{mm}_{dd}_{base_name}"
    return src_filename


# -------------------------
# ПУТИ НАЗНАЧЕНИЯ
# -------------------------
def dest_site2(year, mm, dd):
    return os.path.join(PANORAMA_BASE, year, f"{mm}_{month_names(mm)['title']}", dd)


def dest_news_storage(year, mm):
    return os.path.join(NEWS_STORAGE, year, f"{mm}_{month_names(mm)['lower']}")


def dest_archive_stories(year, mm):
    return os.path.join(ARCHIVE_STORIES, year, f"{mm}_{month_names(mm)['upper']}")


# -------------------------
# УТИЛИТЫ КОПИРОВАНИЯ
# -------------------------
def normalize_path(path: str) -> str:
    return path.replace('/', '\\')


def is_file_already_copied(src_path: str, dest_path: str) -> bool:
    """Проверяет, скопирован ли файл (по размеру и времени модификации)"""
    if not os.path.exists(dest_path):
        return False
    src_size = os.path.getsize(src_path)
    dest_size = os.path.getsize(dest_path)
    if src_size != dest_size:
        return False
    return abs(os.path.getmtime(src_path) - os.path.getmtime(dest_path)) < 2


def find_files_by_date(target_date: datetime, search_folder: str, 
                       additional_folder: str = "") -> list:
    """Находит все mp4-файлы за указанную дату"""
    roots = [normalize_path(search_folder)]
    if additional_folder:
        extra = normalize_path(additional_folder)
        if os.path.isdir(extra):
            roots.append(extra)

    found = []
    for search_root in roots:
        if not os.path.isdir(search_root):
            continue
        for dirpath, _, filenames in os.walk(search_root):
            for fname in filenames:
                if not fname.lower().endswith(".mp4"):
                    continue
                full = os.path.join(dirpath, fname)
                try:
                    size = os.path.getsize(full)
                except OSError:
                    continue
                if (
                    is_specific_date_file_by_name(fname, target_date)
                    and size > 0
                    and (
                        fname.startswith(ALLOWED_PREFIXES)
                        or re.match(r"^\d{2}_\d{2}_", fname)
                    )
                ):
                    found.append(full)
    return found
