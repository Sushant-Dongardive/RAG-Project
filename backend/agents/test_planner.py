from backend.agents.planner import plan_query


questions = [
    "What was the accuracy of the cost-sensitive classifier?",
    "Explain this Python function.",
    "Compare two fingerprint verification methods.",
    "What is the capital of India?"
]


for question in questions:

    result = plan_query(question)

    print("\n" + "=" * 60)
    print("Question:")
    print(question)

    print("\nPlanner result:")
    print(result)
    