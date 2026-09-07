from fastapi import FastAPI
from backend.api.upload import router as upload_router

app = FastAPI(title="Agentic RAG Platform")


@app.get("/")
def home():
    return {
        "message": "Agentic RAG Platform is running!"
    }


app.include_router(upload_router, prefix="/api")