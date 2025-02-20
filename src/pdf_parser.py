# src/pdf_parser.py
import re
import PyPDF2
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_products_from_pdf(file_path: str):
    """
    Извлекает кортежи (название продукта, вес, белок) из PDF-файла.
    Если следующая строка соответствует шаблону веса или содержит данные в скобках,
    объединяет её с предыдущей строкой как вес.
    Также, если после веса найдена строка с информацией о белке (например, "Белк: 20.7 г"),
    извлекает её.
    Остальная логика работы функции (извлечение названия и веса) остаётся без изменений.
    """
    products = []
    # Шаблон для веса (учитывает множитель, порции и прочее)
    weight_pattern = re.compile(
        r"^(?:\d+\s*x\s*)?\d+(?:[.,]\d+)?\s*(г|грамм|ml|миллилитр|миллилитров|мл|шт|штуки|piece|pieces|ложка|ложки|spoon|spoons|ст\s*л|столовая\s*ложка|столовой\s*ложки|порция)$",
        re.IGNORECASE
    )
    # Новый шаблон для белка: ищем варианты с "Белк" или "Белок" и числовое значение с единицами "г" или "гр"
    protein_pattern = re.compile(
        r"(?i)(?:бел[ок]{2}\s*[:\-]?\s*)(\d+(?:[.,]\d+)?)\s*(г|гр)"
    )
    
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        # Обрабатываем каждую страницу PDF
        for page in reader.pages:
            text = page.extract_text()
            logging.debug(f"[DEBUG] Извлечённый текст страницы: {text[:500]}...")
            # Разбиваем текст на строки
            lines = text.splitlines()
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue

                product_name = line
                weight_str = ""
                protein = None
                
                # Если следующая строка соответствует весу или содержит вес в скобках
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if weight_pattern.match(next_line.lower()):
                        weight_str = next_line
                        i += 1  # переходим к следующей строке после веса
                    else:
                        paren_match = re.search(r"\(\d+(?:[.,]\d+)?\s*(г|грамм|ml|миллилитр|миллилитров|мл)\)", next_line.lower())
                        if paren_match:
                            weight_str = next_line
                            i += 1

                # После строки с весом проверяем наличие информации о белке
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    protein_match = protein_pattern.search(next_line)
                    if protein_match:
                        protein = protein_match.group(1).replace(",", ".")
                        i += 1  # пропускаем строку с информацией о белке

                products.append((product_name, weight_str, protein))
                i += 1
    return products