from backend.ingestion.pdf import extract_text_from_pdf
from backend.rag.chunking import chunk_pages
from backend.rag.embedding import generate_embeddings
from backend.rag.vector_store import (
    create_vector_store,
    search_vector_store
)
from backend.rag.llm import generate_answer


def build_rag_pipeline(file_path: str):
    """
    Load the PDF, create chunks, generate embeddings,
    and build the FAISS vector store.
    """

    # 1. Extract PDF text
    pages = extract_text_from_pdf(file_path)

    # 2. Create chunks
    chunks = chunk_pages(pages)

    # 3. Get text from chunks
    texts = [chunk["text"] for chunk in chunks]

    # 4. Generate embeddings
    embeddings = generate_embeddings(texts)

    # 5. Create FAISS index
    index = create_vector_store(embeddings)

    return chunks, index


def answer_question(question: str, chunks, index, top_k=5):
    """
    Retrieve relevant chunks and generate an answer
    using only the retrieved evidence.
    """

    # 1. Convert question into embedding
    question_embedding = generate_embeddings([question])[0]

    # 2. Search relevant chunks
    distances, indices = search_vector_store(
        index,
        question_embedding,
        top_k=top_k
    )

    # 3. Build evidence text
    evidence_parts = []

    for rank, index_number in enumerate(indices, start=1):

        chunk = chunks[index_number]

        evidence_parts.append(
            f"[Source {rank} | Page {chunk['page']}]\n"
            f"{chunk['text']}"
        )

    evidence = "\n\n".join(evidence_parts)

    # 4. Create a strict RAG prompt
    prompt = f"""
You are an academic question-answering assistant.

Answer the question using ONLY the evidence provided below.

Rules:
- Do not use outside knowledge.
- Do not invent information.
- If the evidence does not contain the answer, say:
  "The provided document does not contain enough information."
- Mention the page number when possible.
- Give a clear and concise answer.

Question:
{question}

Evidence:
{evidence}

Answer:
"""

    # 5. Generate answer using Ollama
    answer = generate_answer(prompt)

    return answer, evidence


if __name__ == "__main__":

    file_path = "data/documents/distorted.pdf"

    print("Building RAG pipeline...")

    chunks, index = build_rag_pipeline(file_path)

    print(f"Loaded {len(chunks)} chunks.")
    print(f"FAISS contains {index.ntotal} vectors.")

    question = (
        "What classifier framework was used in the "
        "distorted fingerprint verification system?"
    )

    print("\nQuestion:")
    print(question)

    answer, evidence = answer_question(
        question,
        chunks,
        index,
        top_k=5
    )

    print("\nGenerated Answer:")
    print(answer)

    print("\nRetrieved Evidence:")
    print(evidence)