import os
import requests
from dotenv import load_dotenv

load_dotenv()

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

def chunk_text(text, chunk_size=500, overlap=50):
    # Сюда потом вставишь свой код чанкинга из блокнота
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size-overlap)]
    return chunks

def retrieve(question, chunks, k=3):
    # Сюда потом вставишь свой код поиска из блокнота
    return chunks[:k]

def build_prompt(question, context):
    return f"""Ответь на вопрос, используя ТОЛЬКО контекст ниже.
Если ответа нет — скажи "В документе нет ответа".

Контекст:
{context}

Вопрос: {question}
Ответ:"""

def ask_yandexgpt(prompt):
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
    return response.json()["result"]["alternatives"][0]["message"]["text"]
