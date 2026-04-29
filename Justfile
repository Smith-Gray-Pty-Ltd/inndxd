test:
    uv run pytest -v

lint:
    uv run ruff check .
    uv run ruff format --check .

fmt:
    uv run ruff format .

up:
    docker compose up -d

down:
    docker compose down

logs:
    docker compose logs -f

clean:
    docker compose down -v
