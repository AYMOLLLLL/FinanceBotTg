from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_categories_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с категориями расходов"""
    categories = [
        [KeyboardButton(text="🏠 Жилье"), KeyboardButton(text="🍎 Продукты")],
        [KeyboardButton(text="🚗 Транспорт"), KeyboardButton(text="💊 Здоровье")],
        [KeyboardButton(text="🎮 Развлечения"), KeyboardButton(text="🛍️ Покупки")],
        [KeyboardButton(text="✈️ Путешествия"), KeyboardButton(text="📚 Образование")],
        [KeyboardButton(text="💳 Кредит"), KeyboardButton(text="💾 Прочее")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=categories, resize_keyboard=True)