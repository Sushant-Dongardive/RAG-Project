from backend.rag.hybrid_rag import (
    build_hybrid_rag_pipeline,
    answer_question_hybrid
)


file_path = "data/documents/distorted.pdf"


print("Building Hybrid RAG pipeline...")

chunks, vector_index, bm25_index = (
    build_hybrid_rag_pipeline(file_path)
)

print(f"Loaded {len(chunks)} chunks.")
print(f"Vector index contains {vector_index.ntotal} vectors.")
print("BM25 index created!")


question = "What was the accuracy of the cost-sensitive classifier?"


print("\nQuestion:")
print(question)


answer, evidence = answer_question_hybrid(
    question,
    chunks,
    vector_index,
    bm25_index,
    top_k=5
)


print("\nGenerated Answer:")
print(answer)


print("\nRetrieved Evidence:")
print(evidence)