FROM ghcr.io/astral-sh/uv:0.13.0 AS uv

FROM python:3.14-slim AS build
COPY --from=uv /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock README.md ./
COPY subabot ./subabot
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.14-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    SUBABOT_DATABASE_URL=sqlite:////data/subabot.db \
    PATH="/app/.venv/bin:$PATH"
RUN groupadd --gid 10001 subabot && useradd --uid 10001 --gid subabot --create-home subabot \
    && mkdir /data && chown subabot:subabot /data && chmod 700 /data
COPY --from=build --chown=subabot:subabot /app/.venv /app/.venv
USER subabot
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=3)"
CMD ["uvicorn", "subabot.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
