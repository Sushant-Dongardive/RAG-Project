import pymupdf


def extract_text_from_pdf(file_path: str):
    document = pymupdf.open(file_path)

    pages = []

    for page_number, page in enumerate(document):
        text = page.get_text()

        pages.append({
            "page": page_number + 1,
            "text": text
        })

    document.close()

    return pages


if __name__ == "__main__":
    file_path = "data/documents/distorted.pdf"

    pages = extract_text_from_pdf(file_path)

    print(f"Total pages: {len(pages)}")

    for page in pages:
        print(f"\n--- Page {page['page']} ---")
        print(page["text"][:500])