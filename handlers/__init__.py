from aiogram import Router
from .start import router as start_router
from .expenses import router as expenses_router
from .incomes import router as incomes_router
from .statistics import router as statistics_router
from .delete import router as delete_router

router = Router()
router.include_router(start_router)
router.include_router(expenses_router)
router.include_router(incomes_router)
router.include_router(statistics_router)
router.include_router(delete_router)  # Добавляем роутер удаления

__all__ = ["router"]