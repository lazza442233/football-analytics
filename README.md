# Football Analytics

A containerized Python API for football analytics, built with FastAPI.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## getting Started

1. **Build and start the services:**

   ```bash
   docker compose up --build
   ```

2. **Access the API:**

   The API will be available at [http://localhost:8000](http://localhost:8000).
   - Health check: [http://localhost:8000/health](http://localhost:8000/health)
   - Interactive docs (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)

## Development

The project is configured with hot-reloading. Changes to files in the `src/` directory will automatically restart the server.
