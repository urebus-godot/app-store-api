# App Store API
RESTful API for an online store of computer software. It is designed to publish and purchase games and applications.

---

## Technology stack:
- Programming language: **Python 3.13**
- Framework: **FastAPI**
- ORM: **SQLModel** + **SQLAlchemy**
- Database: **PostgreSQL 16**
- DB migrations: **Alembic**
- Cache: **Redis**
- Task queue: **Celery**
- Testing: **Pytest**
- Linting: **Ruff**
- Reverse proxy: **Nginx**
- Containerization: **Docker** & **Docker Compose**
- Package Manager: **UV**

---

## Features:
- Fully asynchronous code
- JWT authorization with short-lived access tokens and refresh tokens stored in Redis
- CI/CD pipeline with testing, linting and image building
- HTTP/2 and HTTPS support using Nginx
- MinIO S3 for storing user-uploaded files with signed URLs
- Service/Repository pattern + UOW
- Multi-stage Docker image building
- Sending email notifications in FastAPI BackgroundTasks and image processing in Celery tasks
- Celery Beat for periodic tasks
- Rate limiting using Redis
---

## 📂 Project structure

```text
├── .github/workflows     # CI/CD
├── app/                  # App code
│   ├── api/              # Endpoints, routers, FastAPI dependency injection
│   ├── base_models/      # Base SQLModel models
│   ├── core/             # Configuration, security, logging
│   ├── db/               # PostgreSQL and Redis connections and configuration
│   ├── dependencies/     # Code of dependencies (Rate Limiter)
│   ├── middleware/       # FastAPI middleware
│   ├── models/           # SQLModel db models
│   ├── schemas/          # SQLModel schemas
│   ├── service/          # Business logic
│   ├── repo/             # Interaction with the db
│   ├── uow/              # Unit of Work class
│   ├── utils/            # Utility functions (datetime, size units conversion, email sending)
│   ├── storage/          # Interaction with MinIO S3 storage
│   ├── task_queue/       # Celery configuration and tasks
│   ├── ws/               # WebSockets connection managers
│   └── main.py           # FastAPI entry point
├── migrations/           # Alembic migrations
├── nginx/                # Nginx configuration
├── tests/                # Pytest tests
│   ├── api/              # Endpoints tests
│   ├── unit/             # Function and rate limiter tests
│   └── conftest.py       # General fixtures
├── .dockerignore         # Files and directories not included in Docker images
├── .env.example          # Environment variable examples from .env file
├── compose.yaml          # Docker containers to launch the project
├── compose.test.yaml     # Docker containers for tests
├── Dockerfile            # Image build instructions
├── pyproject.toml        # Project configuration and dependencies
└── uv.lock               # Project dependencies with fixed versions
```

---

## Instructions to use project locally
1. Download the repository.
``` bash
git clone https://github.com/urebus-godot/app-store-api.git
```
2. Make the project directory the current directory.
``` bash
cd /path_to_project/app_store_api
```
3. Run the command to start application (this requires Docker Compose to be installed on the machine).
``` bash
docker compose up --build
```
4. Visit a documentation or test the project using curl commands.
* Swagger UI: [https://localhost/docs](https://localhost/docs)
* ReDoc: [https://localhost/redoc](https://localhost/redoc)

---

### Open route
``` bash
curl -X 'GET' \
  'https://localhost/health' \
  -H 'accept: application/json'
```
### Protected route
``` bash
curl -X 'GET' \
  'https://127.0.0.1/api/v1/users/me' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer user-access-token'
```
### Install packages and activate virtual environment
``` bash
uv sync --locked
```
Linux:
``` bash
source /path/to/project/.venv/bin/activate
```
Windows:
``` bash
/path/to/project/.venv/Scripts/Activate.ps1
```
### Testing
Run pytest tests:
``` bash
docker compose -f compose.test.yaml up -d
pytest
```
### Linting
Run the linter:
``` bash
ruff check
```
### Migrations
Run the database migrations:
``` bash
alembic revision -m "Changes of this migration" --autogenerate
alembic upgrade head
```
