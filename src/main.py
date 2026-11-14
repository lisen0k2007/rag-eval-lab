from fastapi import FastAPI, HTTPException, UploadFile, File # <-- Добавь UploadFile, File
from pydantic import BaseModel
from src.rag_core import chunk_text, build_prompt, ask_yandexgpt, embedder, client # <-- Убедись, что импортируешь модель и клиент Chroma из rag_core (мы их туда переносили на Этапе 4)
import io
from pypdf import PdfReader

app = FastAPI(...)

# ... твои старые модели Pydantic ...

# Твой старый эндпоинт /load_document можно оставить, он не помешает.

# --- НОВЫЙ ЭНДПОИНТ ДЛЯ ЗАГРУЗКИ ФАЙЛА ---
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    global collection
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Пожалуйста, загрузите файл в формате PDF")
        
    # Читаем файл прямо в память, не сохраняя на диск
    pdf_bytes = await file.read()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    
    full_text = ""
    for page in reader.pages:
        full_text += (page.extract_text() or "") + "\n"
        
    # Нарезаем на чанки (используем твои лучшие параметры 1000/200)
    chunks = chunk_text(full_text, chunk_size=1000, overlap=200)
    
    # Очищаем старую базу и загружаем новые чанки
    try:
        client.delete_collection("docs")
    except:
        pass
    collection = client.create_collection("docs")
    
    # Векторизуем и добавляем
    embeddings = embedder.encode(chunks).tolist()
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[str(i) for i in range(len(chunks))]
    )
    
    return {"message": "Файл успешно загружен", "chunks_count": len(chunks)}
