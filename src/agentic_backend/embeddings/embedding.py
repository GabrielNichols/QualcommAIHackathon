"""
Wrapper para embeddings nomic-embed-text.onnx (on-device com NPU).
Compatível com Snapdragon X Plus/X Elite.
"""
from __future__ import annotations
import onnxruntime as ort
import numpy as np
from typing import List, Optional
import os
import logging

log = logging.getLogger(__name__)

class ONNXEmbedder:
    """
    Embedder usando modelo ONNX otimizado para NPU.
    Suporta nomic-embed-text-v1.5 e outros modelos de embedding.
    """

    def __init__(self, model_path: str, providers: Optional[List[str]] = None):
        """
        Inicializa o embedder ONNX.

        Args:
            model_path: Caminho para o modelo ONNX
            providers: Lista de execution providers (padrão: tenta NPU primeiro)
        """
        if providers is None:
            # Tentar QNN primeiro, depois CPU
            providers = ["QNNExecutionProvider", "CPUExecutionProvider"]

        self.model_path = model_path
        self.providers = providers
        self.session = None
        self.input_name = None
        self.output_name = None

        self._init_session()

    def _init_session(self):
        """Inicializa a sessão ONNX Runtime."""
        try:
            log.info(f"Inicializando ONNX Embedder: {self.model_path}")
            log.info(f"Providers tentados: {self.providers}")

            # Verificar se arquivo existe
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Modelo ONNX não encontrado: {self.model_path}")

            # Criar sessão
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            self.session = ort.InferenceSession(
                self.model_path,
                providers=self.providers,
                sess_options=sess_options
            )

            # Obter nomes de input/output
            inputs = self.session.get_inputs()
            outputs = self.session.get_outputs()

            if not inputs:
                raise ValueError("Modelo não tem inputs definidos")

            self.input_name = inputs[0].name
            self.output_name = outputs[0].name if outputs else None

            log.info("✅ ONNX Embedder inicializado com sucesso")
            log.info(f"   Input: {self.input_name}")
            log.info(f"   Output: {self.output_name}")
            log.info(f"   Provider usado: {self.session.get_providers()[0]}")

        except Exception as e:
            log.error(f"❌ Falha ao inicializar ONNX Embedder: {e}")
            raise

    def embed(self, texts: List[str]) -> np.ndarray:
        """
        Gera embeddings para uma lista de textos.

        Args:
            texts: Lista de textos para embedding

        Returns:
            Array numpy com embeddings (shape: n_texts, embedding_dim)
        """
        if not self.session:
            raise RuntimeError("Sessão ONNX não inicializada")

        try:
            # Preparar input
            inputs = {}

            # Verificar se o modelo precisa de inputs adicionais (BERT-like)
            input_names = [inp.name for inp in self.session.get_inputs()]

            if "input_ids" in input_names:
                # Modelo BERT-like - precisa de tokenização
                # Por enquanto, vamos criar inputs dummy para testar
                batch_size = len(texts)
                seq_length = 128  # Tamanho máximo da sequência

                # Input IDs (dummy)
                inputs["input_ids"] = np.random.randint(0, 30000, (batch_size, seq_length), dtype=np.int64)

                # Attention mask
                if "attention_mask" in input_names:
                    inputs["attention_mask"] = np.ones((batch_size, seq_length), dtype=np.int64)

                # Token type IDs
                if "token_type_ids" in input_names:
                    inputs["token_type_ids"] = np.zeros((batch_size, seq_length), dtype=np.int64)

            else:
                # Modelo simples - strings diretamente
                inputs[self.input_name] = np.array(texts, dtype=object)

            # Executar inferência
            outputs = self.session.run([self.output_name], inputs)

            # Processar output
            embeddings = outputs[0]

            # Garantir que seja float32
            embeddings = embeddings.astype(np.float32)

            # Se o shape for (batch, seq_len, embed_dim), extrair apenas o primeiro token (CLS)
            if len(embeddings.shape) == 3 and embeddings.shape[1] > 1:
                embeddings = embeddings[:, 0, :]  # Primeiro token de cada sequência

            # Normalizar se necessário (alguns modelos já fazem isso)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.where(norms == 0, 1, norms)

            log.debug(f"Embeddings gerados: shape={embeddings.shape}")

            return embeddings

        except Exception as e:
            log.error(f"Erro na geração de embeddings: {e}")
            raise

    def embed_single(self, text: str) -> np.ndarray:
        """
        Gera embedding para um único texto.

        Args:
            text: Texto para embedding

        Returns:
            Array numpy com embedding (shape: embedding_dim,)
        """
        embeddings = self.embed([text])
        return embeddings[0]

    def get_embedding_dim(self) -> int:
        """Retorna a dimensão dos embeddings."""
        if not self.session:
            raise RuntimeError("Sessão não inicializada")

        output_info = self.session.get_outputs()[0]
        shape = output_info.shape

        if len(shape) == 2 and shape[0] == -1:
            # Shape típico: [-1, embedding_dim]
            return shape[1]
        elif len(shape) == 1:
            return shape[0]
        else:
            raise ValueError(f"Shape de output inesperado: {shape}")

    def is_available(self) -> bool:
        """Verifica se o embedder está disponível."""
        return self.session is not None

    def get_model_info(self) -> dict:
        """Retorna informações sobre o modelo."""
        if not self.session:
            return {"status": "not_loaded"}

        try:
            return {
                "status": "loaded",
                "model_path": self.model_path,
                "providers": self.session.get_providers(),
                "input_name": self.input_name,
                "output_name": self.output_name,
                "embedding_dim": self.get_embedding_dim()
            }
        except Exception as e:
            return {
                "status": "loaded",
                "model_path": self.model_path,
                "error": str(e)
            }
