import os
import re
from pathlib import Path
import pypdf
import pdfplumber
import pandas as pd
from config import CHUNK_SIZE, CHUNK_OVERLAP
from knowledge_db import store_chunk
from vector_retriever import index_chunk_vector  # Adjust to your vector_retriever insert function




def clean_text(text: str) -> str:
    """Cleans excess whitespace while strictly preserving structural linebreaks."""
    if not text:
        return ""
    # Fix hyphenation across linebreaks (e.g. "connec- \ntion" -> "connection")
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    # Replace multiple horizontal spaces/tabs with a single space (keep newlines!)
    text = re.sub(r'[^\S\r\n]+', ' ', text)
    # Normalize 3+ newlines to double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def is_toc_page(text: str) -> bool:
    """Detects and skips Table of Contents / Index pages to avoid false retrieval."""
    if not text:
        return False
    # Frequent dot leaders (e.g., "Architecture ............... 12")
    if len(re.findall(r"\.{4,}", text)) >= 3:
        return True
    
    first_lines = "\n".join(text.split("\n")[:5]).lower()
    toc_indicators = ["table of contents", "index", "list of figures", "list of tables"]
    return any(ind in first_lines for ind in toc_indicators)


def extract_tables_as_markdown(page) -> str:
    """Converts structured PDF tables into standard Markdown tables."""
    try:
        tables = page.extract_tables()
        if not tables:
            return ""
        
        md_tables = []
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            # Clean headers and rows
            header = [str(cell or "").strip().replace("\n", " ") for cell in table[0]]
            if not any(header):
                continue
                
            divider = ["---"] * len(header)
            rows = []
            for row in table[1:]:
                clean_row = [str(cell or "").strip().replace("\n", " ") for cell in row]
                rows.append("| " + " | ".join(clean_row) + " |")
                
            table_md = "\n| " + " | ".join(header) + " |\n| " + " | ".join(divider) + " |\n" + "\n".join(rows) + "\n"
            md_tables.append(table_md)
            
        return "\n".join(md_tables)
    except Exception:
        return ""


def extract_text_from_pdf(pdf_path: str):
    pages_data = []
    
    # 1. Primary extractor: pdfplumber with table awareness
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                
                # Filter out pure Table of Contents/Index pages
                if is_toc_page(page_text):
                    continue
                
                cleaned = clean_text(page_text)
                table_md = extract_tables_as_markdown(page)
                
                if table_md:
                    cleaned = cleaned + "\n\n### Data Table:\n" + table_md

                if len(cleaned.strip()) > 20:
                    pages_data.append({"page": page_idx + 1, "text": cleaned})
    except Exception as e:
        print(f"[Chunker Warning] pdfplumber error on {pdf_path}: {e}")

    # 2. Fallback to pypdf
    if not pages_data or sum(len(p["text"]) for p in pages_data) < 50:
        try:
            reader = pypdf.PdfReader(pdf_path)
            for idx, page in enumerate(reader.pages):
                raw = page.extract_text() or ""
                if is_toc_page(raw):
                    continue
                extracted = clean_text(raw)
                if len(extracted) > 20:
                    pages_data.append({"page": idx + 1, "text": extracted})
        except Exception as e:
            print(f"[Chunker Error] pypdf error: {e}")

    # 3. OCR Fallback for scanned/image PDFs
    if not pages_data:
        try:
            import pytesseract
            with pdfplumber.open(pdf_path) as pdf:
                for idx, page in enumerate(pdf.pages):
                    pil_img = page.to_image(resolution=200).original
                    ocr_text = pytesseract.image_to_string(pil_img)
                    cleaned = clean_text(ocr_text)
                    if len(cleaned) > 20 and not is_toc_page(cleaned):
                        pages_data.append({"page": idx + 1, "text": cleaned})
        except Exception as ocr_err:
            print(f"[Chunker Warning] OCR not available: {ocr_err}")

    return pages_data


def extract_text_from_docx(docx_path: str):
    """Extracts text and tables from Microsoft Word (.docx) files."""
    try:
        import docx
        doc = docx.Document(docx_path)
        blocks = []

        # Read paragraphs
        for p in doc.paragraphs:
            val = p.text.strip()
            if val:
                blocks.append(val)

        # Read tables into markdown
        for table in doc.tables:
            rows_data = []
            for row in table.rows:
                row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                if any(row_cells):
                    rows_data.append("| " + " | ".join(row_cells) + " |")
            if len(rows_data) > 1:
                header = rows_data[0]
                cols_count = len(table.rows[0].cells)
                divider = "| " + " | ".join(["---"] * cols_count) + " |"
                blocks.append("\n" + header + "\n" + divider + "\n" + "\n".join(rows_data[1:]) + "\n")

        full_doc = "\n\n".join(blocks)
        return [{"page": 1, "text": full_doc}] if len(full_doc) > 20 else []
    except Exception as e:
        print(f"[Chunker Warning] Word docx extraction failed: {e}")
        return []


