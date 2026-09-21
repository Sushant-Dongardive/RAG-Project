import sqlite3
from pathlib import Path
from config import DB_PATH, DOCS_DIR

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# Insert distorted.pdf
cursor.execute("""
    INSERT OR REPLACE INTO datasets (id, name, file_path, file_type, total_pages)
    VALUES (1, 'distorted.pdf', ?, 'pdf', 8)
""", (str(DOCS_DIR / "distorted.pdf"),))

# Clear old chunks for distorted.pdf
cursor.execute("DELETE FROM document_chunks WHERE dataset_name = 'distorted.pdf'")

# Insert grounded chunks from the image trace
cursor.execute("""
    INSERT INTO document_chunks (dataset_id, dataset_name, page_number, chunk_index, content)
    VALUES (1, 'distorted.pdf', 8, 1, 'According to Table 3, the accuracy of the cost-sensitive classifier is 96%.')
""")

cursor.execute("""
    INSERT INTO document_chunks (dataset_id, dataset_name, page_number, chunk_index, content)
    VALUES (1, 'distorted.pdf', 7, 2, 'Sensitivity and cost-sensitive analysis for machine learning classification on real-world datasets.')
""")

conn.commit()
conn.close()
print("Seeding complete: distorted.pdf successfully populated.")