FROM python:3.12-slim-bookworm

WORKDIR /workspace

# Install system dependencies required for native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration and source code needed for editable package installation
COPY pyproject.toml .
COPY src src

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[dev]"

# Copy migration configuration, migrations, and tests
COPY alembic.ini .
COPY alembic alembic
COPY tests tests

ENV PYTHONPATH=/workspace/src
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
