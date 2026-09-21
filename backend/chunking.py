import re
from pathlib import Path
import pypdf
import pdfplumber
from config import CHUNK_SIZE, CHUNK_OVERLAP

def clean_text(text: str) -> str:
    """Removes weird artifacts, fixes hyphenated linebreaks, and normalizes spaces."""
    if not text:
        return ""
    # Fix hyphenation across newlines (e.g. "connec- \ntion" -> "connection")
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    # Replace multiple spaces/tabs with single space
    text = re.sub(r'[ \t]+', ' ', text)
    # Normalize excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_text_from_pdf(pdf_path: str):
    pages_data = []
    
    # 1. Primary extractor: pdfplumber (retains layout & tables best)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                text = page.extract_text(layout=True) or page.extract_text() or ""
                cleaned = clean_text(text)
                if len(cleaned) > 20:
                    pages_data.append({"page": page_idx + 1, "text": cleaned})
    except Exception as e:
        print(f"[Chunker Warning] pdfplumber error on {pdf_path}: {e}")

    # 2. Fallback to pypdf
    if not pages_data or sum(len(p["text"]) for p in pages_data) < 50:
        try:
            reader = pypdf.PdfReader(pdf_path)
            for idx, page in enumerate(reader.pages):
                extracted = clean_text(page.extract_text() or "")
                if len(extracted) > 20:
                    pages_data.append({"page": idx + 1, "text": extracted})
        except Exception as e:
            print(f"[Chunker Error] pypdf error: {e}")

    # 3. OCR Fallback for scanned documents
    if not pages_data:
        try:
            import pytesseract
            from PIL import Image
            with pdfplumber.open(pdf_path) as pdf:
                for idx, page in enumerate(pdf.pages):
                    pil_img = page.to_image(resolution=200).original
                    ocr_text = pytesseract.image_to_string(pil_img)
                    cleaned = clean_text(ocr_text)
                    if len(cleaned) > 20:
                        pages_data.append({"page": idx + 1, "text": cleaned})
        except Exception as ocr_err:
            print(f"[Chunker Warning] OCR not available: {ocr_err}")

    return pages_data

def recursive_chunk_text(text: str, chunk_size: int = 500, overlap: int = 100):
    """
    Semantic Recursive Chunker: Splits by double newline (paragraphs), then sentences,
    ensuring contextual completeness.
    """
    if not text:
        return []

    # First split by paragraphs
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_words = para.split()
        if not para_words:
            continue
            
        if current_length + len(para_words) <= chunk_size:
            current_chunk.extend(para_words)
            current_length += len(para_words)
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            # Handle paragraphs larger than chunk_size
            if len(para_words) > chunk_size:
                start = 0
                while start < len(para_words):
                    end = start + chunk_size
                    chunks.append(" ".join(para_words[start:end]))
                    start += (chunk_size - overlap)
                current_chunk = []
                current_length = 0
            else:
                # Start new chunk with overlap
                overlap_words = current_chunk[-overlap:] if len(current_chunk) >= overlap else current_chunk
                current_chunk = overlap_words + para_words
                current_length = len(current_chunk)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return [c for c in chunks if len(c.strip()) > 30]