import faiss
import numpy as np


def create_vector_store(embeddings):
    """
    Create a FAISS index from embedding vectors.
    """

    # Convert embeddings to NumPy float32
    vectors = np.array(embeddings).astype("float32")

    # Get vector dimension
    dimension = vectors.shape[1]

    # Create FAISS index
    index = faiss.IndexFlatL2(dimension)

    # Add vectors to the index
    index.add(vectors)

    return index


def search_vector_store(index, query_embedding, top_k=5):
    """
    Search the vector store for the most similar vectors.
    """

    query_vector = np.array([query_embedding]).astype("float32")

    distances, indices = index.search(query_vector, top_k)

    return distances[0], indices[0]