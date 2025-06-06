import gspread
from datetime import datetime, timedelta
import logging
import config

# Авторизация через gspread напрямую из JSON
client = gspread.service_account(filename=config.GOOGLE_CREDENTIALS_JSON)
spreadsheet = client.open_by_key(config.GOOGLE_SPREADSHEET_ID)

try:
    sheet = spreadsheet.worksheet("Omega3Weekly")
except gspread.WorksheetNotFound:
    sheet = spreadsheet.add_worksheet(title="Omega3Weekly", rows="1000", cols="3")
    sheet.append_row(["Date", "UserID", "Omega3"])

def add_or_update_daily_omega(user_id, omega_value):
    today_str = datetime.now().strftime("%Y-%m-%d")
    uid_str = str(user_id)

    all_values = sheet.get_all_values()
    header = all_values[0] if all_values else []

    try:
        date_index = header.index("Date")
        user_index = header.index("UserID")
        omega_index = header.index("Omega3")
    except ValueError:
        logging.error("Заголовки не найдены")
        return

    found_row = None
    for i, row in enumerate(all_values[1:], start=2):
        if len(row) > user_index and row[date_index] == today_str and row[user_index] == uid_str:
            found_row = i
            break

    # Преобразуем число в строку с запятой вместо точки (если требуется)
    omega_str = str(omega_value).replace('.', ',')

    if found_row:
        # Вместо накопления, перезаписываем значение для данного дня
        sheet.update_cell(found_row, omega_index + 1, omega_str)
    else:
        sheet.append_row([today_str, uid_str, omega_str])

def get_weekly_omega(user_id):
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())
    uid_str = str(user_id)
    total_omega = 0.0

    all_values = sheet.get_all_values()
    header = all_values[0] if all_values else []

    try:
        date_index = header.index("Date")
        user_index = header.index("UserID")
        omega_index = header.index("Omega3")
    except ValueError:
        logging.error("Заголовки не найдены")
        return 0.0

    for record in all_values[1:]:
        try:
            record_date = datetime.strptime(record[date_index], "%Y-%m-%d")
            if record_date.date() >= start_of_week.date() and record[user_index] == uid_str:
                omega_str = record[omega_index].replace(',', '.')
                total_omega += float(omega_str)
        except Exception as e:
            logging.error(f"Ошибка обработки записи: {e}")
            continue

    return total_omega
