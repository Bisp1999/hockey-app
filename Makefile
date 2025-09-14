# Makefile for Hockey Pickup Manager development

.PHONY: help build up down logs shell-backend shell-frontend test clean

# Default target
help:
	@echo "Available commands:"
	@echo "  build          - Build all Docker containers"
	@echo "  up             - Start all services in development mode"
	@echo "  down           - Stop all services"
	@echo "  logs           - Show logs from all services"
	@echo "  logs-backend   - Show backend logs"
	@echo "  logs-frontend  - Show frontend logs"
	@echo "  shell-backend  - Open shell in backend container"
	@echo "  shell-frontend - Open shell in frontend container"
	@echo "  db-init        - Initialize database"
	@echo "  db-migrate     - Run database migrations"
	@echo "  test           - Run tests"
	@echo "  clean          - Clean up containers and volumes"

# Build all containers
build:
	docker-compose build

# Start development environment
up:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Stop all services
down:
	docker-compose down

# Show logs from all services
logs:
	docker-compose logs -f

# Show backend logs
logs-backend:
	docker-compose logs -f backend

# Show frontend logs
logs-frontend:
	docker-compose logs -f frontend

# Open shell in backend container
shell-backend:
	docker-compose exec backend /bin/bash

# Open shell in frontend container
shell-frontend:
	docker-compose exec frontend /bin/sh

# Initialize database
db-init:
	docker-compose exec backend python migrations/init_db.py

# Run database migrations
db-migrate:
	docker-compose exec backend flask db upgrade

# Run tests
test:
	docker-compose exec backend pytest
	docker-compose exec frontend npm test -- --coverage --watchAll=false

# Clean up containers and volumes
clean:
	docker-compose down -v
	docker system prune -f
