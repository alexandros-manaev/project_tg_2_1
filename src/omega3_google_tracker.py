# src/omega3_google_tracker.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import config

# Определяем область доступа к Google API
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_CREDENTIALS_JSON, SCOPE)
client = gspread.authorize(creds)

# Открываем таблицу по ID и выбираем лист "Omega3Weekly"
spreadsheet = client.open_by_key(config.GOOGLE_SPREADSHEET_ID)
try:
    sheet = spreadsheet.worksheet("Omega3Weekly")
except gspread.WorksheetNotFound:
    # Если лист не найден, создаем его и задаем заголовки
    sheet = spreadsheet.add_worksheet(title="Omega3Weekly", rows="1000", cols="3")
    sheet.append_row(["Date", "UserID", "Omega3"])

def add_or_update_daily_omega(user_id, omega_value):
    """
    Добавляет или обновляет суточное значение омега‑3 для указанного пользователя в Google Sheets.
    Если запись за сегодняшний день существует и значение совпадает, ничего не происходит.
    Если значение отличается, обновляется запись.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    uid = str(user_id)
    values = sheet.get_all_values()
    header = values[0]
    try:
        date_index = header.index("Date")  # 0-based
        user_index = header.index("UserID")  # 0-based
        omega_index = header.index("Omega3")  # 0-based, для update_cell используем 1-based индекс
    except ValueError:
        print("[ERROR] Заголовки не найдены")
        return

    found_row = None
    # Перебираем строки (начиная со второй, т.к. первая – заголовок)
    for i, row in enumerate(values[1:], start=2):
        if len(row) >= 3 and row[date_index] == today and row[user_index] == uid:
            found_row = i
            break

    if found_row:
        # Получаем текущее значение омега‑3
        current_value_str = sheet.cell(found_row, omega_index + 1).value
        try:
            current_value = float(current_value_str)
        except (ValueError, TypeError):
            current_value = 0.0
        if current_value == omega_value:
            print(f"[DEBUG] Значение омега‑3 для чата {uid} за {today} не изменилось ({omega_value} мг)")
            return
        else:
            print(f"[DEBUG] Обновляем значение омега‑3 для чата {uid} за {today}: {current_value} мг -> {omega_value} мг")
            sheet.update_cell(found_row, omega_index + 1, omega_value)
    else:
        print(f"[DEBUG] Добавляем запись омега‑3 для чата {uid} за {today}: {omega_value} мг")
        sheet.append_row([today, uid, omega_value])

def get_weekly_omega(user_id):
    """
    Возвращает суммарное значение омега‑3 за текущую неделю для пользователя.
    Суммируются все записи, начиная с понедельника текущей недели.
    """
    now = datetime.now()
    # ISO: понедельник = 1, воскресенье = 7
    start_of_week = now - timedelta(days=now.isoweekday()-1)
    uid = str(user_id)
    total = 0.0
    records = sheet.get_all_records()
    for record in records:
        try:
            record_date = datetime.strptime(record.get("Date"), "%Y-%m-%d")
            if record_date >= start_of_week and str(record.get("UserID")) == uid:
                total += float(record.get("Omega3", 0))
        except Exception:
            continue
    return total