from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    #used translator for this btw :)
    await message.answer(
        "Привет! Я бот для аналитики видео.\n\n"
        "Задайте вопрос на русском языке, например:\n"
        "• Сколько всего видео в системе?\n"
        "• Сколько видео набрало больше 100000 просмотров?\n"
        "• На сколько просмотров выросли видео 28 ноября 2025?"
    )
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message"
    )
