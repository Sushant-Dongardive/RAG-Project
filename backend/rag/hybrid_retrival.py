from backend.rag.embedding import generate_embeddings
from backend.rag.vector_store import search_vector_store
from backend.rag.bm25 import search_bm25
from backend.rag.rrf import reciprocal_rank_fusion


def hybrid_search(
    question,
    chunks,
    vector_index,
    bm25_index,
    top_k=5
):
    """
    Perform vector search and BM25 search,
    then combine their rankings using RRF.
    """

    # 1. Generate question embedding
    question_embedding = generate_embeddings(
        [question]
    )[0]

    # 2. Vector search
    vector_distances, vector_indices = search_vector_store(
        vector_index,
        question_embedding,
        top_k=top_k
    )

    # 3. BM25 search
    bm25_scores, bm25_indices = search_bm25(
        bm25_index,
        question,
        top_k=top_k
    )

    # 4. Combine both rankings
    hybrid_indices = reciprocal_rank_fusion(
        vector_indices,
        bm25_indices,
        top_k=top_k
    )

    # 5. Prepare final results
    results = []

    for index in hybrid_indices:
        results.append({
            "chunk_index": int(index),
            "page": chunks[index]["page"],
            "text": chunks[index]["text"]
        })

    return results