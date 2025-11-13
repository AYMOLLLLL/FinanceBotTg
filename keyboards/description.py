from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_description_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для ввода описания"""
    buttons = [
        [KeyboardButton(text="Пропустить")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)