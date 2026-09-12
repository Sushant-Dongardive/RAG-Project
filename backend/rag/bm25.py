from rank_bm25 import BM25Okapi


def create_bm25_index(texts):
    """
    Create a BM25 index from document chunks.
    """

    tokenized_texts = [
        text.lower().split()
        for text in texts
    ]

    bm25 = BM25Okapi(tokenized_texts)

    return bm25


def search_bm25(bm25, query, top_k=5):
    """
    Search document chunks using BM25 keyword matching.
    """

    query_tokens = query.lower().split()

    scores = bm25.get_scores(query_tokens)

    ranked_indices = scores.argsort()[::-1][:top_k]

    return scores[ranked_indices], ranked_indices