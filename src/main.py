from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from src.rag_core import chunk_text, build_prompt, ask_yandexgpt, embedder, client
import io
from pypdf import PdfReader
import os

app = FastAPI(title="RAG-Eval-Lab API", description="Умный поиск по PDF")

# Глобальная переменная для хранения коллекции
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

def process_and_store(text):
    """Вспомогательная функция для нарезки и сохранения в базу."""
    global collection
    chunks = chunk_text(text, chunk_size=1000, overlap=200)
    
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
    return len(chunks)

@app.post("/load_document")
def load_document():
    """Загружает дефолтный PDF из папки data."""
    pdf_path = "data/document.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Файл data/document.pdf не найден")
        
    reader = PdfReader(pdf_path)
    full_text = "".join([(page.extract_text() or "") + "\n" for page in reader.pages])
    
    count = process_and_store(full_text)
    return {"message": "Документ загружен", "chunks_count": count}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Принимает PDF файл напрямую через интерфейс."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Пожалуйста, загрузите файл в формате PDF")
        
    pdf_bytes = await file.read()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    
    full_text = "".join([(page.extract_text() or "") + "\n" for page in reader.pages])
    
    count = process_and_store(full_text)
    return {"message": "Файл успешно загружен", "chunks_count": count}

@app.post("/ask", response_model=AnswerResponse)
def ask(req: QuestionRequest):
    """Ищет контекст в ChromaDB и спрашивает YandexGPT."""
    global collection
    if collection is None:
        raise HTTPException(status_code=400, detail="Сначала загрузите документ")
        
    q_emb = embedder.encode([req.question]).tolist()
    results = collection.query(query_embeddings=q_emb, n_results=3)
    sources = results["documents"][0]
    
    if not sources:
        return AnswerResponse(answer="В документе нет ответа на этот вопрос.", sources=[])
        
    context = "\n\n---\n\n".join(sources)
    prompt = build_prompt(req.question, context)
    answer = ask_yandexgpt(prompt)
    
    return AnswerResponse(answer=answer, sources=sources)
