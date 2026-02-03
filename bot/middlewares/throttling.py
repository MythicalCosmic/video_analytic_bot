from typing import Callable, Dict, Any, Awaitable
from time import time
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    
    def __init__(self, rate_limit: float = 0.5, max_keys: int = 10000):
        self.rate_limit = rate_limit
        self.max_keys = max_keys
        self._cache: Dict[int, float] = {}
    
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
        current_time = time()
        
        if self._is_throttled(user_id, current_time):
            return None
        
        self._update_timestamp(user_id, current_time)
        
        return await handler(event, data)
    
    def _is_throttled(self, user_id: int, current_time: float) -> bool:
        last_time = self._cache.get(user_id)
        
        if last_time is None:
            return False
        
        return (current_time - last_time) < self.rate_limit
    
    def _update_timestamp(self, user_id: int, current_time: float) -> None:
        if len(self._cache) >= self.max_keys:
            self._cleanup_old_entries(current_time)
        
        self._cache[user_id] = current_time
    
    def _cleanup_old_entries(self, current_time: float) -> None:
        cutoff = current_time - (self.rate_limit * 10)
        self._cache = {
            uid: ts for uid, ts in self._cache.items()
            if ts > cutoff
        }