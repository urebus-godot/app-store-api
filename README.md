# [App Store API]
REST API for an online store where you can purchase and upload applications and games.
## Intructions to use project locally
1. Download repository
2. Make the project directory current
``` bash
cd path_to_project/app_store_api
```
3. Run the command to start application
```
uvicorn app.main:app --host 0.0.0.0 --port --8000
```
4. Visit Swagger UI documetation for API via this link http:127.0.0.1:8000/docs