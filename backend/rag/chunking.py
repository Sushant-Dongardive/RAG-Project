import re


def split_into_sentences(text):
    """
    Split text into sentences while keeping the sentence content intact.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def chunk_pages(pages, chunk_size=500, overlap=100):
    """
    Create chunks from page text without cutting sentences in the middle.

    Each chunk keeps its page number as metadata.
    """

    chunks = []

    for page in pages:
        page_number = page["page"]
        text = page["text"].strip()

        sentences = split_into_sentences(text)

        current_chunk = ""

        for sentence in sentences:

            # If adding the next sentence stays within the limit
            if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                current_chunk += sentence + " "

            else:
                # Save current chunk
                if current_chunk.strip():
                    chunks.append({
                        "text": current_chunk.strip(),
                        "page": page_number
                    })

                # Start next chunk
                current_chunk = sentence + " "

        # Save remaining text
        if current_chunk.strip():
            chunks.append({
                "text": current_chunk.strip(),
                "page": page_number
            })

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