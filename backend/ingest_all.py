import os
import sqlite3
from pathlib import Path
import pypdf
import pdfplumber

from config import DB_PATH, DOCS_DIR
from vector_retriever import VectorStore
from hybrid_retriever import HybridRetriever

def extract_pdf_text(filepath):
    pages = []
    # 1. Try pdfplumber
    try:
        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages):
                txt = page.extract_text() or ""
                if len(txt.strip()) > 10:
                    pages.append((i + 1, txt.strip()))
    except Exception as e:
        print(f"pdfplumber error on {filepath.name}: {e}")

    # 2. Fallback to pypdf if empty
    if not pages:
        try:
            reader = pypdf.PdfReader(filepath)
            for i, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                if len(txt.strip()) > 10:
                    pages.append((i + 1, txt.strip()))
        except Exception as e:
            print(f"pypdf error on {filepath.name}: {e}")

    return pages

def chunk_text(text, chunk_size=400, overlap=80):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 20:
            chunks.append(chunk)
        if end >= len(words):
            break
        start += max(1, chunk_size - overlap)
    return chunks

def run():
    print(f"Scanning directory: {DOCS_DIR}")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    pdf_files = list(DOCS_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"NO PDF FILES FOUND in {DOCS_DIR}! Check folder path.")
        return

    for pdf_path in pdf_files:
        filename = pdf_path.name
        print(f"\n--> Processing: {filename}")
        
        pages = extract_pdf_text(pdf_path)
        print(f"    Extracted {len(pages)} pages.")

        # Register dataset
        cursor.execute("""
            INSERT OR REPLACE INTO datasets (name, file_path, file_type, total_pages)
            VALUES (?, ?, 'pdf', ?)
        """, (filename, str(pdf_path), len(pages) or 1))
        
        cursor.execute("SELECT id FROM datasets WHERE name = ?", (filename,))
        dataset_id = cursor.fetchone()[0]

        # Clear existing chunks for this file
        cursor.execute("DELETE FROM document_chunks WHERE dataset_id = ?", (dataset_id,))

        total_chunks = 0
        for page_num, page_content in pages:
            chunks = chunk_text(page_content)
            for c_idx, chunk in enumerate(chunks):
                cursor.execute("""
                    INSERT INTO document_chunks (dataset_id, dataset_name, page_number, chunk_index, content)
                    VALUES (?, ?, ?, ?, ?)
                """, (dataset_id, filename, page_num, c_idx, chunk))
                total_chunks += 1

        print(f"    Saved {total_chunks} chunks to database.")

    conn.commit()
    conn.close()
    print("\n✅ Ingestion complete! All PDF files are now saved in SQLite.")

if __name__ == "__main__":
    run()