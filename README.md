# App Store API
## API for an online store where you can purchase and upload software.
**Details:** 
Language: Python
Web framework: FastAPI
Primary database: PostgreSQL
Storage for user files: MinIO
Background tasks: Celery
Database for cache: Redis
Reverse proxy: Nginx
Containers: Docker
Library for tests: Pytest
## Intructions to use project locally
1. Download the repository.
``` bash
git clone path_to_project/app_store_api
```
3. Make the project directory current.
``` bash
cd path_to_project/app_store_api
```
3. Run the command to start application.
```
docker compose up -d
```
4. Go by link https:127.0.0.1:8000/docs to visit the Swagger UI documentation or test the project using curl commands:
### Public route
``` bash
curl -X 'GET' `
  'http://127.0.0.1:8000/health' `
  -H 'accept: application/json'
```
### Protected route
``` bash
curl.exe -X 'GET' `
  'http://127.0.0.1:8000/api/v1/users/me' `
  -H 'accept: application/json' `
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4MDNlMjY1YS1hNmE5LTQ2NjAtODljYS0wY2M5ZTM2YmQ1MDIiLCJleHAiOjE3ODI5ODYzMzEsInR5cGUiOiJhY2Nlc3MifQ.Yy2ujVR2rCjKrRGxkYu_ZdYf-WBj0g6wo4QZKd4cDuA'
```
### Testing
Run pytest tests using next command:
``` bash
python -m pytest
```
