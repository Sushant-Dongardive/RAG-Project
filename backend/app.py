import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import shutil
from pathlib import Path
from contextlib import asynccontextmanager
import signal

import threading
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import knowledge_db as db
from config import DOCS_DIR
from chunking import extract_document, recursive_chunk_text
from vector_retriever import VectorStore
from hybrid_retriever import HybridRetriever
from graph_engine import AgenticRAGEngine

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
SUPPORTED_EXTS = {".pdf", ".docx", ".doc", ".csv", ".xlsx", ".xls", ".txt", ".md"}

index_lock = threading.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Server] App started.")
    yield
    print("[Shutdown] Cleaning up open resources...")
    os._exit(0)


app = FastAPI(lifespan=lifespan, title="Agentic RAG Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core services
db.init_db()
vector_store = VectorStore()
hybrid_retriever = HybridRetriever()
engine = AgenticRAGEngine(hybrid_retriever)

def get_all_document_files():
    """Scans both Data/ and Data/Documents/ for supported files."""
    seen = set()
    found = []
    for d in [DOCS_DIR, DATA_DIR]:
        if d.exists():
            for f in d.rglob("*"):
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS:
                    if f.name.lower() not in seen:
                        seen.add(f.name.lower())
                        found.append(f)
    return found


def force_shutdown_handler(sig, frame):
    print("\n[Shutdown] Fast shutdown initiated via Ctrl+C. Exiting...")
    os._exit(0)


signal.signal(signal.SIGINT, force_shutdown_handler)
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, force_shutdown_handler)


def reindex_all():
    """Reads all chunks from SQLite and builds FAISS & BM25 indexes."""
    with index_lock:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM document_chunks")
            all_chunks = [dict(r) for r in cursor.fetchall()]

            if not all_chunks:
                print("[Indexer] SQLite document_chunks is empty. Nothing to index.")
                return 0

            vector_store.reset()
            texts = [c["content"] for c in all_chunks]
            metas = [{
                "id": c["id"],
                "dataset_name": c["dataset_name"],
                "filename": c["dataset_name"],
                "page": c["page_number"],
                "content": c["content"]
            } for c in all_chunks]

            vector_store.add_texts(texts, metas, persist=True)
            hybrid_retriever.build_bm25(metas, force_rebuild=True)
            print(f"[Indexer] Successfully indexed {len(all_chunks)} chunks across all datasets.")
            return len(all_chunks)


