from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.rag_core import chunk_text, retrieve, build_prompt, ask_yandexgpt
from pypdf import PdfReader
import os

app = FastAPI(title="RAG-Eval-Lab API")

_chunks = []

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    sources: list[str]

@app.get("/health")
def health():
    return {"status": "ok", "chunks_loaded": len(_chunks)}

@app.post("/load_document")
def load_document():
    """Загружает PDF из data/document.pdf и режет на чанки."""
    global _chunks
    pdf_path = "data/document.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="data/document.pdf не найден")
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        full_text += (page.extract_text() or "") + "\n"
    _chunks = chunk_text(full_text)
    return {"chunks": len(_chunks)}

@app.post("/ask", response_model=AnswerResponse)
def ask(req: QuestionRequest):
    if not _chunks:
        raise HTTPException(status_code=400, detail="Сначала вызови /load_document")
    sources = retrieve(req.question, _chunks, k=3)
    context = "\n\n---\n\n".join(sources)
    prompt = build_prompt(req.question, context)
    answer = ask_yandexgpt(prompt)
    return AnswerResponse(answer=answer, sources=sources)
