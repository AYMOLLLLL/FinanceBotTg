from datetime import datetime, timedelta
from sqlalchemy import select, func
from database.models import Expense, Income

# Словарь для перевода месяцев
RUSSIAN_MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}


async def get_monthly_statistics(user_id: int, session, month: datetime = None):
    """Получение статистики за месяц"""
    if month is None:
        month = datetime.now()

    # Определяем начало и конец месяца
    start_of_month = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month.month == 12:
        end_of_month = month.replace(year=month.year + 1, month=1, day=1)
    else:
        end_of_month = month.replace(month=month.month + 1, day=1)

    # Сумма доходов за месяц
    income_stmt = select(func.coalesce(func.sum(Income.amount), 0)).where(
        Income.user_id == user_id,
        Income.created_at >= start_of_month,
        Income.created_at < end_of_month
    )
    income_result = await session.execute(income_stmt)
    total_income = income_result.scalar()

    # Сумма расходов за месяц
    expense_stmt = select(func.coalesce(func.sum(Expense.amount), 0)).where(
        Expense.user_id == user_id,
        Expense.created_at >= start_of_month,
        Expense.created_at < end_of_month
    )
    expense_result = await session.execute(expense_stmt)
    total_expenses = expense_result.scalar()

    # Расходы по категориям
    categories_stmt = select(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).where(
        Expense.user_id == user_id,
        Expense.created_at >= start_of_month,
        Expense.created_at < end_of_month
    ).group_by(Expense.category)

    categories_result = await session.execute(categories_stmt)
    expenses_by_category = categories_result.all()

    # Русское название месяца
    russian_month = RUSSIAN_MONTHS.get(month.month, month.strftime('%B'))

    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': total_income - total_expenses,
        'expenses_by_category': dict(expenses_by_category),
        'month': f"{russian_month} {month.year}"
    }


async def generate_financial_advice(user_id: int, session):
    """Генерация финансовых советов на основе статистики"""
    stats = await get_monthly_statistics(user_id, session)

    advice = []

    total_income = stats['total_income']
    total_expenses = stats['total_expenses']

    if total_income == 0:
        return ["💡 Добавьте данные о доходах для получения советов"]

    # Анализ баланса
    balance = stats['balance']
    savings_rate = (balance / total_income) * 100

    if balance < 0:
        advice.append("⚠️ Вы тратите больше, чем зарабатываете! Срочно пересмотрите расходы.")
    elif savings_rate < 10:
        advice.append(f"💡 Накопления ({savings_rate:.1f}%) ниже рекомендуемых 20%")
    elif savings_rate >= 20:
        advice.append(f"✅ Отличная норма накоплений: {savings_rate:.1f}%!")
    else:
        advice.append(f"💰 Норма накоплений: {savings_rate:.1f}%")

    # Анализ по категориям расходов (от доходов!)
    for category, amount in stats['expenses_by_category'].items():
        percent_of_income = (amount / total_income) * 100

        # Правила для разных категорий
        rules = {
            '🎮 Развлечения': 15,
            '🍽️ Рестораны и кафе': 10,
            '🛍️ Покупки': 15,
            '💾 Прочее': 10
        }

        if category in rules and percent_of_income > rules[category]:
            advice.append(
                f"🎯 {category}: {percent_of_income:.1f}% доходов. "
                f"Рекомендуется до {rules[category]}%"
            )

    # Правило 50/30/20
    necessary_categories = ['🏠 Жилье', '🍎 Продукты', '🚗 Транспорт', '💊 Здоровье', '📚 Образование', '💳 Кредит']
    necessary_expenses = sum(
        stats['expenses_by_category'].get(cat, 0)
        for cat in necessary_categories
    )

    necessary_percent = (necessary_expenses / total_income) * 100

    if necessary_percent > 60:
        advice.append(f"🏠 Обязательные расходы ({necessary_percent:.1f}%) превышают рекомендуемые 50%")
    elif necessary_percent < 40 and necessary_expenses > 0:
        advice.append(f"💰 Вы хорошо контролируете обязательные расходы ({necessary_percent:.1f}%)")

    return advice