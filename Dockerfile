# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy poetry configuration
COPY pyproject.toml poetry.lock ./

# Configure poetry to create venv in project and install dependencies
RUN poetry config virtualenvs.in-project true && \
  poetry install --only main --no-root

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv .venv

# Enable the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy source code
COPY src/ src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
