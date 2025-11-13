from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database.models import Expense, Income
from keyboards.main_menu import get_main_keyboard
from keyboards.cancel import get_cancel_keyboard

router = Router()


class DeleteOperation(StatesGroup):
    choosing_type = State()
    confirming_delete = State()


@router.message(Command("delete"))
@router.message(F.text == "🗑️ Удалить операцию")
async def start_delete(message: Message, state: FSMContext, session: AsyncSession):
    await message.answer(
        "🗑️ <b>Удаление операции</b>\n\n"
        "📋 Последние 5 операций:\n",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )

    await show_last_for_delete(message, session, state)
    await state.set_state(DeleteOperation.choosing_type)


async def show_last_for_delete(message: Message, session: AsyncSession, state: FSMContext):
    expenses_stmt = select(Expense).where(
        Expense.user_id == message.from_user.id
    ).order_by(desc(Expense.created_at)).limit(5)

    expenses_result = await session.execute(expenses_stmt)
    last_expenses = expenses_result.scalars().all()

    incomes_stmt = select(Income).where(
        Income.user_id == message.from_user.id
    ).order_by(desc(Income.created_at)).limit(5)

    incomes_result = await session.execute(incomes_stmt)
    last_incomes = incomes_result.scalars().all()

    operations_text = ""
    operations_data = []

    for i, expense in enumerate(last_expenses, 1):
        desc_text = f" - {expense.description}" if expense.description else ""
        operations_text += f"{i}. 📤 {expense.amount:,.2f} ₽ - {expense.category}{desc_text}\n"
        operations_data.append(('expense', expense.id))

    for i, income in enumerate(last_incomes, len(last_expenses) + 1):
        operations_text += f"{i}. 💰 {income.amount:,.2f} ₽ - {income.source}\n"
        operations_data.append(('income', income.id))

    await state.update_data(operations_list=operations_data)

    if operations_text:
        await message.answer(
            f"📋 <b>Последние операции:</b>\n\n{operations_text}\n"
            f"🔢 <b>Введите номер операции для удаления:</b>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await message.answer(
            "💡 <b>Как удалить:</b>\n"
            "Просто введите цифру операции которую хотите удалить",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "📭 Операций для удаления нет",
            reply_markup=get_main_keyboard()
        )


@router.message(DeleteOperation.choosing_type, F.text == "❌ Отмена")
async def cancel_delete(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Удаление отменено",
        reply_markup=get_main_keyboard()
    )


@router.message(DeleteOperation.choosing_type, F.text)
async def process_delete_choice(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Отмена":
        await cancel_delete(message, state)
        return

    try:
        choice = int(message.text)
        data = await state.get_data()
        operations_list = data.get('operations_list', [])

        if choice < 1 or choice > len(operations_list):
            await message.answer(f"❌ Неверный номер. Введите цифру от 1 до {len(operations_list)}:")
            return

        op_type, op_id = operations_list[choice - 1]

        if op_type == 'expense':
            stmt = select(Expense).where(
                Expense.id == op_id,
                Expense.user_id == message.from_user.id
            )
        else:
            stmt = select(Income).where(
                Income.id == op_id,
                Income.user_id == message.from_user.id
            )

        result = await session.execute(stmt)
        operation = result.scalar_one_or_none()

        if not operation:
            await message.answer("❌ Операция не найдена")
            return

        await state.update_data(
            op_type=op_type,
            op_id=op_id
        )

        if op_type == 'expense':
            desc_text = f" - {operation.description}" if operation.description else ""
            op_text = f"📤 {operation.amount:,.2f} ₽ - {operation.category}{desc_text}"
        else:
            op_text = f"💰 {operation.amount:,.2f} ₽ - {operation.source}"

        await message.answer(
            f"❓ <b>Подтвердите удаление:</b>\n\n"
            f"{op_text}\n\n"
            f"Напишите <code>да</code> для подтверждения или <code>нет</code> для отмены",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(DeleteOperation.confirming_delete)

    except ValueError:
        await message.answer("❌ Введите цифру от 1 до 10:")


@router.message(DeleteOperation.confirming_delete, F.text)
async def confirm_delete(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Отмена":
        await cancel_delete(message, state)
        return

    data = await state.get_data()
    user_choice = message.text.lower()

    if user_choice == 'да':
        if data['op_type'] == 'expense':
            stmt = select(Expense).where(
                Expense.id == data['op_id'],
                Expense.user_id == message.from_user.id
            )
        else:
            stmt = select(Income).where(
                Income.id == data['op_id'],
                Income.user_id == message.from_user.id
            )

        result = await session.execute(stmt)
        operation = result.scalar_one_or_none()

        if operation:
            await session.delete(operation)
            await session.commit()

            await message.answer(
                "✅ Операция успешно удалена!",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Операция не найдена",
                reply_markup=get_main_keyboard()
            )

    elif user_choice == 'нет':
        await message.answer(
            "❌ Удаление отменено",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "❌ Напишите <code>да</code> или <code>нет</code>",
            parse_mode="HTML"
        )
        return

    await state.clear()