from backend.ingestion.pdf import extract_text_from_pdf
from backend.rag.chunking import chunk_pages
from backend.rag.embedding import generate_embeddings
from backend.rag.vector_store import create_vector_store
from backend.rag.bm25 import create_bm25_index
from backend.rag.hybrid_retrival import hybrid_search


# 1. Load PDF
file_path = "data/documents/distorted.pdf"

pages = extract_text_from_pdf(file_path)


# 2. Create chunks
chunks = chunk_pages(pages)

print("Total chunks:", len(chunks))


# 3. Get chunk text
texts = [
    chunk["text"]
    for chunk in chunks
]


# 4. Create embeddings and vector index
embeddings = generate_embeddings(texts)

vector_index = create_vector_store(embeddings)

print("Vector index created!")


# 5. Create BM25 index
bm25_index = create_bm25_index(texts)

print("BM25 index created!")


# 6. Ask question
question = "Cost Sensitive 96 percentage correct"


# 7. Hybrid search
results = hybrid_search(
    question,
    chunks,
    vector_index,
    bm25_index,
    top_k=5
)


# 8. Display results
print("\nQuestion:")
print(question)

print("\nHybrid retrieval results:")

for rank, result in enumerate(results, start=1):

    print(f"\n--- Result {rank} ---")
    print("Chunk index:", result["chunk_index"])
    print("Page:", result["page"])
    print("Text:")
    print(result["text"])