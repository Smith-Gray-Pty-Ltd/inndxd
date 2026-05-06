FROM ghcr.io/astral-sh/uv:python3.12-bookworm
WORKDIR /app

RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean

COPY apps/web/package.json apps/web/package-lock.json apps/web/
RUN cd apps/web && npm install

COPY pyproject.toml uv.lock ./
COPY packages/ packages/
COPY apps/web/ apps/web/
RUN cd apps/web && npm run build:css && cd /app && uv sync --frozen --no-dev

CMD ["uv", "run", "uvicorn", "inndxd_web.main:app", "--host", "0.0.0.0", "--port", "8080"]
