# Football Analytics Platform

A high-performance analytics engine for modern football data.

## Tech Stack
- **Python 3.12**
- **FastAPI**
- **Docker**
- **PostgreSQL**

## How to start this locally

1. **Build and run the container:**
   ```bash
   docker compose up --build
   ```

2. **Access the API:**
   - **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
   - **Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

## Development workflow

- **Tests:** Run `poetry run pytest`
- **Linting:** Run `poetry run ruff check .`
