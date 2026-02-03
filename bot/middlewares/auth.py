from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.session import async_session_maker


class AuthMiddleware(BaseMiddleware):
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)
        
        if not event.from_user:
            return await handler(event, data)
        
        user_id = event.from_user.id
        
        async with async_session_maker() as session:
            user = await self._get_or_create_user(session, event)
            data["user"] = user
            data["session"] = session
        
        return await handler(event, data)
    
    async def _get_or_create_user(self, session: AsyncSession, event: Message) -> User:
        tg_user = event.from_user
        
        result = await session.execute(
            select(User).where(User.id == tg_user.id)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            user = User(
                id=tg_user.id,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                username=tg_user.username,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        return user