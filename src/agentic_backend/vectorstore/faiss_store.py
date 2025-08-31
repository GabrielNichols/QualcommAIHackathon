from __future__ import annotations
import faiss, os
import numpy as np
from typing import List, Tuple

class LocalFaiss:
    def __init__(self, dim: int, index_dir: str):
        self.dim = dim
        self.index_dir = index_dir
        os.makedirs(index_dir, exist_ok=True)
        self.index_path = os.path.join(index_dir, f"faiss_{dim}.index")
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            self.index = faiss.IndexFlatIP(dim)
        self.docs: List[str] = []

    def add(self, vectors: np.ndarray, texts: List[str]):
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.docs.extend(texts)
        faiss.write_index(self.index, self.index_path)

    def search(self, query_vec: np.ndarray, k: int = 5) -> List[Tuple[str, float]]:
        faiss.normalize_L2(query_vec)
        D, I = self.index.search(query_vec, k)
        results = []
        for i, d in zip(I[0], D[0]):
            if 0 <= i < len(self.docs):
                results.append((self.docs[i], float(d)))
        return results