def extract_text_from_csv(csv_path: str):
    """Converts CSV rows into clean Markdown tables so vector & BM25 search keep column context."""
    try:
        df = pd.read_csv(csv_path)
        md_table = df.to_markdown(index=False)
        return [{"page": 1, "text": md_table}] if md_table else []
    except Exception as e:
        print(f"[Chunker Warning] CSV extraction failed on {csv_path}: {e}")
        return []


def extract_text_from_excel(excel_path: str):
    """Converts each Excel sheet into Markdown tables."""
    try:
        excel_file = pd.ExcelFile(excel_path)
        sheets_data = []
        for idx, sheet_name in enumerate(excel_file.sheet_names):
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            md_table = df.to_markdown(index=False)
            if md_table:
                sheet_text = f"### Sheet: {sheet_name}\n\n{md_table}"
                sheets_data.append({"page": idx + 1, "text": sheet_text})
        return sheets_data
    except Exception as e:
        print(f"[Chunker Warning] Excel extraction failed on {excel_path}: {e}")
        return []


def extract_text_from_plain(file_path: str):
    """Handles .txt, .md, .log, and code files."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = clean_text(f.read())
        return [{"page": 1, "text": content}] if len(content) > 10 else []
    except Exception as e:
        print(f"[Chunker Warning] Plain text extraction failed on {file_path}: {e}")
        return []


def extract_document(file_path: str):
    """
    Unified entry point. Automatically routes any supported file extension 
    to the correct extractor, returning standard: [{'page': int, 'text': str}, ...]
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    elif ext == ".csv":
        return extract_text_from_csv(file_path)
    elif ext in [".xlsx", ".xls"]:
        return extract_text_from_excel(file_path)
    elif ext in [".txt", ".md", ".json", ".log"]:
        return extract_text_from_plain(file_path)
    else:
        print(f"[Chunker Skip] Unsupported file format: {ext} for {file_path}")
        return []


def recursive_chunk_text(text: str, chunk_size: int = 500, overlap: int = 100):
    """
    Structure-Preserving Recursive Chunker:
    Preserves lists, indentation, linebreaks, and Markdown tables.
    """
    if not text:
        return []

    # Split on double newlines to treat each logical block (list item, paragraph, table) intact
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    chunks = []
    current_blocks = []
    current_word_count = 0

    for block in blocks:
        block_words = len(block.split())
        
        # If adding block exceeds size, seal current chunk
        if current_word_count + block_words > chunk_size and current_blocks:
            chunks.append("\n\n".join(current_blocks))
            # Keep the last block for logical context overlap instead of chopping arbitrary words
            current_blocks = [current_blocks[-1]] if len(current_blocks) > 1 else []
            current_word_count = sum(len(b.split()) for b in current_blocks)

        current_blocks.append(block)
        current_word_count += block_words

    if current_blocks:
        chunks.append("\n\n".join(current_blocks))

    # Strip duplicate identical chunks if any
    unique_chunks = []
    seen = set()
    for c in chunks:
        key = c[:100].strip()
        if key not in seen and len(c.strip()) > 30:
            seen.add(key)
            unique_chunks.append(c)

    return unique_chunks


DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
SUPPORTED_EXTS = {".pdf", ".docx", ".doc", ".csv", ".xlsx", ".xls", ".txt", ".md", ".json", ".log"}


def run_ingestion_pipeline():
    """Scans Data/ folder, extracts content across all formats, and indexes chunks."""
    if not DATA_DIR.exists():
        print(f"[Ingest Error] Data directory not found at: {DATA_DIR}")
        return

    files_found = [p for p in DATA_DIR.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
    
    if not files_found:
        print(f"[Ingest] No supported documents found in {DATA_DIR}")
        return

    print(f"[*] Found {len(files_found)} files to ingest. Starting pipeline...")
    total_chunks_indexed = 0

    for file_path in files_found:
        filename = file_path.name
        print(f" -> Processing: {filename}")

        # 1. Multi-format extraction
        pages_data = extract_document(str(file_path))
        if not pages_data:
            print(f"    [!] No readable content extracted from {filename}")
            continue

        file_chunk_count = 0
        for page_obj in pages_data:
            page_num = page_obj.get("page", 1)
            raw_text = page_obj.get("text", "")

            # 2. Structure-preserving chunking
            chunks = recursive_chunk_text(raw_text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)

            for chunk_idx, chunk_text_content in enumerate(chunks):
                # 3. Store into SQLite (rag_knowledge.db)
                chunk_id = f"{filename}_p{page_num}_c{chunk_idx}"
                store_chunk(chunk_id=chunk_id, filename=filename, page=page_num, chunk_text=chunk_text_content)

                # 4. Insert into FAISS/Dense Vector index
                index_chunk_vector(chunk_id=chunk_id, chunk_text=chunk_text_content)

                file_chunk_count += 1

        total_chunks_indexed += file_chunk_count
        print(f"    [+] Indexed {file_chunk_count} chunks from {filename}")

    print(f"\n[✓] Ingestion complete! Total chunks indexed across all formats: {total_chunks_indexed}")


if __name__ == "__main__":
    run_ingestion_pipeline()