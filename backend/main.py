from fastapi import FastAPI
from backend.ingestion.pdf import extract_text_from_pdf

app = FastAPI(title="Agentic RAG Platform")


@app.get("/")
def home():
    return {
        "message": "Agentic RAG Platform is running!"
        
    }
    
@app.get("/extract")
def extract_my_pdf():
    file_path = "data/documents/distorted.pdf"
    
    # Call the function from your second file
    pages = extract_text_from_pdf(file_path)
    
    # Return the results so they display on the web
    return {
        "total_pages": len(pages),
        "extracted_data": pages
      
    }