# src/csv_parser.py

import csv
import re
import logging

def extract_products_from_csv(file_path: str):
    """
    Извлекает данные из CSV-файла и возвращает список кортежей (product_name, weight, protein).

    Предположения:
      - Файл содержит заголовок с колонками, например:
        "Дата,Кал ( ккал),Жир( г),Н/жир( г),Углев( г),Клетч( г),Сахар( г),Белк( г),Натри( мг),Холес( мг),Калий( мг)"
      - Если строка содержит только один непустой элемент и этот элемент соответствует шаблону веса,
        то она считается строкой с информацией о весе для предыдущей записи.
      - Если вес не обнаружен, используется значение по умолчанию "100 г".
      - Наименование продукта берется из первой колонки.
      - Значение белка берется из столбца, заголовок которого содержит "белк" (например, "Белк( г)").
    """
    products = []
    
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)
    
    # Найдем заголовок — пропускаем строки, начинающиеся с "#"
    header = None
    header_index = None
    for i, row in enumerate(rows):
        if not row:
            continue
        first = row[0].strip()
        if first.startswith("#"):
            continue
        if len(row) > 1:
            header = row
            header_index = i
            break

    if not header:
        logging.error("Заголовок CSV не найден.")
        return products

    # Определяем индекс столбца для белка — ищем заголовок, содержащий "белк"
    protein_idx = None
    for idx, col in enumerate(header):
        col_clean = col.strip().lower().replace(" ", "")
        if "белк(" in col_clean:
            protein_idx = idx
            break
    product_idx = 0

    # Регулярное выражение для определения строки с весом
    weight_pattern = r'^\s*[\d.,]+\s*(шт|г)\b'

    i = header_index + 1
    while i < len(rows):
        row = rows[i]
        # Пропускаем пустые строки и строки с комментариями
        if not row or all(not cell.strip() for cell in row):
            i += 1
            continue
        if row[0].strip().startswith("#"):
            i += 1
            continue

        # Если строка содержит только один непустой элемент и она соответствует шаблону веса,
        # то считаем, что это строка с весом для предыдущей записи.
        non_empty = [cell.strip() for cell in row if cell.strip() != ""]
        if len(non_empty) == 1 and re.search(weight_pattern, non_empty[0].lower()):
            if products and (products[-1][1] == "100 г" or not products[-1][1].strip()):
                prod, _, prot = products[-1]
                products[-1] = (prod, non_empty[0], prot)
            i += 1
            continue

        # Иначе, считаем строку как данные о продукте.
        product_name = row[product_idx].strip()
        protein_val = ""
        if protein_idx is not None and protein_idx < len(row):
            protein_val = row[protein_idx].strip()
        # Вес по умолчанию – "100 г"
        weight_val = "100 г"
        products.append((product_name, weight_val, protein_val))
        i += 1

    return products
