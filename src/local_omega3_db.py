import csv

def load_local_omega3_db(file_path):
    """
    Загружает локальную базу омега‑3 из CSV-файла.
    Ожидается, что CSV содержит заголовок с колонками, например: "Description_RU", "Omega3 (g)".
    Используем кодировку "utf-8-sig" для обработки BOM.
    Возвращает список словарей.
    """
    data = []
    try:
        with open(file_path, newline='', encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)
            reader.fieldnames = [field.strip() for field in reader.fieldnames]
            for row in reader:
                cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                data.append(cleaned_row)
    except Exception as e:
        print(f"Ошибка загрузки локальной базы: {e}")
    return data

def get_local_omega3(file_path):
    return load_local_omega3_db(file_path)

def add_to_local_db(file_path, record):
    try:
        with open(file_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, None)
    except FileNotFoundError:
        headers = None

    with open(file_path, 'a', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = record.keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if headers is None:
            writer.writeheader()
        writer.writerow(record)

def save_local_omega3_db(file_path, data):
    if not data:
        return
    with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
