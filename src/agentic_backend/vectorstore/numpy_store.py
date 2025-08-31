"""
Vector Store simples usando NumPy - compatível com ARM/Windows.
Implementação leve e rápida para ambientes com limitações de arquitetura.
"""

import os
import json
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import pickle
from pathlib import Path


class NumPyVectorStore:
    """
    Vector Store baseado em NumPy para compatibilidade ARM.
    Usa busca por similaridade do cosseno sem dependências externas pesadas.
    """

    def __init__(self, dim: int, storage_dir: str = "./data/vectors"):
        """
        Inicializa o vector store.

        Args:
            dim: Dimensão dos vetores
            storage_dir: Diretório para armazenar os dados
        """
        self.dim = dim
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Arquivos de armazenamento
        self.vectors_file = self.storage_dir / "vectors.npy"
        self.metadata_file = self.storage_dir / "metadata.json"
        self.index_file = self.storage_dir / "index.pkl"

        # Dados em memória
        self.vectors: Optional[np.ndarray] = None
        self.metadata: List[Dict[str, Any]] = []
        self.texts: List[str] = []

        # Carregar dados existentes
        self._load_data()

    def _load_data(self):
        """Carrega dados do disco se existirem."""
        try:
            if self.vectors_file.exists():
                self.vectors = np.load(self.vectors_file)
                print(f"Carregados {len(self.vectors)} vetores do disco")

            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)

            if self.index_file.exists():
                with open(self.index_file, 'rb') as f:
                    data = pickle.load(f)
                    self.texts = data.get('texts', [])

        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            # Inicializar vazios em caso de erro
            self.vectors = None
            self.metadata = []
            self.texts = []

    def _save_data(self):
        """Salva dados no disco."""
        try:
            if self.vectors is not None and len(self.vectors) > 0:
                np.save(self.vectors_file, self.vectors)

            if self.metadata:
                with open(self.metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata, f, ensure_ascii=False, indent=2)

            if self.texts:
                with open(self.index_file, 'wb') as f:
                    pickle.dump({'texts': self.texts}, f)

        except Exception as e:
            print(f"Erro ao salvar dados: {e}")

    def add_vectors(self, vectors: np.ndarray, texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None):
        """
        Adiciona vetores ao store.

        Args:
            vectors: Array numpy de vetores (shape: n_samples, dim)
            texts: Lista de textos correspondentes
            metadata: Lista de metadados opcionais
        """
        if vectors.shape[1] != self.dim:
            raise ValueError(f"Dimensão dos vetores ({vectors.shape[1]}) não corresponde à dimensão esperada ({self.dim})")

        if len(vectors) != len(texts):
            raise ValueError("Número de vetores deve corresponder ao número de textos")

        # Normalizar vetores
        vectors_normalized = self._normalize_vectors(vectors)

        # Adicionar aos dados existentes
        if self.vectors is None:
            self.vectors = vectors_normalized
        else:
            self.vectors = np.vstack([self.vectors, vectors_normalized])

        self.texts.extend(texts)

        if metadata:
            if len(metadata) != len(texts):
                raise ValueError("Número de metadados deve corresponder ao número de textos")
            self.metadata.extend(metadata)
        else:
            # Adicionar metadados vazios
            self.metadata.extend([{}] * len(texts))

        # Salvar no disco
        self._save_data()

        print(f"Adicionados {len(vectors)} vetores. Total: {len(self.vectors)}")

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Busca os vetores mais similares ao vetor de consulta.

        Args:
            query_vector: Vetor de consulta (shape: dim,)
            top_k: Número de resultados a retornar

        Returns:
            Lista de tuplas (texto, score, metadados)
        """
        if self.vectors is None or len(self.vectors) == 0:
            return []

        if query_vector.shape[0] != self.dim:
            raise ValueError(f"Dimensão do vetor de consulta ({query_vector.shape[0]}) não corresponde à dimensão esperada ({self.dim})")

        # Normalizar vetor de consulta
        query_normalized = self._normalize_vectors(query_vector.reshape(1, -1))[0]

        # Calcular similaridade do cosseno
        similarities = np.dot(self.vectors, query_normalized)

        # Obter índices dos top_k mais similares
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if idx < len(self.texts):
                score = float(similarities[idx])
                text = self.texts[idx]
                meta = self.metadata[idx] if idx < len(self.metadata) else {}
                results.append((text, score, meta))

        return results

    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """
        Normaliza vetores para busca por similaridade do cosseno.

        Args:
            vectors: Array de vetores a normalizar

        Returns:
            Vetores normalizados
        """
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        # Evitar divisão por zero
        norms = np.where(norms == 0, 1, norms)
        return vectors / norms

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do vector store."""
        return {
            "total_vectors": len(self.vectors) if self.vectors is not None else 0,
            "dimension": self.dim,
            "storage_dir": str(self.storage_dir),
            "has_vectors_file": self.vectors_file.exists(),
            "has_metadata_file": self.metadata_file.exists(),
            "has_index_file": self.index_file.exists()
        }

    def clear(self):
        """Limpa todos os dados do vector store."""
        self.vectors = None
        self.metadata = []
        self.texts = []

        # Remover arquivos
        for file_path in [self.vectors_file, self.metadata_file, self.index_file]:
            if file_path.exists():
                file_path.unlink()

        print("Vector store limpo")

    def __len__(self) -> int:
        """Retorna o número de vetores no store."""
        return len(self.vectors) if self.vectors is not None else 0

    def __repr__(self) -> str:
        """Representação string do vector store."""
        stats = self.get_stats()
        return f"NumPyVectorStore(dim={stats['dimension']}, vectors={stats['total_vectors']})"


# Função utilitária para criar vector store com configurações padrão
def create_vector_store(dim: int = 768, storage_dir: str = "./data/vectors") -> NumPyVectorStore:
    """
    Cria um NumPyVectorStore com configurações padrão.

    Args:
        dim: Dimensão dos vetores (padrão: 768 para modelos como nomic-embed)
        storage_dir: Diretório de armazenamento

    Returns:
        Instância configurada do NumPyVectorStore
    """
    return NumPyVectorStore(dim=dim, storage_dir=storage_dir)
