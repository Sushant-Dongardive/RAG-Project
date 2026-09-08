def chunk_pages(pages, chunk_size=500, overlap=100):
    chunks = []

    for page in pages:
        text = page["text"].strip()

        start = 0

        while start < len(text):
            end = start + chunk_size

            chunk_text = text[start:end]

            chunks.append({
                "text": chunk_text,
                "page": page["page"],
            })

            start += chunk_size - overlap

    return chunks

if __name__ == "__main__":
    from backend.ingestion.pdf import extract_text_from_pdf

    file_path = "data/documents/distorted.pdf"

    pages = extract_text_from_pdf(file_path)

    chunks = chunk_pages(pages)

    print(f"Total pages: {len(pages)}")
    print(f"Total chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks[:5]):
        print(f"\n--- Chunk {i + 1} ---")
        print(f"Page: {chunk['page']}")
        print(chunk["text"])