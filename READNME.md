Technology Stack Justification
FastAPI: High-performance async web framework. Essential for handling concurrent LLM/database I/O and provides auto-generated API docs.

Uvicorn: High-speed ASGI server required to execute FastAPI's asynchronous code.

PyMuPDF (fitz): Fast C-based PDF engine. Extracts text by visual blocks (vital for smart chunking) and retains exact document metadata.

Swagger UI
What it is: An auto-generated, interactive web interface for your FastAPI backend.
Chunking is the process of breaking down a large piece of text into smaller, manageable segments (or "chunks").

In the context of the RAG (Retrieval-Augmented Generation) project you are building, once you extract the text from your uploaded PDF, you will need to "chunk" that text before feeding it to an AI.