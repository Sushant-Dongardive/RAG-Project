from backend.agents.planner import plan_query
from backend.agents.retriever import retrieve_documents
from backend.agents.synthesizer import synthesize_answer

from backend.ingestion.pdf import extract_text_from_pdf
from backend.rag.chunking import chunk_pages
from backend.rag.embedding import generate_embeddings
from backend.rag.vector_store import create_vector_store
from backend.rag.bm25 import create_bm25_index


# 1. Load document
file_path = "data/documents/distorted.pdf"

pages = extract_text_from_pdf(file_path)

chunks = chunk_pages(pages)

texts = [
    chunk["text"]
    for chunk in chunks
]


# 2. Create vector index
embeddings = generate_embeddings(texts)

vector_index = create_vector_store(embeddings)


# 3. Create BM25 index
bm25_index = create_bm25_index(texts)


# 4. User question
question = "What was the accuracy of the cost-sensitive classifier?"


# 5. Planner Agent
plan = plan_query(question)

print("Planner result:")
print(plan)


# 6. Retriever Agent
retrieval = retrieve_documents(
    plan,
    chunks,
    vector_index,
    bm25_index,
    top_k=5
)

print("\nRetriever completed.")


# 7. Synthesizer Agent
synthesized = synthesize_answer(
    question,
    retrieval
)


# 8. Display final answer
print("\nSynthesizer result:")
print("Question:", synthesized["question"])

print("\nFinal Answer:")
print(synthesized["answer"])

print("\nSources:")
for source in synthesized["sources"]:
    print(source)