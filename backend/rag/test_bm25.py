from backend.ingestion.pdf import extract_text_from_pdf
from backend.rag.chunking import chunk_pages
from backend.rag.bm25 import create_bm25_index, search_bm25


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


# 4. Create BM25 index
bm25 = create_bm25_index(texts)

print("BM25 index created!")


# 5. Search question
question = "Cost Sensitive 96 percentage correct"

scores, indices = search_bm25(
    bm25,
    question,
    top_k=5
)


# 6. Display results
print("\nQuestion:")
print(question)

print("\nTop 5 BM25 results:")

for rank, (score, index_number) in enumerate(
    zip(scores, indices),
    start=1
):

    print(f"\n--- Result {rank} ---")
    print("Chunk index:", index_number)
    print("BM25 score:", score)
    print("Page:", chunks[index_number]["page"])
    print("Text:")
    print(chunks[index_number]["text"])