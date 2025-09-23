SHELL          := /bin/bash
DOCKER         := $(shell which docker)
DOCKER_COMPOSE := $(shell which docker-compose 2>/dev/null || echo `which docker` compose)

.PHONY: setup run test test-remote clean help db-up db-down db-logs db-shell

help:
	@echo "Available commands:"
	@echo "  setup       - Set up the project environment and start database"
	@echo "  run         - Run the application"
	@echo "  test        - Run tests"
	@echo "  test-remote - Run tests in a remote environment"
	@echo "  clean       - Clean up temporary files and stop containers"
	@echo "  deploy      - Deploy the application helm chart"
	@echo "  db-up       - Start the PostgreSQL database"
	@echo "  db-down     - Stop the PostgreSQL database"
	@echo "  db-logs     - Show database logs"
	@echo "  db-shell    - Connect to the database shell"
	@echo "  help        - Show this help message"

setup:
	@echo "Setting up the project..."
	@echo "Starting PostgreSQL database..."
	@${DOCKER_COMPOSE} up postgres -d
	@while ! ${DOCKER} exec messaging-service-db pg_isready -U messaging_user -d messaging_service >/dev/null 2>&1; \
	do \
		if ! ${DOCKER} ps | grep messaging-service-db >/dev/null 2>&1; then \
			echo "Database container is not running. Check the container logs."; \
			exit 1; \
		fi; \
		echo "Waiting for database to be ready..."; \
		sleep 2; \
	done
	@echo "Setup complete!"

run: setup
	@echo "Running the application..."
	@./bin/start.sh

test: run
	@echo "Running tests..."
	@echo "Running test script..."
	@./bin/test.sh

test-remote: run
	@echo "Running tests..."
	@echo "Running test script..."
	@./bin/test-remote.sh

clean:
	@echo "Cleaning up..."
	@echo "Stopping and removing containers..."
	@${DOCKER_COMPOSE} down -v
	@echo "Removing any temporary files..."
	@rm -rf *.log *.tmp

deploy:
	@echo "Deploying the application helm chart..."
	@helm upgrade --install messaging-service-app ./helm/ --namespace messaging-service --create-namespace

db-up:
	@echo "Starting PostgreSQL database..."
	@${DOCKER_COMPOSE} up postgres -d

db-down:
	@echo "Stopping PostgreSQL database..."
	@${DOCKER_COMPOSE} down postgres

db-logs:
	@echo "Showing database logs..."
	@${DOCKER_COMPOSE} logs -f postgres

db-shell:
	@echo "Connecting to database shell..."
	@${DOCKER_COMPOSE} exec postgres psql -U messaging_user -d messaging_service
