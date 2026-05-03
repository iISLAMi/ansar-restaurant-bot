from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        'Добро пожаловать в ресторан <b>ANSAR</b>!\n\n'
        'Я бот для бронирования столиков в нашем ресторане.\n'
        'Для начало бронирования воспользуйтесь командой /book.',
        parse_mode=ParseMode.HTML
    )
