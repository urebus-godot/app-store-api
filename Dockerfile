FROM python:3.14.3-slim AS builder

RUN pip install uv

COPY . .

CMD ["python", "app.main:app"]