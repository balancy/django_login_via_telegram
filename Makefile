all: dev

dev:
	@docker compose up -d --build --remove-orphans

down:
	@docker compose down

lint:
	@uv run ruff check django_app
	@uv run ruff check bot

superuser:
	@docker exec -it django_app python src/manage.py createsuperuser

delete-unused-tokens:
	@docker exec -it django_app python src/manage.py delete_unused_tokens