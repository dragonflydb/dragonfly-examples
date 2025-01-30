from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L3-v2")

def generate_embedding(text):
    return model.encode(text, convert_to_numpy=True).astype(np.float32)
