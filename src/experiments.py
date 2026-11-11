import json
import os
import re
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from src.rag_core import clean_text

# 1. Загружаем датасет вопросов
def load_questions():
    with open("data/eval_questions.json", "r", encoding="utf-8") as f:
        return json.load(f)

# 2. Загружаем и чистим текст PDF
def load_pdf_text(path="data/document.pdf"):
    reader = PdfReader(path)
    full_text = ""
    for page in reader.pages:
        full_text += (page.extract_text() or "") + "\n"
    return clean_text(full_text)

# 3. Нарезка на чанки с заданными параметрами
def chunk_text(text, chunk_size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

# 4. Основная функция эксперимента
def run_experiment(chunk_size, overlap, model_name="all-MiniLM-L6-v2"):
    print(f"\n--- Тест: chunk_size={chunk_size}, overlap={overlap}, модель={model_name} ---")
    
    text = load_pdf_text()
    chunks = chunk_text(text, chunk_size, overlap)
    print(f"Получено чанков: {len(chunks)}")
    
    # Инициализируем модель эмбеддингов (скачается при первом запуске)
    embedder = SentenceTransformer(model_name)
    
    # Создаем временную векторную базу в памяти
    client = chromadb.Client()
    # Удаляем старую коллекцию, если есть, чтобы не было конфликтов
    try:
        client.delete_collection("exp_docs")
    except:
        pass
    collection = client.create_collection("exp_docs")
    
    # Векторизуем чанки
    embeddings = embedder.encode(chunks).tolist()
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[str(i) for i in range(len(chunks))]
    )
    
    # Загружаем вопросы
    questions = load_questions()
    
    hits = 0
    total = 0
    
    for q in questions:
        if q.get("reference_answer") == "НЕТ_ОТВЕТА":
            continue # Пропускаем вопросы, которых нет в документе, для Hit Rate
            
        total += 1
        # Векторизуем вопрос
        q_emb = embedder.encode([q["question"]]).tolist()
        
        # Ищем топ-3 чанка
        results = collection.query(query_embeddings=q_emb, n_results=3)
        retrieved_chunks = results["documents"][0]
        
        # Проверяем, есть ли правильный ответ в найденных чанках
        found = False
        ref_words = set(re.findall(r'\w+', q["reference_answer"].lower()))
        
        for chunk in retrieved_chunks:
            chunk_words = set(re.findall(r'\w+', chunk.lower()))
            intersection = ref_words.intersection(chunk_words)
            if len(intersection) >= len(ref_words) * 0.5: 
                found = True
                break
                
        if found:
            hits += 1
            
    hit_rate = hits / total if total > 0 else 0
    print(f"Hit Rate@3: {hit_rate:.2%} ({hits}/{total})")
    return hit_rate

if __name__ == "__main__":
    # Сетка конфигураций для теста
    configs = [
        {"size": 300, "overlap": 50},
        {"size": 500, "overlap": 50},
        {"size": 800, "overlap": 100},
        {"size": 1000, "overlap": 200},
    ]
    
    results = {}
    for cfg in configs:
        hr = run_experiment(cfg["size"], cfg["overlap"])
        results[f"size={cfg['size']}, overlap={cfg['overlap']}"] = hr
        
    print("\n=== ИТОГОВАЯ ТАБЛИЦА ===")
    for name, hr in results.items():
        print(f"{name}: {hr:.2%}")
