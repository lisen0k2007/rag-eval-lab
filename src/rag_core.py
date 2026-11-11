import os
import re
import requests
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

# Загружаем модель для векторизации (она скачается один раз при первом запуске)
# Используем ту же модель, что и в experiments.py, чтобы результаты совпадали
print("Загрузка модели эмбеддингов (подождите при первом запуске)...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def clean_text(text):
    """Убирает лишние пробелы и переносы строк"""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def chunk_text(text, chunk_size=500, overlap=50):
    """Режет текст на куски"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def retrieve(question, chunks, k=3):
    """
    Умный поиск: векторизует вопрос и чанки, 
    находит самые похожие по смыслу куски текста.
    """
    if not chunks:
        return ""
    
    # Переводим вопрос в вектор
    q_emb = embedder.encode([question])
    
    # Переводим все чанки в векторы
    # (В реальном проекте они должны кэшироваться, но для нашего теста сойдет)
    chunks_emb = embedder.encode(chunks)
    
    # Считаем косинусное сходство (от 0 до 1)
    similarities = cosine_similarity(q_emb, chunks_emb)[0]
    
    # Берем индексы топ-k самых похожих чанков
    top_k_indices = similarities.argsort()[-k:][::-1]
    
    # Собираем найденные чанки
    selected_chunks = [chunks[i] for i in top_k_indices]
    
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
    
    if response.status_code != 200:
        raise ValueError(f"Ошибка Yandex API: {response.text}")

    return response.json()["result"]["alternatives"][0]["message"]["text"]
