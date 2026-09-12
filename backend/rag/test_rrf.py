from backend.rag.rrf import reciprocal_rank_fusion


# Example vector-search ranking
vector_results = [10, 20, 30, 40, 50]

# Example BM25 ranking
bm25_results = [30, 20, 60, 10, 70]


# Combine rankings
hybrid_results = reciprocal_rank_fusion(
    vector_results,
    bm25_results
)


print("Vector results:")
print(vector_results)

print("\nBM25 results:")
print(bm25_results)

print("\nHybrid RRF results:")
print(hybrid_results)