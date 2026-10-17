import re

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
    "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
    "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should",
    "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "would", "you", "your", "yours", "yourself", "yourselves", "according",
    "based", "provided", "context", "document", "question", "answer", "mention", "mentions"
}

def extract_keywords(text: str) -> set:
    words = re.findall(r"\b[a-zA-Z0-9_\-\.%]+\b", (text or "").lower())
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}

def extract_numbers_and_metrics(text: str) -> set:
    """Extracts numbers, percentages, and metrics to verify numerical faithfulness."""
    return set(re.findall(r"\b\d+(?:\.\d+)?%?", text or ""))


def evaluate_groundedness(query: str, retrieved_docs: list, answer: str):
    """
    Self-RAG Guardrail: Ensures the answer is backed by retrieved chunks.
    """
    if not retrieved_docs:
        return {
            "passed": False,
            "status": "No Grounding Data",
            "reason": "Context is empty.",
            "grounding_score": 0.0
        }
    
    if not answer or answer.strip() in ["NOT_IN_CONTEXT", "Answer is not present in the selected dataset."]:
        return {
            "passed": True,
            "status": "Grounded Abstention",
            "reason": "Model correctly abstained from ungrounded generation.",
            "grounding_score": 1.0
        }
        
    combined_context = " ".join([d.get("content", "") for d in retrieved_docs])
    
    # 1. Numerical & Metric Consistency Check
    ans_numbers = extract_numbers_and_metrics(answer)
    ctx_numbers = extract_numbers_and_metrics(combined_context)
    
    # Filter out common formatting numbers (e.g., list numbers like '1.', '2.')
    unsupported_numbers = []
    for num in ans_numbers:
        # Check if number exists as number or percentage in context
        raw_num = num.replace("%", "")
        if num not in ctx_numbers and raw_num not in ctx_numbers:
            # Skip single digit ordinals if list-like
            if len(raw_num) == 1:
                continue
            unsupported_numbers.append(num)

    if unsupported_numbers:
        return {
            "passed": False,
            "status": "Numerical Discrepancy",
            "reason": f"Answer contains metrics not in source context: {', '.join(unsupported_numbers[:3])}.",
            "grounding_score": 0.3
        }
        
    # 2. Informative Keyword Overlap
    ans_keywords = extract_keywords(answer)
    ctx_keywords = extract_keywords(combined_context)

    if not ans_keywords:
        return {
            "passed": True,
            "status": "Passed (Short Factoid)",
            "reason": "Answer contains direct concise match.",
            "grounding_score": 1.0
        }  
        
    shared_keywords = ans_keywords.intersection(ctx_keywords)
    overlap_ratio = len(shared_keywords) / max(len(ans_keywords), 1) 
    
    if overlap_ratio < 0.25 and len(answer) > 40:
        return {
            "passed": False,
            "status": "Potential Hallucination",
            "reason": f"Low factual overlap with retrieved evidence ({round(overlap_ratio * 100, 1)}% alignment).",
            "grounding_score": round(overlap_ratio, 2)
        }

    return {
        "passed": True,
        "status": f"Passed ({round(overlap_ratio * 100, 1)}% grounding alignment)",
        "reason": "Verification confirms grounding within local document context.",
        "grounding_score": round(overlap_ratio, 2)
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