def ingest_file_to_db(filepath: Path):
    """Processes a document and commits its chunks into SQLite."""
    filename = filepath.name
    try:
        pages = extract_document(str(filepath))
    except Exception as e:
        print(f"[Chunker Error on {filename}]: {e}")
        pages = []

    if not pages:
        return 0

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO datasets (name, file_path, file_type, total_pages)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                file_path=excluded.file_path,
                total_pages=excluded.total_pages
        """, (filename, str(filepath), filepath.suffix.replace(".", "") or "pdf", len(pages)))

        cursor.execute("SELECT id FROM datasets WHERE name = ?", (filename,))
        row = cursor.fetchone()
        ds_id = row["id"] if isinstance(row, dict) else row[0]

        cursor.execute("DELETE FROM document_chunks WHERE dataset_id = ?", (ds_id,))

        total_chunks = 0
        for p in pages:
            chunks = recursive_chunk_text(p["text"])
            for idx, chunk in enumerate(chunks):
                cursor.execute("""
                    INSERT INTO document_chunks (dataset_id, dataset_name, page_number, chunk_index, content)
                    VALUES (?, ?, ?, ?, ?)
                """, (ds_id, filename, p["page"], idx, chunk))
                total_chunks += 1

        

        conn.commit()
        return total_chunks


def ingest_single_file(filepath: Path):
    """Processes and indexes only the newly uploaded file incrementally (instant 1-2 sec upload)."""
    new_chunks = ingest_file_to_db(filepath)
    if new_chunks == 0:
        return 0

    filename = filepath.name
    # If the file already existed in vector metadata, remove old entries first
    existing = any(
        (m.get("filename") or m.get("dataset_name", "")).strip().lower() == filename.strip().lower()
        for m in vector_store.metadata
    )
    if existing:
        vector_store.remove_document(filename)
        hybrid_retriever.remove_document(filename)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM document_chunks WHERE dataset_name = ?", (filename,))
        chunks = [dict(r) for r in cursor.fetchall()]

    if chunks:
        texts = [c["content"] for c in chunks]
        metas = [{
            "id": c["id"],
            "dataset_name": c["dataset_name"],
            "filename": c["dataset_name"],
            "page": c["page_number"],
            "content": c["content"]
        } for c in chunks]

        # Incrementally add ONLY this file's chunks to FAISS
        vector_store.add_texts(texts, metas, persist=True)

        # Fast in-memory update for BM25 (<0.05s)
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM document_chunks")
            all_chunks = [dict(r) for r in cursor.fetchall()]
            all_metas = [{
                "id": c["id"],
                "dataset_name": c["dataset_name"],
                "filename": c["dataset_name"],
                "page": c["page_number"],
                "content": c["content"]
            } for c in all_chunks]
            hybrid_retriever.build_bm25(all_metas, force_rebuild=True)

    print(f"[Incremental Ingestion] Successfully indexed {new_chunks} chunks for: {filename}")
    return new_chunks


# In-memory status tracker for asynchronous document processing
document_status = {}  # {filename: {"status": "processing"|"ready"|"error", "chunks": int, "error": str}}


def background_ingest_worker(filepath: Path):
    """Worker function executed in an independent background thread."""
    filename = filepath.name
    document_status[filename] = {"status": "processing", "chunks": 0, "error": None}
    try:
        count = ingest_single_file(filepath)
        document_status[filename] = {"status": "ready", "chunks": count, "error": None}
        print(f"[Async Ingestion] Successfully completed indexing for {filename} ({count} chunks).")
    except Exception as e:
        print(f"[Async Ingestion Error] Failed on {filename}: {e}")
        document_status[filename] = {"status": "error", "chunks": 0, "error": str(e)}


@app.on_event("startup")
def startup_event():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    all_files = get_all_document_files()

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        count = cursor.fetchone()[0]

    if count == 0 and all_files:
        print("[Startup] Initializing empty database from files in Data/...")
        for doc in all_files:
            ingest_file_to_db(doc)

    if vector_store.index is None or len(vector_store.metadata) != count or hybrid_retriever.bm25 is None:
        reindex_all()
    else:
        print(f"[Startup] Vector and BM25 indexes already up to date ({count} chunks).")



class QueryRequest(BaseModel):
    query: str
    active_dataset: str = None


class GlobalAIRequest(BaseModel):
    query: str


class CompareRequest(BaseModel):
    doc_a: str
    doc_b: str
    query: str

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


@app.get("/")
def root():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Agentic RAG Engine Backend is Running!", "status": "ok"}

@app.get("/login")
def login_page():
    login_file = FRONTEND_DIR / "login.html"
    if login_file.exists():
        return FileResponse(login_file)
    return {"message": "Login page not found", "status": "error"}

@app.post("/api/auth/login")
def api_login(req: LoginRequest):
    user = db.authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = f"nexus_tok_{user['id']}_{os.urandom(8).hex()}"
    return {
        "status": "success",
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    }
    
@app.post("/api/auth/register")
def api_register(req: RegisterRequest):
    if not req.email or not req.password or not req.name:
        raise HTTPException(status_code=400, detail="Name, email, and password are required.")
    existing = db.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    user_id = db.create_user(req.email, req.name, req.password)
    token = f"nexus_tok_{user_id}_{os.urandom(8).hex()}"
    return {
        "status": "success",
        "token": token,
        "user": {
            "id": user_id,
            "email": req.email,
            "name": req.name,
            "role": "Researcher"
        }
    }
    
@app.get("/health")
def health():
    return {"status": "ok", "message": "Agentic RAG Engine is healthy"}


@app.get("/datasets")
@app.get("/datasets/")
def list_datasets():
    with db.get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, total_pages, created_at FROM datasets ORDER BY id DESC")
        return [dict(r) for r in c.fetchall()]


@app.get("/datasets/sync")
def sync_datasets():
    try:
        all_files = get_all_document_files()
        for doc in all_files:
            ingest_file_to_db(doc)

        total_chunks = reindex_all()

        # Returns the exact key expected by our frontend alert: d.total_indexed_chunks
        return {
            "status": "success",
            "message": "Synchronized!",
            "total_indexed_chunks": total_chunks,
            "total_chunks": total_chunks,
            "chunks": total_chunks,
            "count": total_chunks
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "total_indexed_chunks": 0,
            "total_chunks": 0
        }


@app.get("/datasets/{dataset_name}/history")
def get_dataset_chat_history(dataset_name: str):
    return db.get_chats_by_dataset(dataset_name)


@app.post("/rag/execute")
def execute_rag_pipeline(req: QueryRequest):
    if not req.active_dataset or req.active_dataset.strip() == "":
        return {
            "error": True,
            "answer": "Please select a dataset or switch to our Global AI.",
            "found_in_dataset": False,
            "sources": [],
            "trace": [{
                "agent": "Planner Agent",
                "message": "Execution halted: No active dataset selected by user."
            }],
            "prompt_global_ai": True
        }

    res = engine.execute_rag(req.query, active_dataset=req.active_dataset)

    if res.get("found_in_dataset"):
        db.save_chat_message(
            dataset_name=req.active_dataset,
            session_type="rag",
            user_query=req.query,
            ai_response=res["answer"],
            sources=res["sources"],
            agent_trace=res["trace"]
        )
    return res


@app.post("/global-ai/chat")
def chat_global_ai(req: GlobalAIRequest):
    answer, web_sources = engine.execute_global_ai(req.query)
    db.save_chat_message(
        dataset_name="Global_Web",
        session_type="global_ai",
        user_query=req.query,
        ai_response=answer,
        sources=[w.get("title", "") for w in web_sources],
        agent_trace=[]
    )
    return {"answer": answer, "web_sources": web_sources}


@app.get("/global-ai/history")
def get_global_ai_history():
    return db.get_all_global_chats()


@app.post("/compare/analyze")
def compare_documents(req: CompareRequest):
    context_a, _, _ = hybrid_retriever.search(req.query, top_k=2, filter_dataset=req.doc_a)
    context_b, _, _ = hybrid_retriever.search(req.query, top_k=2, filter_dataset=req.doc_b)

    text_a = " ".join([c["content"] for c in context_a]) or f"No specific match in {req.doc_a}."
    text_b = " ".join([c["content"] for c in context_b]) or f"No specific match in {req.doc_b}."

    prompt = f"""Compare the following two documents regarding the user question: '{req.query}'
