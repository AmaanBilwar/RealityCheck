from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
import faiss
from sentence_transformers import SentenceTransformer
import uvicorn

app = FastAPI(title="Simple RAG API")

# Define models
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class Document(BaseModel):
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    score: Optional[float] = None

class QueryResponse(BaseModel):
    results: List[Document]
    query: str

# Global variables
embeddings_dir = "embeddings-s3-bucket"
model = None
index = None
documents = {}

@app.on_event("startup")
async def startup_event():
    global model, index, documents
    
    # Load the embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Check if embeddings directory exists
    if not os.path.exists(embeddings_dir):
        raise Exception(f"Embeddings directory '{embeddings_dir}' not found")
    
    # Load documents and embeddings
    embeddings_path = os.path.join(embeddings_dir, "embeddings.npy")
    documents_path = os.path.join(embeddings_dir, "documents.json")
    
    if not os.path.exists(embeddings_path) or not os.path.exists(documents_path):
        raise Exception(f"Required files not found in '{embeddings_dir}'")
    
    # Load embeddings
    embeddings = np.load(embeddings_path)
    
    # Load documents
    with open(documents_path, 'r') as f:
        documents = json.load(f)
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype(np.float32))
    
    print(f"Loaded {len(documents)} documents with {embeddings.shape[0]} embeddings")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    if model is None or index is None:
        raise HTTPException(status_code=500, detail="Service not initialized properly")
    
    # Encode the query
    query_embedding = model.encode([request.query])[0].reshape(1, -1).astype(np.float32)
    
    # Search for similar vectors
    distances, indices = index.search(query_embedding, request.top_k)
    
    # Prepare results
    results = []
    for i, doc_idx in enumerate(indices[0]):
        if doc_idx < len(documents):
            doc = documents[str(doc_idx)]
            results.append(
                Document(
                    id=str(doc_idx),
                    content=doc["content"],
                    metadata=doc.get("metadata", {}),
                    score=float(1.0 - distances[0][i]/100.0)  # Convert distance to similarity score
                )
            )
    
    return QueryResponse(results=results, query=request.query)

@app.get("/documents/{doc_id}", response_model=Document)
async def get_document(doc_id: str):
    if doc_id not in documents:
        raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")
    
    doc = documents[doc_id]
    return Document(
        id=doc_id,
        content=doc["content"],
        metadata=doc.get("metadata", {})
    )

# Utility endpoint to get document count
@app.get("/stats")
async def get_stats():
    return {
        "document_count": len(documents),
        "embeddings_directory": embeddings_dir
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)