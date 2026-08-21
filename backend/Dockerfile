FROM python:3.14-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
COPY README.md ./
COPY main.py ./
COPY src ./src
COPY tests ./tests
COPY admin.py ./admin.py

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]