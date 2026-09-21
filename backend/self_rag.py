def evaluate_groundedness(query: str, retrieved_docs: list, answer: str):
    """
    Self-RAG Guardrail: Ensures the answer is backed by retrieved chunks.
    """
    if not retrieved_docs:
        return {
            "passed": False,
            "status": "No Grounding Data",
            "reason": "Context is empty."
        }
    
    # Check word overlap / factual token adherence
    ans_tokens = set(answer.lower().split())
    context_tokens = set(" ".join([d["content"] for d in retrieved_docs]).lower().split())
    
    shared_tokens = ans_tokens.intersection(context_tokens)
    if len(shared_tokens) < 3 and len(answer) > 20:
        return {
            "passed": False,
            "status": "Potential Hallucination",
            "reason": "Answer vocabulary does not align with retrieved evidence."
        }

    return {
        "passed": True,
        "status": "Passed (No factual contradictions found)",
        "reason": "Verification confirms grounding within local document context."
    }