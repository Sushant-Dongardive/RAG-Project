Technology Stack Justification
FastAPI: High-performance async web framework. Essential for handling concurrent LLM/database I/O and provides auto-generated API docs.

Uvicorn: High-speed ASGI server required to execute FastAPI's asynchronous code.

PyMuPDF (fitz): Fast C-based PDF engine. Extracts text by visual blocks (vital for smart chunking) and retains exact document metadata.
