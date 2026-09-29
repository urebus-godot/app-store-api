# App Store API

Асинхронный backend-сервис магазина приложений и игр: публикация приложений, отзывы, обсуждения в реальном времени.

## Стек

- **Язык / фреймворк:** Python 3.11+, FastAPI (async)
- **Архитектура:** Router → Service → Repository + Unit of Work
- **БД:** PostgreSQL, SQLModel (ORM), Alembic (миграции)
- **Аутентификация:** JWT (access + refresh), refresh-токены в Redis + httponly cookies, blacklist токенов в Redis, роли (`user`, `publisher`, `admin`) в access токене
- **Хранилище файлов:** MinIO (архивы приложений/игр, изображения), presigned URL для загрузки/скачивания
- **Очереди задач:** Celery (обработка изображений), Celery Beat (ежедневная рассылка промокодов на день рождения), Celery Flower (мониторинг)
- **Кэш:** Redis (корзина с приложениями пользователя, rate limiting на Lua-скрипте)
- **Реалтайм:** WebSocket-эндпоинты для обсуждений, Redis Pub/Sub
- **Обратный прокси:** Nginx (HTTP/2, mkcert-сертификат)
- **Инфраструктура:** Docker Compose
- **CI/CD:** тесты, ruff (линтинг), сборка и пуш образа
- **Тестирование:** pytest, покрытие 88%
- **Логирование:** структурированное, с `request_id`

## Возможности

- 🛍 Каталог приложений и игр с загрузкой файлов и изображений через presigned URL
- ⭐ Отзывы и рейтинги приложений
- 💬 Обсуждения в реальном времени (WebSocket + pub/sub)
- 🔐 JWT-аутентификация с ролями и blacklist'ом токенов
- 🛒 Корзина с кэшированием в Redis
- ⭐ Кэширование самых популярных игр в последнее время (в процессе)
- 🎁 Промокоды на пополнение баланса ко дню рождения (Celery Beat)
- 🚦 Rate limiting на основе Redis
- 📊 Мониторинг фоновых задач через Flower

## Архитектура проекта

```
├── .github/workflows       # CI/CD
├── app/
│   └── api/v1
│       └── deps.py
│───├─ base_models/         # Базовые модели SQLModel
│   ├── core/               # Конфигурация, JWT аутентификация, логирование
│   ├── db/                 # Соединение с PostgreSQL, Redis, Redis rate limiter
│   ├── middleware/         # FastAPI middleware
│   ├── models/             # Табличные модели SQLModel
│   ├── repo/               # Взаимодействие с базой данных
│   ├── schemas/            # Схемы SQLModel
│   ├── services/           # Бизнес-логика
│   ├── storage/            # Взаимодействие с хранилищем MinIO
│   ├── task_queue/         # Конфигурация Celery и задачи
│   ├── uow/                # Протокол и конкретный Unit of Work классы
│   ├── utils/              # Вспомогательные функции (работа с датами, отправка email, перевод единиц измерения)
│   ├── ws/                 # Менеджеры WebSockets соединений
│   └── main.py             # Точка входа FastAPI
├── migrations/             # Миграции Alembic
├── nginx/                  # Конфигурация Nginx
├── tests/                  # Тесты Pytest
│   ├── api/                # Тесты эндпоинтов
│   ├── unit/               # Тесты функций и разных фич
│   └── conftest.py         # Общие фикстуры
├── compose.yaml            # Сервисы для запуска API
└── compose.test.yaml       # Сервисы для тестов
```

## Быстрый старт

### Требования

- Docker и Docker Compose

### Запуск

```bash
git clone https://github.com/urebus-godot/app-store-api.git
cd app-store-api
cp .env.example .env
docker compose up --build
```

После запуска:

- API доступно на `https://localhost` (через Nginx, HTTP/2)
- Документация Swagger: `/docs`
- Flower (мониторинг Celery): `http://localhost:5555`
- MinIO веб-панель: `http://localhost:9001`

### Миграции

```bash
alembic revision -m "Что изменилось в базе данных" --autogenerate
alembic upgrade head
```

## Переменные окружения

| Переменная | Описание |
|---|---|
| `DB_URL` | адрес PostgreSQL |
| `REDIS_URL` | адрес Redis |
| `MINIO_ENDPOINT` / `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | доступ к MinIO JWT access и refresh токена ||
| `ACCESS_SECRET_KEY` / `REFRESH_SECRET_KEY` | секрет для подписи 
| `BROKER_URL` / `RESULT_BACKEND_URL` / `WORKER_DB_URL`| адрес брокер, бэкенда для хранения результатов задач, базы данных для Celery |
| `ADMIN_PASSWORD` | пароль для доступа к роли администратора |

## Тесты

```bash
pytest
```

## Линтинг

```bash
ruff check .
```

## CI/CD

Пайплайн запускает тесты (pytest) и проверку кода (ruff), затем собирает и отправляет Docker-образ в реестр при merge или push в основную ветку.