Doc A ({req.doc_a}):
{text_a}

Doc B ({req.doc_b}):
{text_b}

Synthesize a direct comparative response."""

    ans = engine.call_llm("You are a comparative research assistant.", prompt)
    session_tag = f"{req.doc_a} vs {req.doc_b}"

    db.save_chat_message(
        dataset_name=session_tag,
        session_type="compare",
        user_query=req.query,
        ai_response=ans,
        sources=[req.doc_a, req.doc_b]
    )
    return {"analysis": ans, "sources": [req.doc_a, req.doc_b]}


@app.get("/compare/history")
def get_comparison_history():
    return db.get_compare_chats()


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    target_dir = DATA_DIR if DATA_DIR.exists() else DOCS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    dest_path = target_dir / file.filename

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    filename = file.filename
    document_status[filename] = {"status": "processing", "chunks": 0, "error": None}

    # Offload processing to a dedicated background thread so the server stays 100% responsive
    import threading
    threading.Thread(target=background_ingest_worker, args=(dest_path,), daemon=True).start()

    return {
        "status": "processing",
        "filename": filename,
        "message": "File uploaded! Indexing in background."
    }


@app.get("/upload/status/{filename}")
def get_upload_status(filename: str):
    return document_status.get(filename, {"status": "ready"})


@app.get("/upload/status")
def get_all_upload_status():
    return document_status


@app.get("/api/documents")
def list_documents():
    with db.get_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT dataset_name, COUNT(*) as chunk_count FROM document_chunks GROUP BY dataset_name")
            rows = cursor.fetchall()
            return [{"filename": row[0], "chunks": row[1]} for row in rows]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{filename}")
def delete_document(filename: str):
    try:
        with index_lock:
            deleted_count = db.delete_document_chunks(filename)

            vs = VectorStore()
            vs.remove_document(filename)

            retriever = HybridRetriever()
            retriever.remove_document(filename)

        for folder in [DOCS_DIR, DATA_DIR]:
            target_path = folder / filename
            if target_path.exists():
                try:
                    target_path.unlink()
                except Exception:
                    pass

        return {
            "status": "success",
            "message": f"Deleted {filename} successfully.",
            "purged_chunks": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete {filename}: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)