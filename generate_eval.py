import json
import os
import requests
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")

def ask_yandexgpt(prompt):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "x-folder-id": YANDEX_FOLDER_ID,
        "Content-Type": "application/json"
    }
    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {"temperature": 0.3, "maxTokens": 2000},
        "messages": [{"role": "user", "text": prompt}]
    }
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code != 200:
        print("Ошибка API:", response.text)
        return None
    return response.json()["result"]["alternatives"][0]["message"]["text"]

# Читаем первые 3 страницы твоего PDF
pdf_path = "data/document.pdf"
reader = PdfReader(pdf_path)
text = ""
for i in range(min(3, len(reader.pages))):
    text += reader.pages[i].extract_text() + "\n"

prompt = f"""
Прочитай текст методички ниже. Придумай по нему 16 вопросов и ответов (строго по тексту).
А также придумай 4 вопроса, ответов на которые в тексте НЕТ (например, про погоду или другие науки).
Верни ответ СТРОГО в формате JSON-массива, без лишних слов. 
Формат каждого элемента:
{{
  "id": 1,
  "question": "Текст вопроса",
  "reference_answer": "Текст ответа (или НЕТ_ОТВЕТА)",
  "source_page": 1
}}

Текст методички:
{text[:5000]}
"""

print("Генерирую вопросы, подожди 10-20 секунд...")
result = ask_yandexgpt(prompt)

if result:
    # Очищаем ответ от возможных markdown-тегов
    result = result.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(result)
        with open("data/eval_questions.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("УСПЕХ! Файл data/eval_questions.json создан. В нём 20 вопросов.")
    except Exception as e:
        print("Не удалось распарсить JSON. Вот что ответила нейросеть:\n", result)
