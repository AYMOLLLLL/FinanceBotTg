from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота с кнопкой удаления"""
    buttons = [
        [KeyboardButton(text="📥 Добавить расход"), KeyboardButton(text="💰 Добавить доход")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="📋 Последние операции")],
        [KeyboardButton(text="💡 Советы"), KeyboardButton(text="🗑️ Удалить операцию")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)