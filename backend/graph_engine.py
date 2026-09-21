import os
import re
from hybrid_retriever import HybridRetriever
from self_rag import evaluate_groundedness
from web_search import search_global_web
from config import GEMINI_API_KEY

class AgenticRAGEngine:
    def __init__(self, hybrid_retriever: HybridRetriever):
        self.retriever = hybrid_retriever
        self.client = None
        self.legacy_model = None
        self.local_qa_pipe = None
        
        # Initialize Gemini API Client if key exists
        api_key = (GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")).strip()
        if api_key and not api_key.startswith("your_"):
            try:
                from google import genai
                self.client = genai.Client(api_key=api_key)
                print("[LLM] Google Gemini Client connected.")
            except Exception:
                try:
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=api_key)
                    self.legacy_model = legacy_genai.GenerativeModel("gemini-1.5-flash")
                    print("[LLM] Fallback google.generativeai connected.")
                except Exception as leg_err:
                    print(f"[LLM Error]: {leg_err}")

    def _init_local_qa(self):
        if self.local_qa_pipe is None:
            try:
                from transformers import pipeline
                self.local_qa_pipe = pipeline("question-answering", model="deepset/roberta-base-squad2")
            except Exception:
                self.local_qa_pipe = False

    def call_llm(self, system_instruction: str, user_prompt: str) -> str:
        full_prompt = f"{system_instruction}\n\n{user_prompt}"

        # 1. Official google.genai
        if self.client:
            try:
                from google.genai import types
                resp = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,  # Forces deterministic, consistent output
                        top_p=1.0,
                    ),
                )
                if resp and resp.text:
                    return resp.text.strip()
            except Exception as e:
                print(f"[Gemini Client Error]: {e}")

        # 2. Legacy SDK fallback
        if self.legacy_model:
            try:
                resp = self.legacy_model.generate_content(
                    full_prompt,
                    generation_config={"temperature": 0.0}  # Deterministic fallback
                )
                if resp and resp.text:
                    return resp.text.strip()
            except Exception as e:
                print(f"[Legacy Gemini Error]: {e}")

        # 3. Local offline synthesizer fallback
        return self._local_grounded_synthesizer(user_prompt)

        # 3. High quality local heuristic extraction
        return self._local_grounded_synthesizer(user_prompt)

    def _local_grounded_synthesizer(self, prompt: str) -> str:
        if "Context:" not in prompt or "Question:" not in prompt:
            return "Unable to parse context for synthesis."

        context = prompt.split("Context:")[1].split("Question:")[0].strip()
        question = prompt.split("Question:")[1].split("Answer:")[0].strip()

        # Local Transformer QA check
        self._init_local_qa()
        if self.local_qa_pipe:
            try:
                res = self.local_qa_pipe(question=question, context=context[:2000])
                if res and res.get("score", 0) > 0.15 and len(res.get("answer", "")) > 3:
                    ans = res["answer"].strip()
                    for s in re.split(r"(?<=[.?!])\s+", context):
                        if ans.lower() in s.lower():
                            return s.strip()
                    return f"According to the document records: {ans}"
            except Exception:
                pass

        # Multi-Sentence Semantic Matcher
        clean_context = re.sub(r"\[.*?Page \d+\]:", "", context)
        sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", clean_context) if len(s.strip()) > 15]
        q_tokens = set([w.lower() for w in re.findall(r"\w+", question) if len(w) > 2])

        scored = []
        for s in sentences:
            s_tokens = set([w.lower() for w in re.findall(r"\w+", s)])
            overlap = len(q_tokens.intersection(s_tokens))

            # Numerical or metric prioritization
            if any(k in question.lower() for k in ["accuracy", "rate", "cost", "percent", "%", "score", "f1"]):
                if "%" in s or any(ch.isdigit() for ch in s):
                    overlap += 3
            # Conceptual prioritization
            if any(k in question.lower() for k in ["objective", "aim", "purpose", "system", "used", "technologies", "architecture"]):
                if any(k in s.lower() for k in ["propose", "developed", "using", "implements", "architecture", "system", "designed"]):
                    overlap += 2

            if overlap > 0:
                scored.append((overlap, s))

        scored.sort(key=lambda x: x[0], reverse=True)
        if scored:
            best_sentences = [scored[0][1]]
            if len(scored) > 1 and scored[1][0] >= scored[0][0] * 0.7:
                best_sentences.append(scored[1][1])
            res = " ".join(best_sentences)
            return res if res.endswith(".") else res + "."

        return "The document does not contain sufficient details to directly answer this question."

    def execute_rag(self, query: str, active_dataset: str = None):
        trace = []
        retrieved = []  # Explicitly initialized to avoid UnboundLocalError
        
        target = active_dataset if active_dataset and active_dataset != "ALL" else "All Datasets (Global Knowledge Base)"

        # 1. Planner Agent
        trace.append({
            "agent": "Planner Agent",
            "message": f"Analyzing query intent: '{query}'. Routing to local SQLite knowledge store (Target: {target})."
        })

        # 2. Retrieval Agent (BM25 + Dense FAISS via RRF)
        try:
            retrieved, dense_docs, bm25_docs = self.retriever.search(query, top_k=4, filter_dataset=active_dataset)
        except Exception as e:
            print(f"[Retriever Search Error]: {e}")
            retrieved = []

        if not retrieved:
            trace.append({
                "agent": "BM25 & Vector Retriever",
                "message": f"No relevant records found in target dataset: {target}."
            })
            return {
                "answer": "Answer is not present in the selected dataset.",
                "found_in_dataset": False,
                "sources": [],
                "trace": trace,
                "prompt_global_search": True
            }

        # Deduplicate citations while preserving order
        citations = []
        for d in retrieved:
            cite = f"{d['dataset_name']} (Page {d['page']})"
            if cite not in citations:
                citations.append(cite)

        trace.append({
            "agent": "BM25 & Vector Retriever",
            "message": f"Retrieved {len(retrieved)} records from SQLite: {', '.join(citations)}."
        })

        # 3. Synthesizer Agent
        trace.append({
            "agent": "Synthesizer Agent",
            "message": "Synthesizing answer using grounded context..."
        })

        context_blocks = [f"[Source: {d['dataset_name']} | Page {d['page']}]:\n{d['content']}" for d in retrieved]
        context_str = "\n\n".join(context_blocks)

        system_instruction = (
            "You are an expert, truthful AI knowledge engine. Your task is to answer the user's question "
            "thoroughly, accurately, and naturally based ONLY on the provided Context.\n"
            "- If the context has the answer, provide a fluent, complete, well-reasoned response.\n"
            "- Cite the page or section when relevant.\n"
            "- If the provided context does not contain the answer, reply with: 'NOT_IN_CONTEXT'."
        )

        user_prompt = f"Context:\n{context_str}\n\nQuestion: {query}\nAnswer:"

        raw_answer = self.call_llm(system_instruction, user_prompt)

        if "NOT_IN_CONTEXT" in raw_answer:
            return {
                "answer": "Answer is not present in the selected dataset.",
                "found_in_dataset": False,
                "sources": [],
                "trace": trace,
                "prompt_global_search": True
            }

        # 4. Self-RAG Fact-Checker Guardrail
        guardrail = evaluate_groundedness(query, retrieved, raw_answer)
        trace.append({
            "agent": "Fact-Checker (Self-RAG)",
            "message": f"Verification Status: {guardrail['status']}."
        })

        return {
            "answer": raw_answer,
            "found_in_dataset": True,
            "sources": citations,
            "trace": trace,
            "prompt_global_search": False
        }

    def execute_global_ai(self, query: str):
        web_info = search_global_web(query, max_results=4)
        web_context = "\n".join([f"- {w['title']}: {w['snippet']}" for w in web_info if w.get('snippet')])

        system_instruction = (
            "You are an intelligent global AI assistant (like ChatGPT). Answer the user's question "
            "comprehensively and helpfully using the provided live search results."
        )
        user_prompt = f"Live Web Context:\n{web_context}\n\nQuestion: {query}\nAnswer:"

        ans = self.call_llm(system_instruction, user_prompt)
        return ans, web_info