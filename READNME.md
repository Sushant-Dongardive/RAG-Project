Technology Stack Justification
FastAPI: High-performance async web framework. Essential for handling concurrent LLM/database I/O and provides auto-generated API docs.

Uvicorn: High-speed ASGI server required to execute FastAPI's asynchronous code.

PyMuPDF (fitz): Fast C-based PDF engine. Extracts text by visual blocks (vital for smart chunking) and retains exact document metadata.

Swagger UI
What it is: An auto-generated, interactive web interface for your FastAPI backend.
Chunking is the process of breaking down a large piece of text into smaller, manageable segments (or "chunks").

In the context of the RAG (Retrieval-Augmented Generation) project you are building, once you extract the text from your uploaded PDF, you will need to "chunk" that text before feeding it to an AI.

An embedding library is a software toolkit that takes text (like words, sentences, or your PDF chunks) and converts it into a list of numbers called a vector embedding.

Computers and AI models cannot directly calculate mathematical similarity between words; they only understand numbers. An embedding library downloads, runs, and manages specialized machine learning models that turn text into numerical coordinates while preserving semantic meaning.

Library:-sentence-transformersLocal
Type:- Local (Hugging Face)
Key feature :-Runs completely on your laptop for free; very fast with  models like all-MiniLM-L6-v2

FAISS (Facebook AI Similarity Search) is an open-source library built by Meta AI specifically designed to search through massive collections of vector arrays extremely fast.

How FAISS Works
FAISS uses similarity metrics (like Euclidean distance or Cosine similarity) and indexing algorithms:

Flat Index (IndexFlatL2): Compares the search vector against every single vector directly. It guarantees 100% precision and works well for small-to-medium datasets (like your 76 chunks).

Approximate Nearest Neighbors (ANN / IndexIVFFlat): Groups similar vectors into clusters. When a query arrives, it only searches the most relevant cluster rather than the entire database, achieving massive speed gains at scale.

Ollama is an open-source tool that allows you to download, manage, and run Large Language Models (LLMs) locally on your own computer.  Often described as "Docker for AI models," it packages all the complex machinery needed for local AI—weights, model architectures, memory quantization, and GPU acceleration—into simple command-line tools and local APIs.  

What Makes It UsefulOne-Command Setup:
1:-
 Instead of dealing with gigabytes of raw weights and complicated machine-learning frameworks, you can pull and run open-weight models (like Llama 3, Mistral, Gemma, or Qwen) with a single command:  Bashollama run llama3

2:-
Local & Private: Everything runs directly on your machine's CPU and GPU. No data is sent to external cloud APIs, making it completely private, free of token fees, and usable offline.

3:-
Built-in REST API: Ollama automatically hosts a lightweight, OpenAI-compatible local server (typically at http://localhost:11434). This makes it simple to integrate local models into Python scripts, desktop apps, or local chat UIs.

How It Fits Into Your RAG ProjectIn a Retrieval-Augmented Generation (RAG) pipeline, you need two types of models:
1:-
An Embedding Model: To convert document chunks and search queries into numerical vectors (e.g., ollama pull nomic-embed-text).

2:-
A Generator LLM: To read the retrieved text chunks and write the final answer.

Instead of paying for third-party cloud API keys like OpenAI or Anthropic, you can install Ollama and use its Python library to handle both embeddings and generation completely offline: