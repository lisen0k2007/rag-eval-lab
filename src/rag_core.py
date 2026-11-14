import os
import re
import requests
import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Загружаем ключи из .env
load_dotenv()

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

# 1. Инициализируем клиент базы данных (наша переменная client)
client = chromadb.Client()

# 2. Инициализируем модель эмбеддингов
# Если ты качала модель вручную в папку local_model, он возьмет ее оттуда
model_path = "./local_model" if os.path.exists("./local_model") else "all-MiniLM-L6-v2"
embedder = SentenceTransformer(model_path)

def clean_text(text):
    """Убирает мусорные символы, которые иногда выдает PDF."""
    text = re.sub(r'[^\w\s\.\,\;\:\?\!\-\–\—\(\)\[\]\{\}\"\'\%\=\+\*\/\\]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def chunk_text(text, chunk_size=1000, overlap=200):
    """Режет текст на куски."""
    text = clean_text(text)
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def build_prompt(question, context):
    """Собирает промпт для нейросети."""
    return f"""Ответь на вопрос, используя ТОЛЬКО контекст ниже.
Если в контексте нет ответа — скажи "В документе нет ответа на этот вопрос".

Контекст:
{context}

Вопрос: {question}
Ответ:"""

def ask_yandexgpt(prompt):
    """Отправляет запрос к YandexGPT."""
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "x-folder-id": YANDEX_FOLDER_ID,
        "Content-Type": "application/json"
    }
    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {"temperature": 0, "maxTokens": 1000},
        "messages": [{"role": "user", "text": prompt}]
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    return response.json()["result"]["alternatives"][0]["message"]["text"]
