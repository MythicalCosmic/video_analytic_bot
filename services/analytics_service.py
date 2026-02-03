from typing import Optional, Tuple
import asyncpg

from core.config import config
from services.gemini_service import gemini_service


class AnalyticsService:
    
    async def process_question(self, question: str) -> Tuple[Optional[int], Optional[str]]:
        try:
            sql = await gemini_service.generate_sql(question)
            
            if not sql:
                return None, "Не удалось сгенерировать SQL запрос"
            
            if not self._is_safe_query(sql):
                return None, "Запрос содержит недопустимые операции"
            
            result = await self._execute_query(sql)
            
            return result, None
            
        except asyncpg.PostgresError as e:
            return None, f"Ошибка базы данных: {str(e)}"
        except Exception as e:
            return None, f"Ошибка: {str(e)}"
    
    def _is_safe_query(self, sql: str) -> bool:
        sql_upper = sql.upper()
        
        dangerous_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
            "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE",
            "INTO", "SET", "MERGE"
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False
        
        if not sql_upper.strip().startswith("SELECT"):
            return False
        
        return True
    
    async def _execute_query(self, sql: str) -> Optional[int]:
        conn = await asyncpg.connect(dsn=config.asyncpg_dsn)
        
        try:
            result = await conn.fetchval(sql)
            
            if result is None:
                return 0
            
            return int(result)
            
        finally:
            await conn.close()


analytics_service = AnalyticsService()