from backend.ingestion.pdf import extract_text_from_pdf
from backend.rag.chunking import chunk_pages
from backend.rag.embedding import generate_embeddings


# 1. Read PDF
file_path = "data/documents/distorted.pdf"

pages = extract_text_from_pdf(file_path)

# 2. Create chunks
chunks = chunk_pages(pages)

print("Total chunks:", len(chunks))


# 3. Get text from every chunk
texts = [chunk["text"] for chunk in chunks]


# 4. Generate embeddings
embeddings = generate_embeddings(texts)


# 5. Check result
print("\nEmbedding generation completed!")

print("Number of vectors:", len(embeddings))
print("Vector dimensions:", len(embeddings[0]))

print("\nFirst chunk:")
print(chunks[0]["text"])

print("\nFirst vector (first 10 values):")
print(embeddings[0][:10])