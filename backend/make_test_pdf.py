import os
from pathlib import Path

# Ensure output directory exists
DOCS_DIR = Path(__file__).resolve().parent.parent / "Data" / "Documents"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
pdf_path = DOCS_DIR / "test_research_paper.pdf"

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title & Metadata
    title_style = ParagraphStyle(name="TitleStyle", parent=styles["Heading1"], fontSize=18, spaceAfter=12)
    heading_style = ParagraphStyle(name="H2", parent=styles["Heading2"], fontSize=14, spaceAfter=8)
    body_style = ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=8)

    # --- Page 1: Abstract & System Architecture ---
    story.append(Paragraph("Scalable Agentic Retrieval-Augmented Generation for Technical Audits", title_style))
    story.append(Paragraph("<b>Authors:</b> Research & Development Labs (Capstone 2026)", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Abstract & System Architecture", heading_style))
    abstract_text = (
        "This paper introduces an end-to-end Agentic RAG framework designed for mission-critical document "
        "auditing. The architecture combines dense FAISS vector embeddings (MiniLM-L6) with sparse BM25 indexing "
        "via Reciprocal Rank Fusion (RRF with parameter k=60). In high-concurrency benchmarks, the system achieved "
        "a sub-200ms latency profile across 100,000 indexed records."
    )
    story.append(Paragraph(abstract_text, body_style))

    arch_text = (
        "The system pipeline comprises three core micro-agents: the Planner Agent (which determines retrieval routing), "
        "the Synthesis Agent (which aggregates grounded document context), and the Self-RAG Fact-Checker (which verifies "
        "groundedness against source context to eliminate hallucinations)."
    )
    story.append(Paragraph(arch_text, body_style))
    story.append(PageBreak())

    # --- Page 2: Benchmark Results & Table 1 ---
    story.append(Paragraph("2. Experimental Results & Performance Metrics", heading_style))
    bench_text = (
        "We evaluated the retrieval and classification framework across four standard evaluation datasets. "
        "The neural Cross-Encoder re-ranker achieved a Mean Reciprocal Rank (MRR@10) of 0.892, outperforming "
        "baseline vector search by 14.3%."
    )
    story.append(Paragraph(bench_text, body_style))

    # Table of metrics
    table_data = [
        ["Model Architecture", "Precision", "Recall", "F1-Score", "Accuracy"],
        ["Baseline BM25", "78.4%", "81.2%", "79.7%", "80.1%"],
        ["Dense FAISS (MiniLM)", "85.1%", "88.6%", "86.8%", "86.5%"],
        ["Hybrid (BM25 + Dense RRF)", "91.3%", "92.7%", "92.0%", "92.4%"],
        ["Agentic Hybrid + Re-Ranker", "95.8%", "96.4%", "96.1%", "96.7%"]
    ]
    t = Table(table_data, colWidths=[160, 70, 70, 70, 70])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e1b4b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "<b>Table 1:</b> Quantitative comparison of retrieval-augmented classification strategies. "
        "As reported in Table 1, the Agentic Hybrid with Cross-Encoder achieved the highest overall accuracy of 96.7% "
        "and an F1-Score of 96.1%.", body_style
    ))
    story.append(PageBreak())

    # --- Page 3: Implementation & Technology Stack ---
    story.append(Paragraph("3. Technical Implementation & Deployment", heading_style))
    tech_text = (
        "The backend runtime is constructed using FastAPI and Uvicorn running on Python 3.11. "
        "Local vector stores utilize SQLite for relational metadata and FAISS IndexFlatIP for normalized inner-product "
        "similarity computation. For document ingestion, layout preservation is guaranteed via pdfplumber with "
        "pytesseract OCR fallback routines. The system is container-ready and deploys under standard Linux or Windows runtimes."
    )
    story.append(Paragraph(tech_text, body_style))

    doc.build(story)
    print(f"Generated: {pdf_path}")

except ImportError:
    # Fallback to fpdf2 or pure python if reportlab isn't installed
    os.system("pip install reportlab")
    print("ReportLab installed. Run 'python make_test_pdf.py' again to build the PDF.")