import os
import requests
from dotenv import load_dotenv

load_dotenv()

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

def chunk_text(text, chunk_size=500, overlap=50):
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size-overlap)]
    return chunks

def retrieve(question, chunks, k=3):
    # Простая заглушка: берем первые k кусков и склеиваем в одну строку
    selected_chunks = chunks[:k]
    return "\n\n".join(selected_chunks)

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
    
    # Выводим ответ Яндекса в терминал для отладки
    print("\n--- ОТВЕТ ОТ ЯНДЕКСА ---")
    print("Статус:", response.status_code)
    print("Текст:", response.text)
    print("-------------------------\n")
    
    # Если Яндекс вернул ошибку (не 200), выбрасываем исключение
    if response.status_code != 200:
        raise ValueError(f"Ошибка Yandex API: {response.text}")

    # Извлекаем ответ
    try:
        return response.json()["result"]["alternatives"][0]["message"]["text"]
    except KeyError:
        raise ValueError(f"Странный ответ от Яндекса: {response.text}")