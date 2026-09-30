import os
import pickle
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_FILE = Path(__file__).resolve().parent / "faiss_index.bin"
META_FILE = Path(__file__).resolve().parent / "faiss_meta.pkl"


class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance.model = SentenceTransformer("all-MiniLM-L6-v2")
            if hasattr(cls._instance.model, "get_embedding_dimension"):
                cls._instance.dimension = cls._instance.model.get_embedding_dimension()
            else:
                cls._instance.dimension = cls._instance.model.get_sentence_embedding_dimension()
            cls._instance.index = None
            cls._instance.metadata = []
            cls._instance.load_from_disk()
        return cls._instance

    def reset(self):
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        if INDEX_FILE.exists():
            INDEX_FILE.unlink()
        if META_FILE.exists():
            META_FILE.unlink()

    def add_texts(self, chunks: list, metadatas: list, persist: bool = True):
        if not chunks:
            return
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.dimension)

        embeddings = self.model.encode(chunks, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        self.index.add(np.array(embeddings, dtype=np.float32))
        self.metadata.extend(metadatas)

        if persist:
            self.save_to_disk()

    def save_to_disk(self):
        if self.index is not None:
            faiss.write_index(self.index, str(INDEX_FILE))
            with open(META_FILE, "wb") as f:
                pickle.dump(self.metadata, f)
            print(f"[VectorStore] Saved {len(self.metadata)} vectors and metadata to disk.")

    def load_from_disk(self):
        if INDEX_FILE.exists() and META_FILE.exists():
            try:
                self.index = faiss.read_index(str(INDEX_FILE))
                with open(META_FILE, "rb") as f:
                    self.metadata = pickle.load(f)
            except Exception as e:
                print(f"[VectorStore] Cache load error: {e}. Resetting index.")
                self.reset()
        else:
            self.reset()

    def remove_document(self, filename: str):
        target = filename.strip().lower()
        valid_chunks = []
        valid_metas = []
        for m in self.metadata:
            name = (m.get("filename") or m.get("dataset_name", "")).strip().lower()
            if name != target:
                valid_chunks.append(m["content"])
                valid_metas.append(m)

        self.reset()
        if valid_chunks:
            self.add_texts(valid_chunks, valid_metas, persist=True)
        else:
            self.save_to_disk()

    def search(self, query: str, top_k: int = 5, filter_dataset: str = None):
        if self.index is None or self.index.ntotal == 0:
            return []

        q_vec = self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)
        scores, indices = self.index.search(np.array(q_vec, dtype=np.float32), min(top_k * 4, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or idx >= len(self.metadata):
                continue
            item = self.metadata[idx]

            if filter_dataset and filter_dataset != "ALL" and filter_dataset != "All Datasets (Global Knowledge Base)":
                target = filter_dataset.strip().lower()
                doc_name = str(item.get("dataset_name", "")).strip().lower()
                file_name = str(item.get("filename", "")).strip().lower()
                if target != doc_name and target != file_name:
                    continue

            results.append({
                "chunk_id": item.get("id"),
                "content": item.get("content"),
                "dataset_name": item.get("dataset_name") or item.get("filename", "UNKNOWN"),
                "page": item.get("page", 1),
                "score": float(score)
            })
            if len(results) >= top_k:
                break
        return results