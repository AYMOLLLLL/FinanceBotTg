from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Income, User
from keyboards.income_sources import get_income_sources_keyboard
from keyboards.main_menu import get_main_keyboard
from keyboards.cancel import get_cancel_keyboard

router = Router()


class AddIncome(StatesGroup):
    amount = State()
    source = State()


@router.message(F.text == "💰 Добавить доход")
async def start_add_income(message: Message, state: FSMContext):
    await message.answer(
        "💰 Введите сумму дохода (только цифры):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddIncome.amount)


# Обработка отмены на любом этапе
@router.message(StateFilter(AddIncome), F.text == "❌ Отмена")
async def cancel_income(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Добавление дохода отменено",
        reply_markup=get_main_keyboard()
    )


@router.message(AddIncome.amount, F.text)
async def process_income_amount(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_income(message, state)
        return

    user_input = message.text.strip()
    cleaned = user_input.replace(' ', '').replace(',', '.')

    if cleaned.count('.') > 1:
        parts = cleaned.split('.')
        cleaned = parts[0] + '.' + ''.join(parts[1:])

    try:
        amount = float(cleaned)

        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0. Попробуйте еще раз:",
                                 reply_markup=get_cancel_keyboard())
            return

        if amount > 1_000_000_000:
            await message.answer("❌ Слишком большая сумма. Попробуйте еще раз:", reply_markup=get_cancel_keyboard())
            return

        await state.update_data(amount=amount)

        await message.answer(
            "📊 Выберите источник дохода:",
            reply_markup=get_income_sources_keyboard()
        )
        await state.set_state(AddIncome.source)

    except ValueError:
        await message.answer(
            "❌ Не могу распознать число. Примеры правильного ввода:\n"
            "• 50000\n• 50000.50\n• 50 000\n\n"
            "Попробуйте еще раз:",
            reply_markup=get_cancel_keyboard()
        )


@router.message(AddIncome.source, F.text)
async def process_income_source(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Отмена":
        await cancel_income(message, state)
        return

    data = await state.get_data()
    source = message.text

    # Проверяем и создаем пользователя если нужно
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

    # Создаем запись о доходе
    income = Income(
        amount=data['amount'],
        source=source,
        user_id=message.from_user.id
    )

    session.add(income)
    await session.commit()

    # Завершаем FSM
    await state.clear()

    await message.answer(
        f"✅ Доход успешно добавлен!\n"
        f"💰 {data['amount']} ₽ - {source}",
        reply_markup=get_main_keyboard()
    )