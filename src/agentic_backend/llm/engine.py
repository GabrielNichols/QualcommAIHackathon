"""
LLM Engine baseado no model-qa.py - implementação direta e funcional.
"""
from __future__ import annotations
from typing import Optional, Dict, Any
import logging
import time

log = logging.getLogger(__name__)

try:
    import onnxruntime_genai as og
    _HAS_GENAI = True
except Exception:
    _HAS_GENAI = False
    og = None

class LLMEngine:
    def __init__(self, model_path: str, execution_provider: str = "follow_config"):
        self.model_path = model_path
        self.execution_provider = execution_provider
        self._model = None
        self._tokenizer = None
        self._tokenizer_stream = None
        self._init_backend()

    def _init_backend(self):
        """Inicialização baseada exatamente no model-qa.py"""
        if not _HAS_GENAI:
            log.warning("onnxruntime-genai não disponível. Instale com: pip install onnxruntime-genai")
            return

        try:
            log.info(f"Inicializando onnxruntime-genai com {self.model_path}")

            # Seguir exatamente o model-qa.py
            config = og.Config(self.model_path)
            if self.execution_provider != "follow_config":
                config.clear_providers()
                if self.execution_provider != "cpu":
                    log.info(f"Setting model to {self.execution_provider}")
                    config.append_provider(self.execution_provider)

            self._model = og.Model(config)
            log.info("✅ Modelo carregado")

            self._tokenizer = og.Tokenizer(self._model)
            self._tokenizer_stream = self._tokenizer.create_stream()
            log.info("✅ Tokenizer criado")

        except Exception as e:
            log.error(f"Falha ao iniciar LLM: {e}")
            self._model = None

    def generate_text(self, prompt: str, **gen_kwargs) -> str:
        """
        Geração de texto baseada exatamente no model-qa.py
        """
        if not self._model:
            raise RuntimeError("Modelo LLM não inicializado")

        try:
            # Configurar parâmetros como no model-qa.py
            search_options = {
                'do_sample': gen_kwargs.get('do_sample', True),
                'max_length': gen_kwargs.get('max_length', 512),
                'min_length': gen_kwargs.get('min_length', 0),
                'top_p': gen_kwargs.get('top_p', 0.9),
                'top_k': gen_kwargs.get('top_k', 50),
                'temperature': gen_kwargs.get('temperature', 0.3),
                'repetition_penalty': gen_kwargs.get('repetition_penalty', 1.0),
                'batch_size': 1
            }

            params = og.GeneratorParams(self._model)
            params.set_search_options(**search_options)

            # Sem guidance por padrão (simplificar)
            generator = og.Generator(self._model, params)

            # Usar template direto que funcionou no teste
            system_prompt = gen_kwargs.get('system_prompt', 'You are a helpful AI assistant.')

            # Escapar quebras de linha no JSON para evitar erro de parsing
            escaped_system = system_prompt.replace('\n', '\\n').replace('\r', '\\r').replace('"', '\\"')
            escaped_prompt = prompt.replace('\n', '\\n').replace('\r', '\\r').replace('"', '\\"')

            messages = f"""[{{"role": "system", "content": "{escaped_system}"}}, {{"role": "user", "content": "{escaped_prompt}"}}]"""

            if self._model.type == "marian-ssru":
                input_text = prompt
            else:
                # Usar diretamente o template que funcionou no teste direto
                input_text = self._tokenizer.apply_chat_template(messages=messages, add_generation_prompt=True)
                log.info(f"Template aplicado: {repr(input_text[:100])}...")

            input_tokens = self._tokenizer.encode(input_text)

            # Ajustar max_length para levar em conta o tamanho do prompt
            # Garantir que haja pelo menos espaço para 100 tokens de resposta
            input_length = len(input_tokens)
            adjusted_max_length = max(gen_kwargs.get('max_length', 512), input_length + 100)

            # Atualizar os parâmetros de busca com o max_length ajustado
            search_options['max_length'] = adjusted_max_length
            params.set_search_options(**search_options)

            generator.append_tokens(input_tokens)

            # Gerar resposta exatamente como no model-qa.py
            response = ""
            while not generator.is_done():
                generator.generate_next_token()
                new_token = generator.get_next_tokens()[0]
                token_text = self._tokenizer_stream.decode(new_token)
                response += token_text

            # Limpar recursos
            del generator

            return response.strip()

        except Exception as e:
            log.error(f"Erro na geração de texto: {e}")
            raise

    def generate(self, prompt: str, **gen_kwargs) -> str:
        """Método de compatibilidade"""
        return self.generate_text(prompt, **gen_kwargs)

    def is_available(self) -> bool:
        """Verifica se o modelo está disponível"""
        return self._model is not None

    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo"""
        if not self._model:
            return {"status": "not_loaded"}

        return {
            "status": "loaded",
            "model_path": self.model_path,
            "execution_provider": self.execution_provider,
            "type": getattr(self._model, 'type', 'unknown'),
            "vocab_size": getattr(self._tokenizer, 'vocab_size', 'unknown') if self._tokenizer else 'unknown'
        }
