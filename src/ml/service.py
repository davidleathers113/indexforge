import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI(title="IndexForge ML Service")

# Initialize model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


class TextInput(BaseModel):
    text: str


@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": model is not None}


@app.post("/embed")
async def create_embedding(input_data: TextInput):
    try:
        # Generate embedding
        embedding = model.encode(input_data.text)
        return {"embedding": embedding.tolist(), "dimensions": len(embedding)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model-info")
async def model_info():
    return {
        "model_name": model.get_sentence_embedding_dimension(),
        "device": str(next(model.parameters()).device),
        "embedding_dimension": model.get_sentence_embedding_dimension(),
    }
