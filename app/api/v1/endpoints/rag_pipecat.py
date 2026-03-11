import httpx
import logging
import uuid
from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os,pypdf
from app.services.rag_service import ingest_document, query_docs

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/RAG", tags=["Pipecat RAG"])


@router.post("/ingest")
async def ingest(file: UploadFile):
    text = (await file.read()).decode()  # or use pypdf for PDFs
    ingest_document(text, file.filename)
    return {"status": "ingested"}

@router.get("/query")
async def query(q: str):
    return {"context": query_docs(q)}