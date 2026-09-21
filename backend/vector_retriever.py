import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME

class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            cls._instance.dimension = cls._instance.model.get_sentence_embedding_dimension()
            cls._instance.index = faiss.IndexFlatIP(cls._instance.dimension)
            cls._instance.metadata = []
        return cls._instance

    def add_texts(self, chunks: list, metadatas: list):
        if not chunks:
            return
        embeddings = self.model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)
        self.index.add(embeddings.astype(np.float32))
        self.metadata.extend(metadatas)

    def search(self, query: str, top_k: int = 5, filter_dataset: str = None):
        if self.index.ntotal == 0:
            return []
        
        query_vec = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
        k_search = min(top_k * 3, self.index.ntotal)
        scores, indices = self.index.search(query_vec, k_search)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            item = self.metadata[idx]
            if filter_dataset and filter_dataset != "ALL" and item["dataset_name"] != filter_dataset:
                continue
            results.append({
                "chunk_id": item["id"],
                "content": item["content"],
                "dataset_name": item["dataset_name"],
                "page": item["page"],
                "score": float(score)
            })
            if len(results) >= top_k:
                break
        return results

    def reset(self):
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []