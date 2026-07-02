# App Store API
## REST API for an online store where you can purchase and upload applications and games.
This is project is written in Python using FastAPI framework. It uses PostgreSQL 16 as database and features a JWT authentication.
## Intructions to use project locally
1. Download the repository.
2. Make the project directory current.
``` bash
cd path_to_project/app_store_api
```
3. Run the command to start application.
```
uv run python -m app.main
```
4. Go by link http:127.0.0.1:8000/docs to visit the Swagger documentation or test the project using curl commands:
## Free route
``` powershell
curl.exe -X 'GET' `
  'http://127.0.0.1:8000/health' `
  -H 'accept: application/json'
```
## Protected route
``` powershell
curl.exe -X 'GET' `
  'http://127.0.0.1:8000/api/v1/users/me' `
  -H 'accept: application/json' `
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4MDNlMjY1YS1hNmE5LTQ2NjAtODljYS0wY2M5ZTM2YmQ1MDIiLCJleHAiOjE3ODI5ODYzMzEsInR5cGUiOiJhY2Nlc3MifQ.Yy2ujVR2rCjKrRGxkYu_ZdYf-WBj0g6wo4QZKd4cDuA'
```
