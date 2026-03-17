"""
Отправка email через Outlook
"""
import os
import urllib.parse

try:
    import win32com.client as win32
    import pythoncom
    HAS_OUTLOOK = True
except ImportError:
    HAS_OUTLOOK = False


def send_outlook_email(file_path: str, to_address: str) -> bool:
    """Отправляет email через Outlook с ссылкой на файл"""
    if not HAS_OUTLOOK:
        return False
    
    try:
        pythoncom.CoInitialize()
        try:
            outlook = win32.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)
            mail.To = to_address
            mail.Subject = f"Файл скопирован: {os.path.basename(file_path)}"

            unc_path = file_path.replace('\\', '/')
            encoded_path = urllib.parse.quote(unc_path, safe='/:')
            href = f"file:///{encoded_path}"

            mail.HTMLBody = f'Файл скопирован:<br><a href="{href}">{file_path}</a>'
            mail.Send()
            return True
        finally:
            pythoncom.CoUninitialize()
    except Exception:
        return False
