from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import get_or_create_user
from keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await get_or_create_user(message.from_user.id)
    await message.answer(
        "👋 Добро пожаловать в SMM-бот!\n\n"
        "Выберите нужную услугу из меню ниже:",
        reply_markup=main_menu(message.from_user.id),
    )