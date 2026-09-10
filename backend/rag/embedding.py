from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def generate_embeddings(texts):
    """
    Convert a list of text chunks into numerical vectors.
    """

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    )

    return embeddings


if __name__ == "__main__":

    test_texts = [
        "Fingerprint verification is a biometric identification method.",
        "Fingerprint matching is affected by nonlinear distortion."
    ]

    embeddings = generate_embeddings(test_texts)

    print("\nNumber of vectors:", len(embeddings))
    print("Vector dimensions:", len(embeddings[0]))
    print("First vector:")
    print(embeddings[0])