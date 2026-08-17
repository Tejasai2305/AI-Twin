import hashlib
import re
import numpy as np


EMBEDDING_DIMENSION = 384


def _tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())


def _hash_token(token):
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little")


def create_embedding(text):
    """
    Lightweight deterministic 384-dimensional text embedding.

    Uses hashed word and character features instead of loading
    a SentenceTransformer model.
    """

    vector = np.zeros(EMBEDDING_DIMENSION, dtype=np.float32)

    tokens = _tokenize(text)

    # Word features
    for token in tokens:
        index = _hash_token(token) % EMBEDDING_DIMENSION
        vector[index] += 1.0

    # Character n-gram features
    normalized = " ".join(tokens)

    for i in range(len(normalized) - 2):
        ngram = normalized[i:i + 3]
        index = _hash_token(ngram) % EMBEDDING_DIMENSION
        vector[index] += 0.25

    # Normalize vector
    norm = np.linalg.norm(vector)

    if norm > 0:
        vector /= norm

    return vector