#!/bin/bash

set -e

echo "Running entrypoint script"

if [ "$DJANGO_ENV" = "dev" ]; then
  echo "Environment: Development"

  echo "Performing migrations"

  python src/manage.py migrate

  echo "Starting development server"

  python src/manage.py runserver 0.0.0.0:8000
elif [ "$DJANGO_ENV" = "prod" ]; then
  echo "Environment: Production"
else
  echo "Unknown environment: $DJANGO_ENV"
  exit 
fi