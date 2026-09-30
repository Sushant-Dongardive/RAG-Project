import sys
from pathlib import Path
from knowledge_db import delete_document_chunks
from vector_retriever import VectorStore
from hybrid_retriever import HybridRetriever

def delete_dataset(filename: str):
    print(f"[*] Starting removal of '{filename}' from all pipelines...")

    # 1. Purge from SQLite
    deleted_rows = delete_document_chunks(filename)

    # 2. Purge from FAISS & rewrite faiss_index.bin / faiss_meta.pkl
    vs = VectorStore()
    vs.remove_document(filename)

    # 3. Purge from BM25 & rewrite bm25_cache.pkl
    retriever = HybridRetriever()
    retriever.remove_document(filename)

    # 4. Optional: Remove raw source file from Data/ if present
    data_file = Path(__file__).resolve().parent.parent / "Data" / filename
    if data_file.exists():
        data_file.unlink()
        print(f"[File] Deleted physical file from Data/: {data_file.name}")

    print(f"\n[✓] Successfully removed '{filename}' ({deleted_rows} chunks purged).")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = input("Enter the filename to delete (e.g. large_document.pdf): ").strip()
    
    if target:
        delete_dataset(target)
    else:
        print("No filename specified.")