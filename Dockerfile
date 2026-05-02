# Используем официальный образ Python 3.12 slim как базовый для минимального размера
FROM python:3.12-slim-bookworm
# Устанавливаем системные зависимости, необходимые для компиляции и работы
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей для установки пакетов
COPY requirements.txt .

# Устанавливаем зависимости без кэша для уменьшения размера образа
RUN pip install --no-cache-dir -r requirements.txt

# СОЗДАЕМ ДИРЕКТОРИЮ ДЛЯ СТАТИЧЕСКИХ ФАЙЛОВ
RUN mkdir -p /app/static/images

# Создаем не-root пользователя
RUN useradd -m -u 1000 appuser

# Устанавливаем владельца для статических файлов
RUN chown -R appuser:appuser /app/static

USER appuser

# Копируем весь код проекта в контейнер (включая статические файлы)
COPY --chown=appuser:appuser . .

# Указываем команду по умолчанию для запуска FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]