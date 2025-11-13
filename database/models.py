from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger, Text
from sqlalchemy.sql import func
from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(BigInteger, nullable=False)

class Income(Base):
    __tablename__ = "incomes"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    source = Column(String(100), default="Основной доход")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(BigInteger, nullable=False)
