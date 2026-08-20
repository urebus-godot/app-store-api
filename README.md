# App Store API
RESTful API for an online store of computer software. It is designed to publish and purchase games and applications.
## Technology stack:
- Programming language: **Python 3.13**
- Framework: **FastAPI**
- ORM: **SQLModel** + **SQLAlchemy**
- Database: **PostgreSQL 16**
- DB migrations: **Alembic**
- Cache: **Redis**
- Task queue: **Celery**
- Testing: **Pytest**
- Linter: **Ruff**
- Reverse proxy: **Nginx**
- Containerization: **Docker** & **Docker Compose**
- Package Manager: UV
---

## 📂 Project structure

```text
├── app/                  # App code
│   ├── api/              # Endpoints, routers, dependency injection
│   ├── core/             # Configuration, security, logging
│   ├── db/               # PostgreSQL and Redis connections and configuration
│   ├── base_models/      # Base SQLModel models
│   ├── models/           # SQLModel db models
│   ├── schemas/          # SQLModel schemas
│   ├── service/          # Business logic
│   ├── repo/             # Interaction with the db
│   ├── task_queue/       # Celery configuration and tasks
│   └── main.py           # FastAPI entry point
├── migrations/           # Alembic migrations
├── tests/                # Pytest tests
├── .env.example          # Environment variables from .env file
├── compose.yaml          # Docker containers to launch the project
├── compose.test.yaml     # Docker containers for tests
├── Dockerfile            # Image build instructions
├── pyproject.toml        # Project configuration and dependencies
└── uv.lock               # Project dependencies with locked versions
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
* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
### Open route
``` bash
curl -X 'GET' \
  'https://localhost/health' \
  -H 'accept: application/json'
```
### Protected route
``` bash
curl -X 'GET' \
  'http://127.0.0.1:8000/api/v1/users/me' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer \
  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4MDNlMjY1YS1hNmE \
  5LTQ2NjAtODljYS0wY2M5ZTM2YmQ1MDIiLCJleHAiOjE3ODI5OD \
  YzMzEsInR5cGUiOiJhY2Nlc3MifQ.Yy2ujVR2rCjKrRGxkYu_ZdYf-WBj0g6wo4QZKd4cDuA'
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
