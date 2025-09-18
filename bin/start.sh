#!/bin/bash

set -e

echo "Starting the application container..."
echo "Environment: ${ENV:-development}"

# Add your application startup commands here
docker compose up -d \
  && while [[ "$(docker inspect --format="{{json .State.Health.Status}}" messaging-service-app | jq)" != *"healthy"* ]]; \
    do \
      echo "Waiting for application to be ready..."; \
      sleep 2; \
    done \
  && echo "Application started successfully!"
