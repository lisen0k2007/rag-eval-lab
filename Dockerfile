# Берем официальный образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем библиотеки (без кэша, чтобы образ был меньше)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порты для FastAPI (8000) и Streamlit (8501)
EXPOSE 8000
EXPOSE 8501

# Команда по умолчанию (запускает бэкенд)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
