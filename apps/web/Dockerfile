FROM ghcr.io/astral-sh/uv:python3.12-bookworm
WORKDIR /app
RUN uv tool install playwright && uv run playwright install-deps && uv run playwright install chromium
COPY pyproject.toml uv.lock ./
COPY packages/ packages/
COPY apps/api/ apps/api/
COPY apps/web/ apps/web/
RUN uv sync --frozen --no-dev
CMD ["uv", "run", "uvicorn", "inndxd_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
