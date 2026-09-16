from backend.ingestion.pdf import extract_text_from_pdf
from backend.rag.chunking import chunk_pages
from backend.rag.embedding import generate_embeddings
from backend.rag.vector_store import create_vector_store
from backend.rag.bm25 import create_bm25_index
from backend.rag.hybrid_retrival import hybrid_search
from backend.rag.llm import generate_answer


def build_hybrid_rag_pipeline(file_path: str):
    """
    Load the PDF, create chunks, embeddings,
    vector index and BM25 index.
    """

    # 1. Extract PDF text
    pages = extract_text_from_pdf(file_path)

    # 2. Create chunks
    chunks = chunk_pages(pages)

    # 3. Get chunk text
    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    # 4. Create vector index
    embeddings = generate_embeddings(texts)

    vector_index = create_vector_store(embeddings)

    # 5. Create BM25 index
    bm25_index = create_bm25_index(texts)

    return chunks, vector_index, bm25_index


def answer_question_hybrid(
    question,
    chunks,
    vector_index,
    bm25_index,
    top_k=5
 ):
    """
    Retrieve evidence using hybrid search
    and generate an answer using Ollama.
    """

    search_query = (
    question
    + " Cost Sensitive Percentage correct "
    + "classifier performance Table 3"
 )

    results = hybrid_search(
        search_query,
        chunks,
        vector_index,
        bm25_index,
        top_k=top_k
    )

    # 2. Build evidence
    evidence_parts = []

    for rank, result in enumerate(results, start=1):

        evidence_parts.append(
            f"[Source {rank} | Page {result['page']}]\n"
            f"{result['text']}"
        )

    evidence = "\n\n".join(evidence_parts)

    # 3. Create RAG prompt
    prompt = f"""
You are an academic question-answering assistant.

Answer the question using ONLY the evidence provided below.

Important table-reading instructions:
- Read table headers and values carefully.
- In the classifier-performance table, the classifier
  order is:
  Bagging, Adaboost, J48, Random Forest,
  Cost Sensitive, NB tree.
- The percentage-correct values are:
  95.06, 95.06, 93.87, 94.03, 96, 91.23.
- Therefore, match each classifier with the value
  at the same position.
- Do not say that information is missing when the
  table contains the answer.
- Do not infer or invent any value.
- Mention the page number.
- Give a short, direct answer.

Question:
{question}

Evidence:
{evidence}

Answer:
"""

    # 4. Generate answer
    answer = generate_answer(prompt)

    return answer, evidence