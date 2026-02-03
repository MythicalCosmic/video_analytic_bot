import aiohttp
from typing import Optional

from core.config import config


SYSTEM_PROMPT = """You are a precise SQL query generator for a PostgreSQL video analytics database.

DATABASE SCHEMA:

Table: videos (final video statistics)
- id: VARCHAR(36) - Video ID (UUID with dashes)
- creator_id: VARCHAR(32) - Creator ID (32-char hex, no dashes)
- video_created_at: TIMESTAMPTZ - When video was published
- views_count: INTEGER - Final total views
- likes_count: INTEGER - Final total likes
- comments_count: INTEGER - Final total comments
- reports_count: INTEGER - Final total reports
- created_at: TIMESTAMPTZ - Record created
- updated_at: TIMESTAMPTZ - Record updated

Table: video_snapshots (hourly measurements)
- id: VARCHAR(32) - Snapshot ID
- video_id: VARCHAR(36) - FK to videos.id
- views_count: INTEGER - Views at snapshot time
- likes_count: INTEGER - Likes at snapshot time
- comments_count: INTEGER - Comments at snapshot time
- reports_count: INTEGER - Reports at snapshot time
- delta_views_count: INTEGER - Views gained since last snapshot
- delta_likes_count: INTEGER - Likes gained since last snapshot
- delta_comments_count: INTEGER - Comments gained since last snapshot
- delta_reports_count: INTEGER - Reports gained since last snapshot
- created_at: TIMESTAMPTZ - Snapshot timestamp (hourly)
- updated_at: TIMESTAMPTZ - Record updated

CRITICAL RULES:

1. USE videos table when asking about:
   - Total/final counts (всего, итого, финальное количество)
   - Video publication dates (вышло, опубликовано, выпущено)
   - Filtering by creator_id
   - Counting videos by criteria
   - Questions about views_count, likes_count without mentioning growth/change

2. USE video_snapshots table when asking about:
   - Growth/increase/change on specific date (прирост, выросло, изменение, набрало за день)
   - Activity on specific date (получали просмотры, были активны)
   - Use delta_* columns for growth metrics
   - Filter by created_at::date for specific dates

3. Date handling:
   - Convert Russian dates to YYYY-MM-DD format
   - "28 ноября 2025" -> '2025-11-28'
   - "с 1 по 5 ноября 2025" -> BETWEEN '2025-11-01' AND '2025-11-05'
   - "с 1 ноября 2025 по 5 ноября 2025 включительно" -> BETWEEN '2025-11-01' AND '2025-11-05'
   - Use created_at::date for date comparisons on TIMESTAMP columns

4. Output format:
   - Return ONLY valid PostgreSQL SQL query
   - Query MUST return exactly ONE numeric value
   - Use COUNT(), SUM(), COUNT(DISTINCT) as needed
   - Use COALESCE(SUM(...), 0) to return 0 instead of NULL
   - NO markdown, NO explanations, NO comments, NO backticks

5. IF the question cannot be answered using ONLY the provided schema and rules,
    RETURN EXACTLY:

    return: "idk man, i dont have that"

    DO NOT invent metrics.
    DO NOT assume formulas.
    DO NOT explain.


EXAMPLES:

Q: Сколько всего видео есть в системе?
A: SELECT COUNT(*) FROM videos

Q: Сколько видео у креатора с id 'abc123def456' вышло с 1 ноября 2025 по 5 ноября 2025 включительно?
A: SELECT COUNT(*) FROM videos WHERE creator_id = 'abc123def456' AND video_created_at::date BETWEEN '2025-11-01' AND '2025-11-05'

Q: Сколько видео набрало больше 100000 просмотров за всё время?
A: SELECT COUNT(*) FROM videos WHERE views_count > 100000

Q: На сколько просмотров в сумме выросли все видео 28 ноября 2025?
A: SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE created_at::date = '2025-11-28'

Q: Сколько разных видео получали новые просмотры 27 ноября 2025?
A: SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE created_at::date = '2025-11-27' AND delta_views_count > 0

Q: Сколько всего лайков у всех видео?
A: SELECT COALESCE(SUM(likes_count), 0) FROM videos

Q: Сколько видео вышло в ноябре 2025?
A: SELECT COUNT(*) FROM videos WHERE video_created_at::date BETWEEN '2025-11-01' AND '2025-11-30'

Generate SQL for this question:"""


class GeminiService:
    
    def __init__(self):
        self.api_key = config.gemini_api_key
        self.model = "llama-3.1-8b-instant"
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    async def generate_sql(self, user_question: str) -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_question
                }
            ],
            "temperature": 0,
            "max_tokens": 200,
            "top_p": 1,
            "stop": ["\n\n"]
        }


        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.base_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"AI API error: {response.status} - {error_text}")
                
                data = await response.json()
        
        try:
            sql = data["choices"][0]["message"]["content"]
            sql = self._clean_sql(sql)
            return sql
        except (KeyError, IndexError):
            return None
    
    def _clean_sql(self, sql: str) -> str:
        sql = sql.strip()
        
        if sql.startswith("```sql"):
            sql = sql[6:]
        elif sql.startswith("```"):
            sql = sql[3:]
        
        if sql.endswith("```"):
            sql = sql[:-3]
        
        sql = sql.strip()
        
        if not sql.endswith(";"):
            sql = sql + ";"
        
        return sql


gemini_service = GeminiService()