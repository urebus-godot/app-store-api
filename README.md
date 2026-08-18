# 🚀 App Store API

[![FastAPI](https://shields.io)](https://fastapi.tiangolo.com/)
[![Python](https://shields.io)](https://python.org)
[![Docker](https://shields.io)](https://docker.com)
[![PostgreSQL](https://shields.io)](https://postgresql.org)

**RESTful API интернет магазина для покупки и выкладывания программного обеспечения**

---

## 🛠️ Технологический стек

* **Бэкенд:** Python 3.13, FastAPI, Pydantic v2
* **База данных & ORM:** PostgreSQL, SQLModel, Alembic (миграции)
* **Кэширование:** Redis,
* **Фоновые задачи:** Celery,
* **Тестирование:** Pytest, HTTPX
* **DevOps & Окружение:** Docker, Docker Compose, GitHub Actions (CI/CD)
* **Авторизация:** JWT (JSON Web Tokens), OAuth2

---

## ✨ Ключевые фичи (Features)

* 🔐 **Аутентификация:** авторизация по JWT (access/refresh токены) с ролями.
* ⚡ **Асинхронность:** асинхронность.
* 📦 **Фоновые задачи:** вынос тяжелых операций (отправка писем, генерация отчетов) в Celery воркеры.
* 🗄️ **Кэширование данных:** оптимизация частых GET-запросов с помощью кэширования в Redis.
* 🛠️ **Валидация:** строгая валидация входящих данных через Pydantic.

---

## 📁 Структура проекта

Проект спроектирован по принципам <выберите ваше: Clean Architecture / Многослойная архитектура (Layered) / Паттерну Router-Service-Repository>:

```text
├── src/
│   ├── auth/                # Модуль аутентификации (роуты, схемы, сервисы)
│   ├── tasks/               # Модуль бизнес-логики (пример: задачи)
│   ├── database.py          # Инициализация БД и сессий SQLAlchemy
│   ├── config.py            # Настройки проекта (Pydantic BaseSettings)
│   └── main.py              # Точка входа в приложение FastAPI
├── migrations/              # Миграции базы данных (Alembic)
├── tests/                   # Интеграционные и юнит-тесты (Pytest)
├── .env.example             # Шаблон конфигурационных переменных
├── docker-compose.yml       # Сборка локального окружения
└── Dockerfile               # Инструкция сборки Docker-образа
```

---

## 🚀 Как запустить проект локально

### Вариант 1. Через Docker (Рекомендуемый)

Убедитесь, что у вас установлены [Docker](https://docker.com) и Docker Compose.

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com
   cd your-repo-name
   ```
2. Создайте файл окружения из шаблона:
   ```bash
   cp .env.example .env
   ```
3. Запустите контейнеры:
   ```bash
   docker-compose up -d --build
   ```
Приложение автоматически применит миграции и станет доступно по адресу `http://localhost:8000`.

### Вариант 2. Локальный запуск (Для разработки)

1. Установите зависимости (используя виртуальное окружение):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Для Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Запустите локальные СУБД PostgreSQL и Redis (или укажите свои доступы в `.env`).
3. Примените миграции Alembic:
   ```bash
   alembic upgrade head
   ```
4. Запустите сервер:
   ```bash
   uvicorn src.main:app --reload
   ```

---

## 📊 Документация API и примеры запросов

После запуска проекта интерактивная документация доступна в двух форматах:
* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

### Пример основного эндпоинта:
* `POST /api/v1/auth/login` — Получение JWT-токена.
* `GET /api/v1/tasks/` — Получение списка задач (поддерживает пагинацию и фильтрацию).

---

## 🧪 Тестирование

Для запуска тестов используется фреймворк `pytest`. Тесты изолированы и используют отдельную базу данных в Docker:

```bash
# Запуск тестов локально
pytest -v

# Запуск тестов в Docker-контейнере
docker-compose exec web pytest
```

---

## 👨‍💻 Автор

* **Ваше Имя** — *Backend Developer*
* **GitHub:** [@your_username](https://github.com)
* **Telegram:** [@your_telegram](https://t.me)
* **LinkedIn:** [Ваш Профиль](https://linkedin.com)
