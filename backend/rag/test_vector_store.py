from backend.ingestion.pdf import extract_text_from_pdf
from backend.rag.chunking import chunk_pages
from backend.rag.embedding import generate_embeddings
from backend.rag.vector_store import create_vector_store, search_vector_store


# 1. Load PDF
file_path = "data/documents/distorted.pdf"

pages = extract_text_from_pdf(file_path)


# 2. Create chunks
chunks = chunk_pages(pages)

print("Total chunks:", len(chunks))


# 3. Get chunk text
texts = [chunk["text"] for chunk in chunks]


# 4. Generate embeddings
embeddings = generate_embeddings(texts)


# 5. Create FAISS vector store
index = create_vector_store(embeddings)

print("Vector store created!")
print("Vectors stored:", index.ntotal)


# 6. Create a question
question = "What classifier was used for fingerprint verification?"


# 7. Convert question into an embedding
question_embedding = generate_embeddings([question])[0]


# 8. Search FAISS
distances, indices = search_vector_store(
    index,
    question_embedding,
    top_k=5
)


# 9. Display results
print("\nQuestion:")
print(question)

print("\nTop 5 relevant chunks:")

for rank, (distance, index_number) in enumerate(
    zip(distances, indices), start=1
):

    print(f"\n--- Result {rank} ---")
    print("Chunk index:", index_number)
    print("Distance:", distance)
    print("Page:", chunks[index_number]["page"])
    print("Text:")
    print(chunks[index_number]["text"])