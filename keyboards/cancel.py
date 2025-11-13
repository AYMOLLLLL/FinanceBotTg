from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура только с кнопкой отмены"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )