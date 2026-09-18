from backend.rag.hybrid_retrival import hybrid_search


def retrieve_documents(
    plan,
    chunks,
    vector_index,
    bm25_index,
    top_k=5
):
    """
    Retrieve evidence according to the Planner Agent's decision.
    """

    question = plan["question"]
    strategy = plan["retrieval_strategy"]

    # General questions do not need document retrieval
    if strategy == "general_llm":
        return {
            "question": question,
            "retrieval_strategy": strategy,
            "results": []
        }

    # Domain questions use hybrid retrieval
    if strategy == "hybrid_search":

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

        return {
            "question": question,
            "retrieval_strategy": strategy,
            "results": results
        }

    # Other strategies will be implemented later
    return {
        "question": question,
        "retrieval_strategy": strategy,
        "results": []
    }