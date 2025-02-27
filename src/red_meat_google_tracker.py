import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import logging
import config

# Подключение к Google Sheets
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_CREDENTIALS_JSON, SCOPE)
client = gspread.authorize(creds)

# Открываем таблицу по ID и выбираем лист "RedMeatWeekly"
spreadsheet = client.open_by_key(config.GOOGLE_SPREADSHEET_ID)
try:
    sheet = spreadsheet.worksheet("RedMeatWeekly")
except gspread.WorksheetNotFound:
    # Если лист не найден, создаем его и задаем заголовки
    sheet = spreadsheet.add_worksheet(title="RedMeatWeekly", rows="1000", cols="4")
    sheet.append_row(["Date", "UserID", "Weight_g", "Protein_g"])

def add_or_update_daily_red_meat(user_id, weight_g, protein_g):
    """
    Добавляет или обновляет запись о красном мясе за сегодняшний день.
    Если запись уже есть, обновляем её новыми значениями.
    При записи белок форматируем как число с двумя знаками после запятой.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    uid_str = str(user_id)

    # Считываем все строки
    all_values = sheet.get_all_values()
    header = all_values[0] if all_values else []
    # Определим индексы столбцов (Date, UserID, Weight_g, Protein_g)
    try:
        date_col = header.index("Date")
        user_col = header.index("UserID")
        weight_col = header.index("Weight_g")
        protein_col = header.index("Protein_g")
    except ValueError:
        logging.error("Не найдены нужные заголовки в листе RedMeatWeekly")
        return

    found_row = None
    # Начинаем со второй строки, так как первая — заголовки
    for row_idx, row in enumerate(all_values[1:], start=2):
        if len(row) > user_col and row[date_col] == today_str and row[user_col] == uid_str:
            found_row = row_idx
            break

    protein_str = format(protein_g, ".2f")  # Форматируем белок с двумя знаками после запятой

    if found_row:
        logging.info(f"Обновляем красное мясо за {today_str} для user {uid_str}: {weight_g} г, {protein_str} г белка")
        sheet.update_cell(found_row, weight_col + 1, weight_g)
        sheet.update_cell(found_row, protein_col + 1, protein_str)
    else:
        logging.info(f"Добавляем запись красного мяса за {today_str} для user {uid_str}: {weight_g} г, {protein_str} г белка")
        sheet.append_row([today_str, uid_str, weight_g, protein_str])

def get_weekly_red_meat(user_id):
    """
    Суммирует данные красного мяса за текущую неделю (с понедельника) для данного user_id.
    Если значение белка явно превышает разумное значение (например, больше 100 г),
    предполагается, что оно сохранено с ошибкой масштабирования, и делится на 100.
    Возвращает (total_weight, total_protein).
    """
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())
    uid_str = str(user_id)

    all_records = sheet.get_all_records()
    total_weight = 0.0
    total_protein = 0.0

    for record in all_records:
        try:
            record_date = datetime.strptime(record.get("Date"), "%Y-%m-%d")
            if record_date.date() >= start_of_week.date() and str(record.get("UserID")) == uid_str:
                w = float(record.get("Weight_g", 0))
                p = float(record.get("Protein_g", 0))
                # Если белок больше 100, предполагаем ошибку масштабирования и делим на 100
                if p > 100:
                    p /= 100
                total_weight += w
                total_protein += p
        except Exception:
            continue

    return total_weight, total_protein