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

Your task is to verify whether the generated answer is supported
by the retrieved evidence.

Rules:
- Use ONLY the retrieved evidence.
- Do not use outside knowledge.
- Check factual claims carefully.
- Check numerical values carefully.
- Do not reject an answer merely because the evidence
  does not repeat the claim as a normal sentence.
- Tables are important evidence.

TABLE INTERPRETATION:

PDF text extraction may flatten a table into a sequence of
headers followed by a sequence of values.

When this happens, values in the same row correspond
positionally to the headers in the same order.

For example, if a table contains:

Headers:
A B C D

Values:
10 20 30 40

then the correct mapping is:

A → 10
B → 20
C → 30
D → 40

Use this positional mapping when checking numerical claims
from flattened tables.

If the generated answer identifies a value for a particular
column and that value is supported by the corresponding
position in the retrieved table, consider the claim supported.

Also distinguish between:
- a metric name
- its value
- the entity/classifier/column to which that value belongs.

If the question asks for accuracy and the table uses a metric
such as "Percentage correct", determine whether that metric
is the relevant accuracy measure from the table context.

Return exactly:

Status: VERIFIED
or
Status: NOT_VERIFIED
or
Status: CONTRADICTED

Reason: short explanation


Question:
{question}

Generated Answer:
{answer}

Retrieved Evidence:
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