from chromadb import Client
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

embedder = SentenceTransformer("all-MiniLM-L6-v2")
chroma = Client()
collection = chroma.get_or_create_collection("docs")

def ingest_document(text: str, doc_id: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)
    embeddings = embedder.encode(chunks).tolist()
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"{doc_id}_{i}" for i in range(len(chunks))]
    )

def query_docs(query: str, n=3) -> str:
    embedding = embedder.encode([query]).tolist()
    results = collection.query(query_embeddings=embedding, n_results=n)
    return "\n\n".join(results["documents"][0])