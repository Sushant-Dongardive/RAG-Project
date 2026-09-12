def reciprocal_rank_fusion(
    vector_indices,
    bm25_indices,
    k=60
):
    """
    Combine vector-search and BM25 rankings
    using Reciprocal Rank Fusion.
    """

    scores = {}

    # Process vector-search results
    for rank, index in enumerate(vector_indices):
        scores[index] = scores.get(index, 0) + 1 / (k + rank + 1)

    # Process BM25 results
    for rank, index in enumerate(bm25_indices):
        scores[index] = scores.get(index, 0) + 1 / (k + rank + 1)

    # Sort chunks by combined score
    ranked_indices = sorted(
        scores,
        key=scores.get,
        reverse=True
    )

    return ranked_indices