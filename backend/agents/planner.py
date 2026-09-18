def plan_query(question: str):
    """
    Classify the user question and choose
    the appropriate retrieval strategy.
    """

    question_lower = question.lower()

    if any(
        word in question_lower
        for word in [
            "paper",
            "document",
            "research",
            "classifier",
            "accuracy",
            "algorithm",
            "dataset",
            "according to"
        ]
    ):
        query_type = "domain_question"
        retrieval_strategy = "hybrid_search"

    elif any(
        word in question_lower
        for word in [
            "code",
            "python",
            "java",
            "function",
            "class",
            "bug",
            "error"
        ]
    ):
        query_type = "code_question"
        retrieval_strategy = "code_search"

    elif any(
        word in question_lower
        for word in [
            "compare",
            "difference",
            "versus",
            "vs"
        ]
    ):
        query_type = "comparison_question"
        retrieval_strategy = "multi_document_search"

    else:
        query_type = "general_question"
        retrieval_strategy = "general_llm"

    return {
        "question": question,
        "query_type": query_type,
        "retrieval_strategy": retrieval_strategy
    }