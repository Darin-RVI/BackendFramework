# Makefile for Backend Framework
# Note: For Windows PowerShell, use the commands directly or install make

.PHONY: help build up down restart logs clean ps shell-api shell-frontend shell-db

help:
	@echo "Backend Framework - Docker Commands"
	@echo ""
	@echo "Usage: make [command]"
	@echo ""
	@echo "Commands:"
	@echo "  build      - Build all Docker images"
	@echo "  up         - Start all services"
	@echo "  down       - Stop all services"
	@echo "  restart    - Restart all services"
	@echo "  logs       - View logs from all services"
	@echo "  logs-api   - View API logs"
	@echo "  logs-front - View frontend logs"
	@echo "  clean      - Stop and remove all containers, networks, volumes"
	@echo "  ps         - List running containers"
	@echo "  shell-api  - Access API container shell"
	@echo "  shell-front - Access frontend container shell"
	@echo "  shell-db   - Access PostgreSQL shell"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api nginx_api

logs-front:
	docker-compose logs -f frontend nginx_frontend

logs-db:
	docker-compose logs -f postgres

clean:
	docker-compose down -v
	docker system prune -f

ps:
	docker-compose ps

shell-api:
	docker-compose exec api bash

shell-front:
	docker-compose exec frontend bash

shell-db:
	docker-compose exec postgres psql -U postgres -d backend_db

# Development helpers
dev-api:
	docker-compose up api postgres nginx_api

dev-front:
	docker-compose up frontend nginx_frontend

test-api:
	docker-compose exec api pytest

migrate:
	docker-compose exec api flask db upgrade

migrate-create:
	docker-compose exec api flask db migrate -m "$(message)"
