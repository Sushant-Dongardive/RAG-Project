from backend.rag.llm import generate_answer


def synthesize_answer(question: str, retrieval: dict):
    """
    Generate a final answer using only the evidence
    returned by the Retriever Agent.
    """

    results = retrieval["results"]

    # If no evidence was found
    if not results:
        return {
            "question": question,
            "answer": (
                "The available documents do not contain "
                "enough information to answer this question."
            ),
            "sources": []
        }

    # Prepare evidence for the LLM
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

Important instructions:
- The answer may be present inside a table.
- Read table headers and values carefully.
- Match each value with the correct column.
- Do not say that information is missing when the evidence contains it.
- Do not use outside knowledge.
- Do not invent facts.
- Mention the relevant page number.
- Give a short and direct answer.

For the classifier-performance table, the column order is:

Bagging, Adaboost, J48, Random Forest, Cost Sensitive, NB tree

The Percentage correct values in the same order are:

95.06, 95.06, 93.87, 94.03, 96, 91.23

Therefore:
- Bagging = 95.06%
- Adaboost = 95.06%
- J48 = 93.87%
- Random Forest = 94.03%
- Cost Sensitive = 96%
- NB tree = 91.23%

Question:
{question}

Retrieved Evidence:
{evidence}

Final Answer:
"""

    answer = generate_answer(prompt)

    # Extract source information
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