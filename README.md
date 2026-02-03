# Video Analytics Bot

A production-ready Telegram bot for video analytics queries with natural language processing. Built on the **Boundless-Aiogram** framework (2000+ downloads), this bot translates user questions into SQL queries and returns real-time analytics from a PostgreSQL database.

## Overview

This bot allows users to ask questions about video analytics in natural language and receive instant numerical answers. It uses an LLM (currently Llama 3.1 via Groq API, migrating to Gemini soon) to generate SQL queries from user input, executes them safely against a PostgreSQL database, and returns results directly in Telegram.

**Key Features:**
- Natural language to SQL query translation
- Rate limiting and authentication middleware
- Async/await architecture with Aiogram 3.x
- SQLAlchemy ORM with Alembic migrations
- Docker containerization for easy deployment
- Comprehensive safety checks for SQL injection prevention
- Structured project layout for maintainability
- High-performance PostgreSQL database with asyncpg driver

## Architecture

```
video-analytics-bot/
├── bot/
│   ├── handlers/          # Message and callback handlers
│   ├── middlewares/       # Throttling and authentication
│   ├── filters/           # Custom message filters
│   ├── keyboards/         # Reply and inline keyboards
│   └── states/            # FSM state definitions
├── core/
│   ├── config.py          # Environment configuration
│   └── logging.py         # Logging setup
├── database/
│   ├── models/            # SQLAlchemy models
│   └── session.py         # Database session management
├── services/
│   ├── gemini_service.py  # LLM query generation (Llama → Gemini migration)
│   └── analytics_service.py # Query execution and validation
├── scripts/
│   └── import_data.py     # Data import utilities
├── migrations/            # Alembic database migrations
├── data/                  # Sample data files
├── tests/                 # Unit tests
├── docker-compose.yml     # Docker orchestration
├── Dockerfile             # Container definition
├── Makefile               # Development commands
└── main.py                # Application entry point
```

## Technology Stack

- **Framework:** Aiogram 3.x (async Telegram bot framework)
- **Database:** PostgreSQL 15 with asyncpg driver
- **ORM:** SQLAlchemy 2.x with async support
- **Migrations:** Alembic
- **LLM API:** Groq (Llama 3.1-8B-Instant, transitioning to Gemini)
- **Containerization:** Docker & Docker Compose
- **Language:** Python 3.12

## Database Schema

### videos
Stores final video statistics:
- `id` - Video UUID
- `creator_id` - Creator identifier
- `video_created_at` - Publication timestamp
- `views_count` - Total views
- `likes_count` - Total likes
- `comments_count` - Total comments
- `reports_count` - Total reports
- `created_at` - Record creation timestamp
- `updated_at` - Record update timestamp

### video_snapshots
Hourly measurement snapshots:
- `id` - Snapshot identifier
- `video_id` - Foreign key to videos
- `views_count` - Views at snapshot time
- `likes_count` - Likes at snapshot time
- `comments_count` - Comments at snapshot time
- `reports_count` - Reports at snapshot time
- `delta_views_count` - Views gained since last snapshot
- `delta_likes_count` - Likes gained since last snapshot
- `delta_comments_count` - Comments gained since last snapshot
- `delta_reports_count` - Reports gained since last snapshot
- `created_at` - Snapshot timestamp
- `updated_at` - Record update timestamp

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Git
- Text editor for configuration

## Installation & Setup

### Method 1: Docker (Recommended)

This is the easiest and most reliable method for running the bot.

#### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/video-analytics-bot.git
cd video-analytics-bot
```

#### Step 2: Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Telegram Bot Token
# Get this from @BotFather on Telegram
BOT_TOKEN=your_bot_token_here

# Database Configuration
# Use these defaults for Docker setup
DB_HOST=localhost
DB_PORT=5432
DB_NAME=video_analytic
DB_USER=postgres
DB_PASSWORD=root

# LLM API Configuration
# Get your free API key from: https://console.groq.com
# Note: Variables are named GEMINI_* for future migration
# Currently uses Llama 3.1 via Groq API
GEMINI_API_KEY=your_groq_api_key_here
GEMINI_MODEL=llama-3.1-8b-instant

# Database Connection Pool Settings
DB_POOL_MIN_SIZE=5
DB_POOL_MAX_SIZE=20
```

#### Step 3: Start the Bot

Using Make (recommended):

```bash
make setup    # First-time setup
make prod     # Start in production mode
make logs     # View logs
```

Using Docker Compose directly:

```bash
docker compose up -d
docker compose logs -f bot
```

#### Step 4: Verify Installation

The bot will automatically:
1. Start PostgreSQL database
2. Wait for database to be healthy
3. Import sample data from `./data/videos.json`
4. Start the Telegram bot

Check the logs to confirm everything is running:

```bash
docker compose logs -f bot
```

You should see messages indicating successful database connection and bot startup.

### Method 2: Local Development

For development without Docker:

#### Step 1: Install PostgreSQL

Install PostgreSQL 15 on your system:
- **Windows:** Download from [postgresql.org](https://www.postgresql.org/download/windows/)
- **Mac:** `brew install postgresql@15`
- **Linux:** `sudo apt install postgresql-15`

Create the database:

```bash
psql -U postgres
CREATE DATABASE video_analytic;
\q
```

#### Step 2: Setup Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Configure Environment

Copy and edit `.env`:

```bash
cp .env.example .env
```

Update database configuration for local PostgreSQL:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=video_analytic
DB_USER=postgres
DB_PASSWORD=your_local_postgres_password
```

#### Step 4: Run Migrations

```bash
alembic upgrade head
```

#### Step 5: Import Sample Data

```bash
python -m scripts.import_data ./data/videos.json
```

#### Step 6: Start the Bot

```bash
python main.py
```

## Usage

Once the bot is running, open Telegram and start a conversation with your bot.

### Example Queries

**Total counts:**
- "How many videos are in the system?"
- "How many videos got more than 100,000 views?"
- "How many total likes do all videos have?"

**Date-based queries:**
- "How many videos were published in November 2025?"
- "How many videos gained views on November 28, 2025?"
- "What was the total view growth on November 27, 2025?"

**Creator-specific queries:**
- "How many videos does creator abc123 have?"
- "How many videos from creator xyz789 were published between November 1-5, 2025?"

The bot will:
1. Parse your natural language question
2. Generate a safe SQL query
3. Execute it against the database
4. Return the numerical result

## How It Works

### 1. User Input
User sends a question in natural language via Telegram.

### 2. Query Generation
The `GeminiService` (currently using Groq/Llama) translates the question into PostgreSQL SQL using:
- Detailed schema information
- Critical rules for table selection
- Date format conversion
- Safety constraints
- Example queries for context

### 3. Safety Validation
The `AnalyticsService` validates the generated query to prevent:
- SQL injection attacks
- Data modification attempts (INSERT, UPDATE, DELETE)
- Non-aggregating queries that could leak data
- Dangerous operations (DROP, TRUNCATE, etc.)

### 4. Query Execution
Safe queries are executed against PostgreSQL using asyncpg for maximum performance.

### 5. Response
The numerical result is returned to the user in Telegram.

## Middleware System

### ThrottlingMiddleware

Implements rate limiting to prevent spam and abuse:

```python
class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5, max_keys: int = 10000):
        # Default: 0.5 seconds between messages per user
```

Features:
- Per-user rate limiting
- Memory-efficient with automatic cleanup
- Configurable rate limit and cache size
- Prevents bot abuse and API overload

### AuthMiddleware

Handles user authentication and session management:

```python
class AuthMiddleware(BaseMiddleware):
    async def _get_or_create_user(self, session: AsyncSession, event: Message):
        # Automatically creates user records for new users
```

Features:
- Automatic user registration
- Database session injection
- User data persistence
- Seamless integration with handlers

## Make Commands

The Makefile provides convenient commands for common operations:

```bash
# Setup & Installation
make setup              # First-time setup
make install            # Install Python dependencies locally

# Development
make dev                # Run bot locally (no Docker)

# Docker Operations
make prod               # Start production containers
make stop               # Stop all containers
make restart            # Restart bot container
make rebuild            # Rebuild and restart
make clean              # Remove all containers and data

# Monitoring & Logs
make logs               # Show bot logs (live)
make logs-all           # Show all container logs
make status             # Show container status

# Database
make db-shell           # Open PostgreSQL shell
make db-backup          # Backup database
make db-restore         # Restore from latest backup

# Debugging
make bot-shell          # Open shell inside bot container
make test-query         # Test a query manually

# Code Quality
make format             # Format code with black
make lint               # Lint code with flake8

# Utilities
make update             # Pull latest code and restart
make security-check     # Check for exposed secrets

