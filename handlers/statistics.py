from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from services.finance_calculations import get_monthly_statistics, generate_financial_advice
from database.models import Expense, Income

router = Router()


@router.message(F.text == "📊 Статистика")
@router.message(Command("report"))
async def show_statistics(message: Message, session: AsyncSession):
    """Показать статистику за текущий месяц"""
    stats = await get_monthly_statistics(message.from_user.id, session)

    total_income = stats['total_income']
    total_expenses = stats['total_expenses']

    # Формируем текстовый отчёт
    report = f"📊 <b>Финансовый отчёт за {stats['month']}</b>\n\n"

    report += f"💰 <b>Доходы:</b> {total_income:,.2f} ₽\n"
    report += f"📤 <b>Расходы:</b> {total_expenses:,.2f} ₽\n"
    report += f"✅ <b>Баланс:</b> {stats['balance']:,.2f} ₽\n"

    if total_income > 0:
        expense_percent = (total_expenses / total_income) * 100
        savings_percent = (stats['balance'] / total_income) * 100
        report += f"📈 <b>Накопления:</b> {savings_percent:.1f}% от доходов\n\n"
    else:
        report += "\n"

    if total_income > 0:
        report += "📊 <b>Структура бюджета:</b>\n"
        for category, amount in stats['expenses_by_category'].items():
            # Считаем проценты от ДОХОДОВ!
            percentage = (amount / total_income) * 100
            report += f"• {category}: {amount:,.2f} ₽ ({percentage:.1f}% доходов)\n"

    await message.answer(report, parse_mode="HTML")


@router.message(F.text == "💡 Советы")
@router.message(Command("advice"))
async def show_advice(message: Message, session: AsyncSession):
    """Показать финансовые советы"""
    advice_list = await generate_financial_advice(message.from_user.id, session)

    if not advice_list:
        await message.answer("📊 Недостаточно данных для анализа. Добавьте несколько доходов и расходов.")
        return

    advice_text = "💡 <b>Персональные финансовые советы:</b>\n\n"

    for i, advice in enumerate(advice_list, 1):
        advice_text += f"{i}. {advice}\n"

    # Добавляем общие рекомендации
    advice_text += "\n📚 <b>Общие рекомендации:</b>\n"
    advice_text += "• Правило 50/30/20: 50% на нужды, 30% на желания, 20% на накопления\n"
    advice_text += "• Создайте финансовую подушку безопасности (3-6 месячных доходов)\n"
    advice_text += "• Регулярно отслеживайте свои финансы"

    await message.answer(advice_text, parse_mode="HTML")


@router.message(Command("last"))
@router.message(F.text == "📋 Последние операции")
async def show_last_transactions(message: Message, session: AsyncSession):
    """Показать последние 5 операций"""
    # Последние расходы
    expenses_stmt = select(Expense).where(
        Expense.user_id == message.from_user.id
    ).order_by(desc(Expense.created_at)).limit(5)

    expenses_result = await session.execute(expenses_stmt)
    last_expenses = expenses_result.scalars().all()

    # Последние доходы
    incomes_stmt = select(Income).where(
        Income.user_id == message.from_user.id
    ).order_by(desc(Income.created_at)).limit(5)

    incomes_result = await session.execute(incomes_stmt)
    last_incomes = incomes_result.scalars().all()

    # Формируем сообщение
    transactions_text = "📋 <b>Последние операции:</b>\n\n"

    if not last_expenses and not last_incomes:
        transactions_text += "📭 Операций пока нет\n"
        transactions_text += "💸 Добавьте первый расход: /spent 500 такси"
    else:
        # Объединяем и сортируем все операции по дате
        all_operations = []

        for expense in last_expenses:
            all_operations.append({
                'type': '📤',
                'amount': expense.amount,
                'category': expense.category,
                'date': expense.created_at,
                'description': expense.description
            })

        for income in last_incomes:
            all_operations.append({
                'type': '💰',
                'amount': income.amount,
                'category': income.source,
                'date': income.created_at,
                'description': None
            })

        # Сортируем по дате (новые сверху)
        all_operations.sort(key=lambda x: x['date'], reverse=True)

        # Выводим последние 5 операций
        for op in all_operations[:5]:
            date_str = op['date'].strftime("%d.%m %H:%M")
            desc_text = f" - {op['description']}" if op['description'] else ""
            transactions_text += f"{op['type']} {op['amount']:,.2f} ₽ - {op['category']}{desc_text}\n"
            transactions_text += f"<i>🕐 {date_str}</i>\n\n"

    await message.answer(transactions_text, parse_mode="HTML")