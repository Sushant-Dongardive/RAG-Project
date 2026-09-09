import re


def clean_text(text):
    """
    Clean common PDF extraction formatting problems.
    """

    # Replace multiple spaces/tabs with a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Join words broken across a line with a hyphen
    # Example: non-
    # linear -> non-linear
    text = re.sub(r"-\s*\n\s*", "-", text)

    # Replace normal line breaks with spaces
    text = re.sub(r"\s*\n\s*", " ", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


if __name__ == "__main__":

    sample_text = """
    Fingerprint verification is
    performed
    manually
    by professional
    fingerprint experts.
    """

    cleaned = clean_text(sample_text)

    print("Before:")
    print(sample_text)

    print("\nAfter:")
    print(cleaned)
    