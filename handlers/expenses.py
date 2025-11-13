from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Expense, User
from keyboards.categories import get_categories_keyboard
from keyboards.description import get_description_keyboard
from keyboards.main_menu import get_main_keyboard
from keyboards.cancel import get_cancel_keyboard

router = Router()


class AddExpense(StatesGroup):
    amount = State()
    category = State()
    description = State()


@router.message(F.text == "📥 Добавить расход")
async def start_add_expense(message: Message, state: FSMContext):
    await message.answer(
        "💸 Введите сумму расхода (только цифры):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddExpense.amount)


# Обработка отмены на любом этапе
@router.message(StateFilter(AddExpense), F.text == "❌ Отмена")
async def cancel_expense(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Добавление расхода отменено",
        reply_markup=get_main_keyboard()
    )


@router.message(AddExpense.amount, F.text != "❌ Отмена")
async def process_amount(message: Message, state: FSMContext):


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
            "📂 Выберите категорию:",
            reply_markup=get_categories_keyboard()
        )
        await state.set_state(AddExpense.category)

    except ValueError:
        await message.answer(
            "❌ Не могу распознать число. Примеры правильного ввода:\n"
            "• 1000\n• 1000.50\n• 1000,50\n• 1 000\n\n"
            "Попробуйте еще раз:",
            reply_markup=get_cancel_keyboard()
        )


@router.message(AddExpense.category, F.text != "❌ Отмена")
async def process_category(message: Message, state: FSMContext):


    # Проверяем, что выбранная категория есть в списке
    category_text = message.text
    valid_categories = ["🏠 Жилье", "🍎 Продукты", "🚗 Транспорт", "💊 Здоровье",
                        "🎮 Развлечения", "🛍️ Покупки", "✈️ Путешествия", "📚 Образование", "💳 Кредит", "💾 Прочее"]

    if category_text not in valid_categories:
        await message.answer("❌ Пожалуйста, выберите категорию из списка:", reply_markup=get_categories_keyboard())
        return

    await state.update_data(category=category_text)
    data = await state.get_data()

    await message.answer(
        f"💰 Сумма: {data['amount']} ₽\n"
        f"📂 Категория: {category_text}\n\n"
        "✏️ Введите описание (или нажмите 'Пропустить'):",
        reply_markup=get_description_keyboard()
    )
    await state.set_state(AddExpense.description)


@router.message(AddExpense.description, F.text != "❌ Отмена")
async def process_description(message: Message, state: FSMContext, session: AsyncSession):

    data = await state.get_data()
    description_text = message.text

    # Если пользователь ввел "Пропустить", то описание будет None
    if description_text == "Пропустить":
        description_text = None

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

    # Создаем запись о расходе
    expense = Expense(
        amount=data['amount'],
        category=data['category'],
        description=description_text,
        user_id=message.from_user.id
    )

    session.add(expense)
    await session.commit()

    # Завершаем FSM
    await state.clear()

    await message.answer(
        f"✅ Расход успешно добавлен!\n"
        f"💸 {data['amount']} ₽ - {data['category']}\n"
        f"📝 {description_text if description_text else 'Без описания'}",
        reply_markup=get_main_keyboard()
    )


# Быстрое добавление расхода командой /spent
@router.message(Command("spent"))
async def quick_add_expense(message: Message, session: AsyncSession):
    """Быстрое добавление расхода: /spent 500 такси"""
    try:
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            await message.answer(
                "💸 <b>Формат быстрой команды:</b>\n"
                "<code>/spent [сумма] [категория] (описание)</code>\n\n"
                "📝 <b>Примеры:</b>\n"
                "<code>/spent 500 такси</code>\n"
                "<code>/spent 300 еда продукты на неделю</code>\n"
                "<code>/spent 1000 кино с друзьями</code>",
                parse_mode="HTML"
            )
            return

        amount = float(parts[1].replace(',', '.'))
        category_text = parts[2].lower()

        # Автоматическое определение категории
        category_map = {
            'еда': '🍎 Продукты',
            'продукты': '🍎 Продукты',
            'такси': '🚗 Транспорт',
            'транспорт': '🚗 Транспорт',
            'бензин': '🚗 Транспорт',
            'метро': '🚗 Транспорт',
            'кино': '🎮 Развлечения',
            'развлечения': '🎮 Развлечения',
            'кафе': '🎮 Развлечения',
            'ресторан': '🎮 Развлечения',
            'кофе': '🎮 Развлечения',
            'магазин': '🛍️ Покупки',
            'покупки': '🛍️ Покупки',
            'одежда': '🛍️ Покупки',
            'здоровье': '💊 Здоровье',
            'лекарства': '💊 Здоровье',
            'врач': '💊 Здоровье',
            'жилье': '🏠 Жилье',
            'коммуналка': '🏠 Жилье',
            'аренда': '🏠 Жилье',
            'ипотека': '🏠 Жилье',
            'кредит': '💳 Кредит',
            'долг': '💳 Кредит',
            'заем': '💳 Кредит'
        }

        category = category_map.get(category_text, f"💾 {category_text.title()}")
        description = parts[3] if len(parts) > 3 else None

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

        # Создаем запись о расходе
        expense = Expense(
            amount=amount,
            category=category,
            description=description,
            user_id=message.from_user.id
        )

        session.add(expense)
        await session.commit()

        await message.answer(
            f"✅ <b>Расход добавлен!</b>\n"
            f"💸 {amount:,.2f} ₽ - {category}\n"
            f"📝 {description if description else 'Без описания'}",
            parse_mode="HTML"
        )

    except ValueError:
        await message.answer("❌ Ошибка в сумме. Пример: <code>/spent 500 такси</code>", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")