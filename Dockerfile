FROM python:3.10-slim

# Устанавливаем системные зависимости, которые нужны для компиляции некоторых библиотек
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости и устанавливаем их с таймаутом побольше
COPY requirements.txt .
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r requirements.txt

# Копируем проект
COPY . .

EXPOSE 8000
EXPOSE 8501

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
