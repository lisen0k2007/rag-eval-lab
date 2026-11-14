from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from src.rag_core import chunk_text, build_prompt, ask_yandexgpt, embedder, client
import io
from pypdf import PdfReader
import os

app = FastAPI(title="RAG-Eval-Lab API", description="Умный поиск по PDF")

# Глобальная переменная для хранения коллекции ChromaDB
collection = None

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    sources: list[str]

@app.get("/health")
def health():
    status = "ok" if collection is not None else "no_document_loaded"
    return {"status": "ok", "database_status": status}

@app.post("/load_document")
def load_document():
    """Загружает дефолтный PDF из папки data (для обратной совместимости)."""
    global collection
    pdf_path = "data/document.pdf"
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Файл data/document.pdf не найден")
        
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        full_text += (page.extract_text() or "") + "\n"
        
    # Используем лучшие параметры из экспериментов
    chunks = chunk_text(full_text, chunk_size=1000, overlap=200)
    
    try:
        client.delete_collection("docs")
    except:
        pass
    collection = client.create_collection("docs")
    
    embeddings = embedder.encode(chunks).tolist()
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[str(i) for i in range(len(chunks))]
    )
    
    return {"message": "Документ загружен", "chunks_count": len(chunks)}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Принимает PDF файл напрямую через интерфейс."""
    global collection
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Пожалуйста, загрузите файл в формате PDF")
        
    pdf_bytes = await file.read()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    
    full_text = ""
    for page in reader.pages:
        full_text += (page.extract_text() or "") + "\n"
        
    chunks = chunk_text(full_text, chunk_size=1000, overlap=200)
    
    try:
        client.delete_collection("docs")
    except:
        pass
    collection = client.create_collection("docs")
    
    embeddings = embedder.encode(chunks).tolist()
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[str(i) for i in range(len(chunks))]
    )
    
    return {"message": "Файл успешно загружен", "chunks_count": len(chunks)}

@app.post("/ask", response_model=AnswerResponse)
def ask(req: QuestionRequest):
    """Принимает вопрос, ищет контекст в ChromaDB и спрашивает YandexGPT."""
    global collection
    
    if collection is None:
        raise HTTPException(status_code=400, detail="Сначала загрузите документ через /upload или /load_document")
        
    # Векторизуем вопрос
    q_emb = embedder.encode([req.question]).tolist()
    
    # Ищем топ-3 чанка
    results = collection.query(query_embeddings=q_emb, n_results=3)
    sources = results["documents"][0]
    
    if not sources:
        return AnswerResponse(answer="В документе нет ответа на этот вопрос.", sources=[])
        
    context = "\n\n---\n\n".join(sources)
    prompt = build_prompt(req.question, context)
    
    answer = ask_yandexgpt(prompt)
    
    return AnswerResponse(answer=answer, sources=sources)
