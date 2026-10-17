import pickle
import re
from pathlib import Path
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from vector_retriever import VectorStore

BM25_CACHE = Path(__file__).resolve().parent / "bm25_cache.pkl"


def tokenize(text: str):
    return re.findall(r"\w+", (text or "").lower())


class HybridRetriever:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HybridRetriever, cls).__new__(cls)
            cls._instance.vector_store = VectorStore()
            cls._instance.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            cls._instance.bm25 = None
            cls._instance.corpus_chunks = []
            cls._instance.load_bm25()
        return cls._instance

    def build_bm25(self, chunks: list, force_rebuild: bool = True):
        self.corpus_chunks = chunks
        if not chunks:
            self.bm25 = None
            if BM25_CACHE.exists():
                BM25_CACHE.unlink()
            return

        tokenized_corpus = [tokenize(c.get("content", "")) for c in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

        if force_rebuild:
            with open(BM25_CACHE, "wb") as f:
                pickle.dump({"bm25": self.bm25, "chunks": self.corpus_chunks}, f)
            print(f"[Retriever] Loaded BM25 index from cache ({len(chunks)} chunks).")

    def load_bm25(self):
        if BM25_CACHE.exists():
            try:
                with open(BM25_CACHE, "rb") as f:
                    data = pickle.load(f)
                    self.bm25 = data["bm25"]
                    self.corpus_chunks = data["chunks"]
            except Exception:
                self.bm25 = None
                self.corpus_chunks = []

    def remove_document(self, filename: str):
        target = filename.strip().lower()
        remaining = [
            c for c in self.corpus_chunks
            if (c.get("filename") or c.get("dataset_name", "")).strip().lower() != target
        ]
        self.build_bm25(remaining, force_rebuild=True)

    def search(self, query: str, top_k: int = 4, filter_dataset: str = None):
        dense_results = self.vector_store.search(query, top_k=top_k * 2, filter_dataset=filter_dataset)

        bm25_results = []
        if self.bm25 and self.corpus_chunks:
            tokens = tokenize(query)
            scores = self.bm25.get_scores(tokens)
            ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k * 4]

            for idx in ranked_indices:
                if scores[idx] <= 0:
                    continue
                c = self.corpus_chunks[idx]
                if filter_dataset and filter_dataset != "ALL" and filter_dataset != "All Datasets (Global Knowledge Base)":
                    target = filter_dataset.strip().lower()
                    doc_name = str(c.get("dataset_name", "")).strip().lower()
                    file_name = str(c.get("filename", "")).strip().lower()
                    if target != doc_name and target != file_name:
                        continue
                bm25_results.append({
                    "chunk_id": c.get("id"),
                    "content": c.get("content"),
                    "dataset_name": c.get("dataset_name") or c.get("filename", "UNKNOWN"),
                    "page": c.get("page", 1),
                    "score": float(scores[idx])
                })
                if len(bm25_results) >= top_k * 2:
                    break

        # Pool & Deduplicate
        seen = set()
        pool = []
        for item in dense_results + bm25_results:
            key = (item.get("content", ""))[:120].strip()
            if key not in seen:
                seen.add(key)
                pool.append(item)

        if not pool:
            return [], dense_results, bm25_results

        # Cross-Encoder Reranking
        pairs = [[query, item["content"]] for item in pool[:8]]
        rerank_scores = self.reranker.predict(pairs, batch_size=8, show_progress_bar=False)

        for i, score in enumerate(rerank_scores):
            pool[i]["rerank_score"] = float(score)

        pool = sorted(pool[:len(rerank_scores)], key=lambda x: x["rerank_score"], reverse=True)
        return pool[:top_k], dense_results, bm25_results