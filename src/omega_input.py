import logging
import re
import unicodedata
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
import omega3_google_tracker

def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text).strip().lower()

def search_omega3_db(local_db, query):
    query_norm = normalize_text(query)
    results = []
    for row in local_db:
        desc = row.get("Description_RU", "")
        if query_norm in normalize_text(desc):
            results.append(row)
    return results

def build_search_keyboard(results):
    keyboard = []
    for idx, row in enumerate(results):
        desc_ru = row.get("Description_RU", "").strip()
        keyboard.append([InlineKeyboardButton(f"{idx+1}. {desc_ru}", callback_data=str(idx))])
    keyboard.append([InlineKeyboardButton("Не употреблял", callback_data="none")])
    keyboard.append([InlineKeyboardButton("Готово", callback_data="done")])
    return InlineKeyboardMarkup(keyboard)

async def omega_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message if update.message is not None else update.callback_query.message
    await message.reply_text("Введите название морепродукта (или его часть), например: лосось")
    return 0  # WAITING_FOR_QUERY

async def omega_query_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    local_db = context.bot_data.get("local_db", [])
    results = search_omega3_db(local_db, text)
    if not results:
        await update.message.reply_text(f"Ничего не найдено по запросу: {text}. Попробуйте ещё раз.")
        return 0
    context.user_data["search_results"] = results
    context.user_data["selected_indices"] = []
    kb = build_search_keyboard(results)
    await update.message.reply_text("Выберите продукт из списка:", reply_markup=kb)
    return 1  # WAITING_FOR_SELECTION

async def omega_select_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "none":
        context.user_data["report_omega"] = 0.0
        context.user_data["weekly_omega"] = 0.0
        await query.edit_message_text("Вы указали, что не употребляли морепродукты.")
        return ConversationHandler.END
    if data == "done":
        selected = context.user_data.get("selected_indices", [])
        if not selected:
            await query.edit_message_text("Вы не выбрали ни одного продукта. Попробуйте снова.")
            return ConversationHandler.END
        await query.edit_message_text("Введите количество (в граммах) для каждого выбранного продукта через запятую:")
        return 2  # WAITING_FOR_QUANTITIES
    else:
        idx = int(data)
        selected = context.user_data.setdefault("selected_indices", [])
        if idx not in selected:
            selected.append(idx)
        results = context.user_data["search_results"]
        chosen = [results[i]["Description_RU"] for i in selected]
        text = "Текущий выбор:\n" + "\n".join(chosen)
        text += "\n\nНажмите 'Готово' или 'Не употреблял', когда закончите выбор."
        kb = build_search_keyboard(results)
        await query.edit_message_text(text, reply_markup=kb)
        return 1

async def omega_input_quantities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    quantities_str = re.split(r'\s*,\s*', text)
    selected = context.user_data.get("selected_indices", [])
    if len(quantities_str) != len(selected):
        await update.message.reply_text("Количество введённых значений не совпадает с количеством выбранных продуктов.")
        return 2
    results = context.user_data["search_results"]
    total_omega = 0.0
    details = []
    for i, q in zip(selected, quantities_str):
        grams = float(q)
        row = results[i]
        base = float(row.get("Omega3 (g)", 0.0))
        val = base * (grams / 100)
        total_omega += val
        details.append(f"{row['Description_RU']} -> {val:.2f} г")
    context.user_data["report_omega"] = total_omega
    user_id = update.message.chat_id
    omega3_google_tracker.add_or_update_daily_omega(user_id, total_omega)
    weekly = omega3_google_tracker.get_weekly_omega(user_id)
    weekly_in_grams = weekly  
    context.user_data["weekly_omega"] = weekly_in_grams
    msg = "Результаты:\n" + "\n".join(details)
    msg += f"\n\nСуточная доза: {total_omega:.2f} г\nНедельная доза: {weekly_in_grams:.2f} г"
    await update.message.reply_text(msg)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Внести отчёт по красному мясу", callback_data="trigger_redmeat")]])
    await update.message.reply_text("Теперь можно рассчитать красное мясо:", reply_markup=kb)
    return ConversationHandler.END

def get_omega_conversation_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("omega", omega_command),
            CallbackQueryHandler(omega_command, pattern="^trigger_omega$")
        ],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, omega_query_input)],
            1: [CallbackQueryHandler(omega_select_product)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, omega_input_quantities)]
        },
        fallbacks=[CommandHandler("cancel", lambda update, context: update.message.reply_text("Операция отменена."))]
    )