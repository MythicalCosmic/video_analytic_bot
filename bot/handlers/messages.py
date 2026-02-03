from aiogram import Router, F
from aiogram.types import Message

from services.analytics_service import analytics_service

router = Router()


@router.message(F.text)
async def handle_question(message: Message) -> None:
    question = message.text.strip()
    
    if not question:
        return
    
    result, error = await analytics_service.process_question(question)
    
    if error:
        await message.answer(f"Error: {error}")
        return
    
    await message.answer(str(result))