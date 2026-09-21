import re
from rank_bm25 import BM25Okapi
from vector_retriever import VectorStore
from sentence_transformers import CrossEncoder
from config import RRF_K

class HybridRetriever:
    def __init__(self):
        self.vector_store = VectorStore()
        self.corpus_chunks = []
        self.bm25 = None
        # Lightweight, high-precision cross-encoder for re-ranking
        try:
            self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            print("[Retriever] Cross-Encoder Re-Ranker loaded.")
        except Exception as e:
            print(f"[Retriever Warning] Re-ranker offline: {e}")
            self.reranker = None

    def build_bm25(self, all_chunks: list):
        self.corpus_chunks = all_chunks
        tokenized = [self._tokenize(c["content"]) for c in all_chunks]
        if tokenized and any(len(t) > 0 for t in tokenized):
            self.bm25 = BM25Okapi(tokenized)

    def _tokenize(self, text: str):
        return [w.lower() for w in re.findall(r"\w+", str(text)) if len(w) > 1]

    def search(self, query: str, top_k: int = 4, filter_dataset: str = None):
        # 1. Fetch wider candidate pool (top 10 dense + top 10 sparse)
        dense_results = self.vector_store.search(query, top_k=10, filter_dataset=filter_dataset)
        
        bm25_results = []
        if self.bm25 and self.corpus_chunks:
            tokens = self._tokenize(query)
            if tokens:
                scores = self.bm25.get_scores(tokens)
                sorted_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
                for idx in sorted_idx:
                    chunk = self.corpus_chunks[idx]
                    if filter_dataset and filter_dataset != "ALL" and chunk["dataset_name"].strip().lower() != filter_dataset.strip().lower():
                        continue
                    if scores[idx] > 0:
                        bm25_results.append({
                            "chunk_id": chunk["id"],
                            "content": chunk["content"],
                            "dataset_name": chunk["dataset_name"],
                            "page": chunk["page"],
                            "score": float(scores[idx])
                        })
                    if len(bm25_results) >= 10:
                        break

        # 2. Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        item_map = {}

        for rank, item in enumerate(dense_results):
            cid = item["chunk_id"]
            item_map[cid] = item
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (RRF_K + rank + 1))

        for rank, item in enumerate(bm25_results):
            cid = item["chunk_id"]
            item_map[cid] = item
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (RRF_K + rank + 1))

        # Fallback to general chunks if pool is empty
        if not item_map:
            filtered = [c for c in self.corpus_chunks if not filter_dataset or filter_dataset == "ALL" or c["dataset_name"].strip().lower() == filter_dataset.strip().lower()]
            for c in filtered[:10]:
                item_map[c["id"]] = c
                rrf_scores[c["id"]] = 0.1

        sorted_candidates = [item_map[cid] for cid, _ in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:10]]

        # 3. Neural Cross-Encoder Re-Ranking Step
        if self.reranker and sorted_candidates:
            pairs = [[query, c["content"]] for c in sorted_candidates]
            cross_scores = self.reranker.predict(pairs)
            for idx, score in enumerate(cross_scores):
                sorted_candidates[idx]["cross_score"] = float(score)
            
            sorted_candidates.sort(key=lambda x: x.get("cross_score", 0), reverse=True)

        final_results = sorted_candidates[:top_k]
        return final_results, dense_results, bm25_results