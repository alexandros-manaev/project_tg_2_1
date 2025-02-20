# main.py

import sys
import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Добавляем путь к src
sys.path.append(os.path.abspath('/content/drive/MyDrive/проект ТГ бот/project/src'))

import config
import auth
import pdf_parser
import fatsecret_api
import product_filters
import vegetable_fruit_filters
import omega3_google_tracker
import usda_omega3
import red_meat_tracker          # новый модуль для анализа красного мяса
import red_meat_google_tracker   # модуль для хранения данных по красному мясу в Google Sheets

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.chat_id
    if config.MASTER_ACCESS_TOKEN and config.MASTER_ACCESS_TOKEN_SECRET:
        logging.info(f"Мастер токены найдены для пользователя {user_id}, пропускаем авторизацию.")
        await update.message.reply_text("Мастер токены уже настроены. Вы можете сразу отправить PDF.")
    else:
        await update.message.reply_text("Привет! Для начала работы введите /login для авторизации FatSecret.")

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    if document.mime_type != "application/pdf":
        await update.message.reply_text("Пожалуйста, отправьте PDF-файл.")
        return
    file = await document.get_file()
    file_path = os.path.join(os.getcwd(), f"{document.file_id}.pdf")
    await file.download_to_drive(custom_path=file_path)
    await update.message.reply_text("PDF получен, начинаю обработку...")

    products = pdf_parser.extract_products_from_pdf(file_path)
    if not products:
        await update.message.reply_text("Не удалось извлечь данные из PDF.")
        return

    # 🔹 Кальций из молочных продуктов
    dairy_products = product_filters.filter_dairy_products(products, api_categories={})
    total_calcium = sum(
        fatsecret_api.get_calcium_for_product(product, config.MASTER_ACCESS_TOKEN, config.MASTER_ACCESS_TOKEN_SECRET, fatsecret_api.parse_weight(weight))
        for product, weight, _ in dairy_products
    )

    # 🔹 Масса растительной продукции (без извлечения клетчатки)
    total_weight, plant_message = vegetable_fruit_filters.handle_vegetables_and_fruits(products)

    # 🔹 Омега‑3 через USDA API
    omega3_products = [(p, w) for (p, w, *rest) in products]
    total_omega3_daily = sum(
        usda_omega3.get_omega3_for_product(product, fatsecret_api.parse_weight(weight))
        for product, weight in omega3_products
    )
    omega3_google_tracker.add_or_update_daily_omega(update.message.chat_id, total_omega3_daily * 1000)
    weekly_omega3_mg = omega3_google_tracker.get_weekly_omega(update.message.chat_id)
    weekly_omega3_g = round(weekly_omega3_mg / 1000, 2)
    total_omega3_daily = round(total_omega3_daily, 2)

    # 🔹 Анализ красного мяса
    red_meat_weight, red_meat_protein, red_meat_portions = red_meat_tracker.handle_red_meat(products)
    red_meat_msg = red_meat_tracker.red_meat_message(red_meat_weight, red_meat_protein, red_meat_portions)
    red_meat_google_tracker.add_or_update_daily_red_meat(update.message.chat_id, red_meat_weight, red_meat_protein)
    weekly_red_weight, weekly_red_protein = red_meat_google_tracker.get_weekly_red_meat(update.message.chat_id)
    weekly_red_portions = weekly_red_protein / 25.0 if weekly_red_protein > 0 else 0.0

    # 📌 Вывод результатов в чат
    await update.message.reply_text(f"Общий кальций из молочной продукции: {total_calcium:.1f} мг.")
    await update.message.reply_text(f"Общая масса растительных продуктов: {total_weight:.1f} г\n{plant_message}")
    await update.message.reply_text(f"Сегодня потреблено омега‑3: {total_omega3_daily:.2f} г")
    await update.message.reply_text(f"Недельное потребление омега‑3: {weekly_omega3_g:.2f} г")
    await update.message.reply_text(red_meat_msg)
    await update.message.reply_text(
        f"Недельное потребление красного мяса:\nПотреблено: {weekly_red_weight:.0f} г из 700 г\n"
        f"Белок: {weekly_red_protein:.1f} г (≈{weekly_red_portions:.1f} порций)"
    )

def main():
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    application.run_polling()

if __name__ == "__main__":
    main()