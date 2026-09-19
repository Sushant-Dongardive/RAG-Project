from backend.rag.llm import generate_answer


def synthesize_answer(question: str, retrieval: dict):
    """
    Generate a final answer using only the evidence
    returned by the Retriever Agent.
    """

    results = retrieval["results"]

    if not results:
        return {
            "question": question,
            "answer": (
                "The available documents do not contain "
                "enough information to answer this question."
            ),
            "sources": []
        }

    evidence_parts = []

    for rank, result in enumerate(results, start=1):
        evidence_parts.append(
            f"[Source {rank} | Page {result['page']}]\n"
            f"{result['text']}"
        )

    evidence = "\n\n".join(evidence_parts)

    prompt = f"""
You are the Synthesizer Agent of an Agentic RAG system.

Answer the user's question using ONLY the retrieved evidence.

Rules:
- Use only the provided evidence.
- Do not use outside knowledge.
- Do not invent facts.
- Carefully interpret tables.
- When a table contains column headers and values,
  match each value with the corresponding header.
- If the question asks for accuracy and the evidence
  provides a "Percentage correct" metric for the
  relevant classifier, use that value as the reported
  accuracy.
- Give the numerical value exactly as shown in the evidence.
- Do not write phrases such as "96 Percentage correct".
- Use natural wording such as "96%".
- Mention the page number when possible.
- Keep the answer short and direct.
- If the evidence genuinely does not contain the answer,
  say:
  "The provided evidence does not contain enough information."

Question:
{question}

Retrieved Evidence:
{evidence}

Final Answer:
"""

    answer = generate_answer(prompt)

    sources = []

    for result in results:
        sources.append({
            "page": result["page"],
            "chunk_index": result["chunk_index"]
        })

    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }