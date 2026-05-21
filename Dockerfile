FROM python:3.12-slim-bookworm
# Системные зависимости для компиляции и работы
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# устанавливаем рабочую директорию внутри контейнера
WORKDIR /app
COPY requirements.txt .
# устанавливаем зависимости без кэша
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/static/images
# создаем не-root пользователя
RUN useradd -m -u 1000 appuser
# устанавливаем владельца для статических файлов
RUN chown -R appuser:appuser /app/static
USER appuser
# копируем весь код проекта в контейнер
COPY --chown=appuser:appuser . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]