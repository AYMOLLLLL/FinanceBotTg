from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User
from keyboards.main_menu import get_main_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """Упрощенный обработчик старта БЕЗ relationships"""
    # Просто создаем пользователя если его нет
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        session.add(user)
        await session.commit()

    welcome_text = (
        "👋 Добро пожаловать в Финансового Помощника!\n\n"
        "💡 <b>Основные возможности:</b>\n"
        "• 📥 Внесение доходов и расходов\n"
        "• 📊 Статистика за любой период\n"
        "• 💡 Персональные финансовые советы\n"
        "• 🎯 Анализ по категориям\n\n"
        "Выберите действие в меню ниже:"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обновлённая справка с быстрыми командами"""
    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"

        "🔹 <b>Основные команды:</b>\n"
        "• /start - Главное меню\n"
        "• /help - Эта справка\n"
        "• /report - Финансовый отчёт\n"
        "• /advice - Персональные советы\n"
        "• /delete - Удалить операцию\n"
        "• /last - Последние операции\n\n"

        "⚡ <b>Быстрые команды:</b>\n"
        "<code>/spent 500 такси</code> - быстро добавить расход\n"
        "<code>/spent 300 еда продукты</code> - с описанием\n"
        "<code>/spent 1000 кино</code>\n\n"

        "🎯 <b>Категории для /spent:</b>\n"
        "• еда, продукты 🍎\n"
        "• такси, транспорт 🚗\n"
        "• кино, развлечения 🎮\n"
        "• кафе, ресторан 🍽️\n"
        "• магазин, покупки 🛍️\n"
        "• здоровье, врач 💊\n"
        "• жилье, аренда 🏠\n\n"
        "• кредит, долг, заем💳"

        "💡 <b>Финансовые правила:</b>\n"
        "• 50% - обязательные расходы\n"
        "• 30% - желания и развлечения\n"
        "• 20% - накопления и инвестиции"
    )
    await message.answer(help_text, parse_mode="HTML")


@router.message(lambda message: message.text == "ℹ️ Помощь")
async def help_button(message: Message):
    await cmd_help(message)