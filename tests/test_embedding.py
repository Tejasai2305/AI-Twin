from backend.embeddings.embedding_service import create_embedding
import numpy as np

sentence1 = "FastAPI is a modern Python framework."
sentence2 = "Which web framework are we using?"
sentence3 = "I like playing football."

embedding1 = create_embedding(sentence1)
embedding2 = create_embedding(sentence2)
embedding3 = create_embedding(sentence3)


def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (
        np.linalg.norm(vec1) * np.linalg.norm(vec2)
    )


print("Similarity (1,2):", cosine_similarity(embedding1, embedding2))
print("Similarity (1,3):", cosine_similarity(embedding1, embedding3))