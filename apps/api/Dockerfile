FROM ghcr.io/astral-sh/uv:python3.12-bookworm
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages/ packages/
COPY apps/api/ apps/api/
RUN uv sync --frozen --no-dev
CMD ["uv", "run", "uvicorn", "inndxd_api.main:app", "--host", "0.0.0.0", "--port", "8000"]