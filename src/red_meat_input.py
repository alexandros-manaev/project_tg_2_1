import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import red_meat_google_tracker

# Определяем состояния диалога
SELECT_MEAT_TYPE, SELECT_FATNESS, INPUT_GRAMS, ANOTHER_OR_DONE = range(4)

# Факторы расчёта белка для разных типов красного мяса и жирностей
MEAT_PROTEIN_FACTORS = {
    "говядина": {"жирная": 0.18, "средней жирности": 0.20, "постная": 0.25},
    "свинина": {"жирная": 0.16, "средней жирности": 0.18, "постная": 0.22},
    "баранина": {"жирная": 0.17, "средней жирности": 0.19, "постная": 0.24},
    "утятина": {"жирная": 0.16, "средней жирности": 0.18, "постная": 0.23},
}

def get_red_meat_conversation_handler():
    return ConversationHandler(
        entry_points=[
            CommandHandler("redmeat", redmeat_start),
            CallbackQueryHandler(redmeat_start, pattern="^trigger_redmeat$")
        ],
        states={
            SELECT_MEAT_TYPE: [CallbackQueryHandler(select_meat_type)],
            SELECT_FATNESS: [CallbackQueryHandler(select_fatness)],
            INPUT_GRAMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_grams)],
            ANOTHER_OR_DONE: [CallbackQueryHandler(another_or_done)]
        },
        fallbacks=[],
    )

async def redmeat_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Старт диалога для расчёта красного мяса. Обрабатывает как текстовое сообщение, так и callback-запрос.
    """
    if update.callback_query:
        await update.callback_query.answer()
        reply_target = update.callback_query.message
    else:
        reply_target = update.message

    keyboard = [
        [InlineKeyboardButton(meat_type.capitalize(), callback_data=meat_type)]
        for meat_type in MEAT_PROTEIN_FACTORS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.user_data["selected_meats"] = []

    await reply_target.reply_text("Выберите тип красного мяса:", reply_markup=reply_markup)
    return SELECT_MEAT_TYPE

async def select_meat_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    meat_type = query.data

    # Если получено неожиданное значение, перезапускаем выбор
    if meat_type not in MEAT_PROTEIN_FACTORS:
        await query.edit_message_text("Неверный выбор. Пожалуйста, выберите тип мяса заново.")
        return await redmeat_start(update, context)

    context.user_data["current_meat_type"] = meat_type

    keyboard = [
        [InlineKeyboardButton(fatness.capitalize(), callback_data=fatness)]
        for fatness in MEAT_PROTEIN_FACTORS[meat_type]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Вы выбрали {meat_type}. Теперь выберите жирность:", reply_markup=reply_markup
    )
    return SELECT_FATNESS

async def select_fatness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    fatness = query.data
    context.user_data["current_fatness"] = fatness

    await query.edit_message_text("Введите количество в граммах:")
    return INPUT_GRAMS

async def input_grams(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        grams = float(text.replace(',', '.'))
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число.")
        return INPUT_GRAMS

    # Получаем выбранные параметры
    meat_type = context.user_data.get("current_meat_type")
    fatness = context.user_data.get("current_fatness")
    factor = MEAT_PROTEIN_FACTORS.get(meat_type, {}).get(fatness, 0)
    protein = grams * factor

    # Сохраняем запись в список выбранных значений
    selected = context.user_data.setdefault("selected_meats", [])
    selected.append((meat_type, fatness, grams, protein))

    # Обновляем данные в Google Sheets
    user_id = update.effective_chat.id
    total_weight = sum(item[2] for item in selected)
    total_protein = sum(item[3] for item in selected)
    red_meat_google_tracker.add_or_update_daily_red_meat(user_id, total_weight, total_protein)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить ещё", callback_data="another")],
        [InlineKeyboardButton("Готово", callback_data="done")]
    ])
    await update.message.reply_text("Запись сохранена. Добавить ещё или завершить?", reply_markup=keyboard)
    return ANOTHER_OR_DONE

async def another_or_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "another":
        keyboard = [
            [InlineKeyboardButton(meat_type.capitalize(), callback_data=meat_type)]
            for meat_type in MEAT_PROTEIN_FACTORS
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите тип красного мяса:", reply_markup=reply_markup)
        return SELECT_MEAT_TYPE
    else:
        # Обновляем данные по красному мясу из Google Sheets
        user_id = update.effective_chat.id
        weekly_red = red_meat_google_tracker.get_weekly_red_meat(user_id)
        context.user_data["weekly_redmeat"] = weekly_red

        # Формируем финальный отчёт с рекомендациями
        calcium = context.user_data.get("report_calcium", 0)
        plant = context.user_data.get("report_plant", (0, ""))
        omega = context.user_data.get("report_omega", 0)
        weekly_omega = context.user_data.get("weekly_omega", 0)

        rec_calcium = "✅ **Норма по кальцию выполнена!**" if calcium >= 800 else "⚠️ **Добавьте больше молочных продуктов!**"
        rec_plant = "✅ **Норма по растительности выполнена!**" if plant[0] >= 500 else "⚠️ **Добавьте больше овощей и фруктов!**"
        rec_omega_day = "✅ **Дневная норма Омега-3 выполнена!**" if omega >= 1.5 else "⚠️ **Добавьте рыбу или Омега-3 добавки!**"
        rec_omega_week = "✅ **Недельная норма Омега-3 выполнена!**" if 14 <= weekly_omega <= 21 else "⚠️ **Корректируйте потребление Омега-3!**"
        # Предполагается, что weekly_red – это кортеж, где первый элемент – суммарный вес красного мяса за неделю
        rec_red = "✅ **Вы придерживаетесь нормы по красному мясу!**" if weekly_red[0] <= 700 else "⚠️ **Сократите потребление красного мяса!**"

        final_msg = (
            "📊 **Итоговая сводка за день:**\n\n"
            f"🧀 **Кальций:** {calcium:.1f} мг\n{rec_calcium}\n\n"
            f"🥗 **Растительная продукция:** {plant[0]:.1f} г\n{rec_plant}\n\n"
            f"🐟 **Омега-3 за день:** {omega:.2f} г\n{rec_omega_day}\n"
            f"📅 **Недельное потребление Омега-3:** {weekly_omega:.2f} г\n{rec_omega_week}\n\n"
            f"🍖 **Красное мясо:** {weekly_red[0]:.1f} г за неделю\n{rec_red}"
        )
        await query.edit_message_text(final_msg)
        return ConversationHandler.END
