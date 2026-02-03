.PHONY: help setup dev prod logs stop clean restart rebuild status test db-shell bot-shell format lint install update

# Colors for pretty output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
RESET  := \033[0m

##@ General

help: ## 📚 Show this help message
	@echo "$(GREEN)Video Analytics Bot - Command Reference$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(YELLOW)<target>$(RESET)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(YELLOW)%-15s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(GREEN)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Installation

setup: ## 🚀 First-time setup (creates .env, installs deps, starts bot)
	@echo "$(GREEN)Setting up Video Analytics Bot...$(RESET)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env file...$(RESET)"; \
		cp .env.example .env 2>/dev/null || echo "$(RED)Warning: .env.example not found$(RESET)"; \
	fi
	@echo "$(GREEN)✓ Setup complete! Edit .env with your tokens, then run 'make prod'$(RESET)"

install: ## 📦 Install Python dependencies locally (for development)
	@echo "$(GREEN)Installing Python dependencies...$(RESET)"
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(RESET)"

##@ Development

dev: ## 🔧 Run bot in development mode (local Python, no Docker)
	@echo "$(GREEN)Starting bot in development mode...$(RESET)"
	python main.py

##@ Docker Operations

prod: ## 🚀 Start bot in production mode (Docker)
	@echo "$(GREEN)Starting bot in production mode...$(RESET)"
	docker compose up -d
	@echo "$(GREEN)✓ Bot is running! Check logs with 'make logs'$(RESET)"

stop: ## 🛑 Stop all containers
	@echo "$(YELLOW)Stopping containers...$(RESET)"
	docker compose down
	@echo "$(GREEN)✓ Containers stopped$(RESET)"

restart: ## 🔄 Restart bot container (keeps database running)
	@echo "$(YELLOW)Restarting bot...$(RESET)"
	docker compose restart bot
	@echo "$(GREEN)✓ Bot restarted$(RESET)"

rebuild: ## 🔨 Rebuild bot image and restart (use after code changes)
	@echo "$(YELLOW)Rebuilding bot image...$(RESET)"
	docker compose build bot
	docker compose up -d bot
	@echo "$(GREEN)✓ Bot rebuilt and restarted$(RESET)"

clean: ## 🧹 Stop containers and remove volumes (WARNING: deletes database!)
	@echo "$(RED)This will delete ALL data including the database!$(RESET)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v; \
		echo "$(GREEN)✓ Everything cleaned$(RESET)"; \
	else \
		echo "$(YELLOW)Cancelled$(RESET)"; \
	fi

##@ Monitoring & Logs

logs: ## 📋 Show bot logs (live, press Ctrl+C to exit)
	docker compose logs -f bot

logs-all: ## 📋 Show all container logs
	docker compose logs -f

status: ## 📊 Show container status
	@echo "$(GREEN)Container Status:$(RESET)"
	@docker compose ps

##@ Database

db-shell: ## 🗄️ Open PostgreSQL shell
	@echo "$(GREEN)Opening database shell...$(RESET)"
	@echo "$(YELLOW)Tip: Use \\dt to list tables, \\q to quit$(RESET)"
	docker compose exec db psql -U postgres -d video_analytic

db-backup: ## 💾 Backup database to backups/backup_YYYYMMDD_HHMMSS.sql
	@mkdir -p backups
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	echo "$(GREEN)Creating backup: backups/backup_$$TIMESTAMP.sql$(RESET)"; \
	docker compose exec -T db pg_dump -U postgres video_analytic > backups/backup_$$TIMESTAMP.sql; \
	echo "$(GREEN)✓ Backup created$(RESET)"

db-restore: ## 📥 Restore database from latest backup
	@LATEST=$$(ls -t backups/*.sql 2>/dev/null | head -n1); \
	if [ -z "$$LATEST" ]; then \
		echo "$(RED)No backups found in backups/$(RESET)"; \
		exit 1; \
	fi; \
	echo "$(YELLOW)Restoring from: $$LATEST$(RESET)"; \
	read -p "This will overwrite current database. Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose exec -T db psql -U postgres video_analytic < $$LATEST; \
		echo "$(GREEN)✓ Database restored$(RESET)"; \
	else \
		echo "$(YELLOW)Cancelled$(RESET)"; \
	fi

##@ Debugging

bot-shell: ## 🐚 Open shell inside bot container
	docker compose exec bot /bin/bash

test-query: ## 🧪 Test a query (usage: make test-query QUERY="your question")
	@if [ -z "$(QUERY)" ]; then \
		echo "$(RED)Usage: make test-query QUERY=\"your question here\"$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Testing query: $(QUERY)$(RESET)"
	docker compose exec bot python -c "import asyncio; from services.analytics_service import analytics_service; print(asyncio.run(analytics_service.process_question('$(QUERY)')))"

##@ Code Quality

format: ## ✨ Format code with black
	@echo "$(GREEN)Formatting code...$(RESET)"
	black .
	@echo "$(GREEN)✓ Code formatted$(RESET)"

lint: ## 🔍 Lint code with flake8
	@echo "$(GREEN)Linting code...$(RESET)"
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "$(GREEN)✓ Linting complete$(RESET)"

##@ Utilities

update: ## 🔄 Pull latest code and restart
	@echo "$(GREEN)Pulling latest changes...$(RESET)"
	git pull
	@echo "$(GREEN)Rebuilding and restarting...$(RESET)"
	$(MAKE) rebuild
	@echo "$(GREEN)✓ Update complete$(RESET)"

security-check: ## 🔒 Check for exposed secrets in .env
	@echo "$(GREEN)Checking for security issues...$(RESET)"
	@if grep -E "BOT_TOKEN=.*[0-9]{9}:" .env >/dev/null 2>&1; then \
		echo "$(YELLOW)⚠ Bot token found in .env (this is normal)$(RESET)"; \
	fi
	@if git ls-files --error-unmatch .env >/dev/null 2>&1; then \
		echo "$(RED)❌ DANGER: .env is tracked by git!$(RESET)"; \
		echo "$(RED)   Run: git rm --cached .env$(RESET)"; \
		exit 1; \
	else \
		echo "$(GREEN)✓ .env is not tracked by git$(RESET)"; \
	fi

##@ Quick Actions

quick-start: setup prod logs ## ⚡ Complete setup and start (for new users)

quick-restart: rebuild logs ## ⚡ Rebuild and show logs (for developers)

emergency-stop: ## 🚨 Force stop everything immediately
	@echo "$(RED)Emergency stop!$(RESET)"
	docker compose kill
	docker compose down
	@echo "$(GREEN)✓ Everything stopped$(RESET)"