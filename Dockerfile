FROM python:3.14.3-slim

RUN pip install uv

COPY . .

CMD ["uv", "run", ""]