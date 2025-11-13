from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_income_sources_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с источниками доходов"""
    sources = [
        [KeyboardButton(text="💼 Зарплата"), KeyboardButton(text="💼 Фриланс")],
        [KeyboardButton(text="📈 Инвестиции"), KeyboardButton(text="🎁 Подарок")],
        [KeyboardButton(text="🔄 Возврат долга"), KeyboardButton(text="🏆 Премия")],
        [KeyboardButton(text="💸 Прочее"), KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=sources, resize_keyboard=True)