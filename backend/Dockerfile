FROM python:3.12 AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen

FROM base AS runtime
ENV PYTHONUNBUFFERED=1
COPY subabot/ ./subabot/
CMD ["uv", "run", "start"]