# Quick Actions
make quick-start        # Complete setup and start
make quick-restart      # Rebuild and show logs
make emergency-stop     # Force stop everything
```

## Database Migrations

This project uses Alembic for database schema management.

### Creating a Migration

After modifying models in `database/models/`:

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Applying Migrations

Apply all pending migrations:

```bash
alembic upgrade head
```

### Rolling Back

Rollback the last migration:

```bash
alembic downgrade -1
```

### Viewing Migration History

```bash
alembic history
alembic current
```

## Project Structure Details

### bot/
Contains all Telegram bot logic:
- **handlers/**: Message and callback query handlers
- **middlewares/**: ThrottlingMiddleware and AuthMiddleware
- **filters/**: Custom filters for message routing
- **keyboards/**: Reply and inline keyboard layouts
- **states/**: FSM state definitions for multi-step interactions

### core/
Core configuration and utilities:
- **config.py**: Environment variable management with dataclass
- **logging.py**: Centralized logging configuration

### database/
Database layer:
- **models/**: SQLAlchemy ORM models (User, Video, VideoSnapshot)
- **session.py**: Async session maker and connection management

### services/
Business logic services:
- **gemini_service.py**: LLM integration for SQL generation
- **analytics_service.py**: Query validation and execution

### scripts/
Utility scripts:
- **import_data.py**: Import videos and snapshots from JSON

### migrations/
Alembic migration files for database versioning.

## Configuration Notes

### Environment Variables

The project uses a `.env` file for configuration. Key variables:

**BOT_TOKEN**: Your Telegram bot token from @BotFather

**Database Variables**: Connection parameters
- `DB_HOST`: Database host (use `localhost` for local, automatically overridden to `db` in Docker)
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password

**LLM Variables** (named GEMINI for future migration):
- `GEMINI_API_KEY`: Groq API key for Llama access
- `GEMINI_MODEL`: Model name (currently llama-3.1-8b-instant)

**Pool Variables**: Connection pool sizing
- `DB_POOL_MIN_SIZE`: Minimum pool connections
- `DB_POOL_MAX_SIZE`: Maximum pool connections

### Docker Override Behavior

When running in Docker, the following environment variables are automatically overridden:
- `DB_HOST` → `db` (Docker service name)
- `DATABASE_URL` → Uses `db` as hostname
- `ASYNCPG_DSN` → Uses `db` as hostname

This is handled in `docker-compose.yml` and `core/config.py` uses `override=False` to respect Docker's environment variables.

## Troubleshooting

### Bot Can't Connect to Database

**Symptom:** Error `[Errno 111] Connect call failed`

**Solution:**
1. Verify Docker containers are running: `docker compose ps`
2. Check database is healthy: `docker compose logs db`
3. Restart containers: `docker compose restart`
4. If persists, clean restart: `docker compose down && docker compose up -d`

### LLM Service Errors

**Symptom:** `AI API error: 401` or `AI API error: 429`

**Solution:**
1. Verify your Groq API key in `.env`
2. Check rate limits at console.groq.com
3. Ensure `GEMINI_API_KEY` is set correctly
4. Restart bot: `make restart`

### Database Migration Errors

**Symptom:** Alembic errors during `upgrade head`

**Solution:**
1. Check current migration state: `alembic current`
2. View migration history: `alembic history`
3. If corrupted, restore from backup: `make db-restore`
4. Or clean reset: `make clean && make setup`

### Import Data Fails

**Symptom:** Error during `import_data` script

**Solution:**
1. Verify `./data/videos.json` exists
2. Check JSON format is valid
3. Ensure database is accessible
4. Try manual import: `docker compose exec bot python -m scripts.import_data ./data/videos.json`

### Permission Denied on entrypoint.sh

**Symptom:** Docker can't execute entrypoint script

**Solution:**
```bash
chmod +x entrypoint.sh
docker compose build bot
docker compose up -d
```

## Performance Optimization

### Database Indexing

Key indexes for optimal query performance:
- `videos.creator_id` - Creator filtering
- `videos.video_created_at` - Date range queries
- `video_snapshots.video_id` - Snapshot joins
- `video_snapshots.created_at` - Date-based analytics

### Connection Pooling

Adjust pool sizes in `.env` based on load:
- Small bot (<100 users): `MIN=5, MAX=20`
- Medium bot (100-1000 users): `MIN=10, MAX=50`
- Large bot (>1000 users): `MIN=20, MAX=100`

### LLM Response Time

The Groq API with Llama 3.1-8B typically responds in 200-500ms. For better performance:
- Use faster models if needed
- Cache common queries (not implemented yet)
- Consider local LLM deployment for high volume

## Security Considerations

### SQL Injection Prevention

Multiple layers of protection:
1. **Query validation**: Checks for dangerous keywords
2. **Parameterized queries**: Uses asyncpg safely
3. **Read-only queries**: Only SELECT allowed
4. **Single value return**: Aggregates only

### API Key Security

**Never commit `.env` to version control!**

The `.gitignore` includes `.env` by default. Verify with:
```bash
make security-check
```

### Rate Limiting

ThrottlingMiddleware prevents abuse:
- Default: 0.5 seconds between messages
- Configurable per deployment
- Memory-efficient cleanup

## Future Enhancements

### Planned Features

1. **Gemini Migration**: Switch from Llama to Google Gemini API
2. **Query Caching**: Redis integration for common queries
3. **Advanced Analytics**: Multi-metric queries, aggregations
4. **Visualization**: Chart generation for trends
5. **Admin Panel**: Web interface for monitoring
6. **Multi-language**: i18n support for questions and responses
7. **Query History**: Per-user query logging
8. **Custom Dashboards**: Saved query templates

### Contributing

This project is built on the Boundless-Aiogram framework. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests if applicable
5. Submit a pull request

## License

MIT License

Copyright (c) 2025 Video Analytics Bot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Acknowledgments

- Built with [Boundless-Aiogram](https://github.com/yourusername/boundless-aiogram) (2000+ downloads)
- Powered by [Aiogram 3.x](https://github.com/aiogram/aiogram)
- Database by [PostgreSQL](https://www.postgresql.org/)
- LLM by [Groq](https://groq.com/)

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**Built with Python 3.12 | Aiogram 3.x | PostgreSQL 15 | Docker**