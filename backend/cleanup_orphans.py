import sqlite3
from pathlib import Path
from vector_retriever import VectorStore
from hybrid_retriever import HybridRetriever

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
DB_PATH = Path(__file__).resolve().parent / "rag_knowledge.db"

def purge_deleted_files():
    print("[*] Checking for ghost datasets in database...")
    
    # 1. Get physical filenames currently in Data/
    real_files = {p.name.strip().lower() for p in DATA_DIR.rglob("*") if p.is_file()}
    
    # 2. Check SQLite
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT filename FROM chunks")
    db_files = [row[0] for row in cursor.fetchall()]
    
    orphans = [f for f in db_files if f.strip().lower() not in real_files]
    
    if not orphans:
        print("[✓] No orphaned records found. SQLite matches Data/ folder.")
    else:
        print(f"[-] Found {len(orphans)} deleted files still in SQLite: {orphans}")
        for ghost in orphans:
            cursor.execute("DELETE FROM chunks WHERE filename = ?", (ghost,))
            cursor.execute("DELETE FROM chat_history WHERE dataset_name = ?", (ghost,))
            print(f"    [-] Purged '{ghost}' from SQLite.")
        conn.commit()
    conn.close()

    # 3. Clean up VectorStore and FAISS
    vs = VectorStore()
    if vs.metadata:
        initial_count = len(vs.metadata)
        valid_chunks = []
        valid_metas = []
        for item in vs.metadata:
            fname = (item.get("filename") or item.get("dataset_name", "")).strip().lower()
            if fname in real_files:
                valid_chunks.append(item["content"])
                valid_metas.append(item)
        
        if len(valid_metas) < initial_count:
            print(f"[*] Rebuilding FAISS vector index: {initial_count} -> {len(valid_metas)} chunks...")
            vs.reset()
            if valid_chunks:
                vs.add_texts(valid_chunks, valid_metas, persist=True)
            else:
                vs.save_to_disk()
            print("[VectorStore] Saved vectors and metadata to disk.")

    # 4. Rebuild BM25
    retriever = HybridRetriever()
    retriever.corpus_chunks = [
        c for c in retriever.corpus_chunks
        if (c.get("filename") or c.get("dataset_name", "")).strip().lower() in real_files
    ]
    retriever.build_bm25(retriever.corpus_chunks, force_rebuild=True)
    print("[Retriever] Loaded BM25 index from cache.")
    print("[Indexer] Successfully indexed chunks across all datasets.")

if __name__ == "__main__":
    purge_deleted_files()