import sys
import os
import re
import logging
import tempfile
import requests
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import config
import fatsecret_api
import product_filters
import vegetable_fruit_filters         # анализ растительной продукции
import red_meat_google_tracker          # обработка красного мяса
import omega3_google_tracker            # отслеживание омега‑3 в Google Sheets
from csv_parser import extract_products_from_csv
from local_omega3_db import load_local_omega3_db
from omega_input import get_omega_conversation_handler
from red_meat_input import get_red_meat_conversation_handler

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# ----- /start -----
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton("Сдать ежедневный отчёт")],
        [KeyboardButton("Рассчитать Омега‑3"), KeyboardButton("Рассчитать Красное мясо")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

# ----- /report -----
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Пришлите ссылку на ваш рацион за день (CSV) для расчёта кальция и растительной продукции.")

# ----- Обработчик CSV-ссылок -----
async def handle_csv_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    await update.message.reply_text("Обрабатываю вашу ссылку на CSV...")
    try:
        response = requests.get(text, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Ошибка скачивания CSV: {e}")
        await update.message.reply_text("Не удалось скачать CSV. Попробуйте снова.")
        return
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        tmp_file.write(response.content)
        tmp_file_path = tmp_file.name
    products = extract_products_from_csv(tmp_file_path)
    os.unlink(tmp_file_path)
    if not products:
        await update.message.reply_text("Не удалось извлечь продукты из CSV. Проверьте формат файла.")
        return

    dairy_filtered = product_filters.filter_dairy_products(products, {})
    total_calcium = sum(
        fatsecret_api.get_calcium_for_product(
            product,
            config.MASTER_ACCESS_TOKEN,
            config.MASTER_ACCESS_TOKEN_SECRET,
            fatsecret_api.parse_weight(weight)
        )
        for product, weight, *_ in dairy_filtered
    )
    total_weight, plant_message = vegetable_fruit_filters.handle_vegetables_and_fruits(products)
    context.user_data["report_calcium"] = total_calcium
    context.user_data["report_plant"] = (total_weight, plant_message)

    msg = (
        f"📊 **Отчёт по рациону:**\n\n"
        f"🧀 **Кальций:** {total_calcium:.1f} мг\n"
        f"🥗 **Растительная продукция:** {total_weight:.1f} г\n{plant_message}\n\n"
        "Теперь рассчитайте Омега‑3: нажмите кнопку ниже."
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Рассчитать Омега‑3", callback_data="trigger_omega")]])
    await update.message.reply_text(msg, reply_markup=keyboard)

# ----- Финальный отчёт -----
async def final_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    calcium = context.user_data.get("report_calcium", 0)
    plant = context.user_data.get("report_plant", (0, ""))
    omega = context.user_data.get("report_omega", 0)
    redmeat = context.user_data.get("report_redmeat", (0, 0))
    weekly_omega = context.user_data.get("weekly_omega", 0)
    weekly_red = context.user_data.get("weekly_redmeat", (0, 0))

    # --- Рекомендации ---
    rec_calcium = "✅ **Норма по кальцию выполнена!**" if calcium >= 800 else "⚠️ **Добавьте больше молочных продуктов!**"
    rec_plant = "✅ **Норма по растительности выполнена!**" if plant[0] >= 500 else "⚠️ **Добавьте больше овощей и фруктов!**"
    rec_omega_day = "✅ **Дневная норма Омега-3 выполнена!**" if omega >= 1.5 else "⚠️ **Добавьте рыбу или Омега-3 добавки!**"
    rec_omega_week = "✅ **Недельная норма Омега-3 выполнена!**" if 14 <= weekly_omega <= 21 else "⚠️ **Корректируйте потребление Омега-3!**"
    rec_red = "✅ **Вы придерживаетесь нормы по красному мясу!**" if weekly_red[0] <= 700 else "⚠️ **Сократите потребление красного мяса!**"

    final_msg = (
        "📊 **Итоговая сводка за день:**\n\n"
        f"🧀 **Кальций:** {calcium:.1f} мг\n{rec_calcium}\n\n"
        f"🥗 **Растительная продукция:** {plant[0]:.1f} г\n{rec_plant}\n\n"
        f"🐟 **Омега-3 за день:** {omega:.2f} г\n{rec_omega_day}\n"
        f"📅 **Недельное потребление Омега-3:** {weekly_omega:.2f} г\n{rec_omega_week}\n\n"
        f"🍖 **Красное мясо:** {weekly_red[0]:.1f} г за неделю\n{rec_red}"
    )
    
    await update.message.reply_text(final_msg)

# ----- main() -----
def main():
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.bot_data["local_db"] = load_local_omega3_db(os.path.join(os.path.dirname(__file__), "..", "data", "omega3_db.csv"))

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("finalreport", final_report))
    application.add_handler(get_omega_conversation_handler())
    application.add_handler(get_red_meat_conversation_handler())

    # Добавляем обработчик для точного совпадения "Сдать ежедневный отчёт"
    application.add_handler(MessageHandler(filters.Regex("^Сдать ежедневный отчёт$"), report_command))
    # Общий обработчик для остальных текстовых сообщений (CSV-ссылки)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_csv_link))

    logging.info("Bot started. Polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
