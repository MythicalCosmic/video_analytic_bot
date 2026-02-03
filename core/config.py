"""
Configuration management
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv(override=True)

@dataclass
class Config:
    """Bot configuration"""
    bot_token: str
    database_url: str
    admin_ids: list[int]
    
    # Database settings
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    
    # Gemini LLM
    gemini_api_key: str
    gemini_model: str
    
    # Pool settings
    db_pool_min_size: int
    db_pool_max_size: int
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", "5432"))
        db_name = os.getenv("DB_NAME", "video_analytic")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        
        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot_database.db"),
            admin_ids=[int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id],
            
            # Database
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            db_user=db_user,
            db_password=db_password,
            
            # Gemini
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            
            # Pool
            db_pool_min_size=int(os.getenv("DB_POOL_MIN_SIZE", "5")),
            db_pool_max_size=int(os.getenv("DB_POOL_MAX_SIZE", "20")),
        )
    
    @property
    def async_database_url(self) -> str:
        """Async database URL for SQLAlchemy"""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def asyncpg_dsn(self) -> str:
        """DSN for raw asyncpg connections (fastest)"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


config = Config.from_env()