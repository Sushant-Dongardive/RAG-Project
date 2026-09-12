from backend.rag.basic_rag import build_rag_pipeline, answer_question


file_path = "data/documents/distorted.pdf"

print("Building RAG pipeline...")

chunks, index = build_rag_pipeline(file_path)

print(f"Loaded {len(chunks)} chunks.")
print(f"FAISS contains {index.ntotal} vectors.")


questions = [
    "Which classifiers were compared in the classifier framework?",
    "What are bagging, boosting, and cost-sensitive classifiers used for?",
    "Which classifier achieved the best performance?",
    "What was the accuracy of the cost-sensitive classifier?",
]


for question in questions:

    print("\n" + "=" * 70)
    print("QUESTION:")
    print(question)

    answer, evidence = answer_question(
        question,
        chunks,
        index,
        top_k=5
    )

    print("\nANSWER:")
    print(answer)

    print("\nEVIDENCE:")
    print(evidence)