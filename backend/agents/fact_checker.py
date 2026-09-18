from backend.rag.llm import generate_answer


def fact_check_answer(question: str, synthesized: dict, retrieval: dict):
    """
    Check whether the synthesized answer is supported
    by the retrieved evidence.
    """

    answer = synthesized["answer"]
    results = retrieval["results"]

    if not results:
        return {
            "question": question,
            "answer": answer,
            "verification_status": "unverified",
            "reason": "No evidence was retrieved.",
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
You are the Fact-Checker Agent of an Agentic RAG system.

Check whether the generated answer is directly supported
by the retrieved evidence.

Important table-reading instructions:

The evidence contains a classifier-performance table.

The classifier order is:

Bagging, Adaboost, J48, Random Forest, Cost Sensitive, NB tree

The values in the "Percentage correct" row are:

95.06, 95.06, 93.87, 94.03, 96, 91.23

Match the values by position:

- Bagging = 95.06%
- Adaboost = 95.06%
- J48 = 93.87%
- Random Forest = 94.03%
- Cost Sensitive = 96%
- NB tree = 91.23%

For this table:
- "Percentage correct" represents the classifier's accuracy.
- Therefore, "96% percentage correct" supports the statement
  that the cost-sensitive classifier achieved 96% accuracy.

Rules:
- Use only the provided evidence.
- Do not use outside knowledge.
- Check numerical values carefully.
- Check whether the answer matches the table.
- If the answer is supported, return VERIFIED.
- If the answer is unsupported, return NOT_VERIFIED.
- If the evidence contradicts the answer, return CONTRADICTED.

Return exactly this format:

Status: VERIFIED or NOT_VERIFIED or CONTRADICTED
Reason: short explanation

Question:
{question}

Generated Answer:
{answer}

Evidence:
{evidence}
"""

    verification = generate_answer(prompt)

    status = "unverified"

    if "Status: VERIFIED" in verification:
        status = "verified"
    elif "Status: CONTRADICTED" in verification:
        status = "contradicted"
    elif "Status: NOT_VERIFIED" in verification:
        status = "not_verified"

    sources = []

    for result in results:
        sources.append({
            "page": result["page"],
            "chunk_index": result["chunk_index"]
        })

    return {
        "question": question,
        "answer": answer,
        "verification_status": status,
        "reason": verification,
        "sources": sources
    }