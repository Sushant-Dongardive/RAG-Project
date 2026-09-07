from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil

from backend.ingestion.pdf import extract_text_from_pdf

router = APIRouter()

UPLOAD_DIR = Path("data/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    pages = extract_text_from_pdf(str(file_path))

    return {
        "filename": file.filename,
        "total_pages": len(pages),
        "message": "PDF uploaded and text extracted successfully."
    }