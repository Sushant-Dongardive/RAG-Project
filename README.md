# Retrieval-Augmented Generation (RAG) Project

An end-to-end RAG application capable of ingesting local text documents, parsing them into vector embeddings, and providing context-aware responses to user queries.

## 📁 Repository Structure
- `backend/`: Core logic containing data ingestion, vector database setup, and the LLM API integration.
- `frontend/`: Interactive user interface to chat with your documents.
- `Data/Documents/`: Local directory holding target data files for indexing (kept out of Git history).

## 🚀 Getting Started

### 1. Clone & Environment Setup
Ensure you have Python 3.10+ installed. Navigate to the root directory and activate your environment:
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate
# On Mac/Linux:
source venv/bin/activate
```

### 2. Install Dependencies
Navigate to the backend and install the required modules:
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Secrets
Create a `.env` file inside the `backend` folder and populate your keys:
```env
OPENAI_API_KEY=your_secret_key_here
```

### 4. Run the Application
- Run the ingestion pipeline or backend engine inside `backend/`.
- Run the web app server inside `frontend/`.
