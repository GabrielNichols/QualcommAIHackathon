"""
Agente Chatbot com RAG e busca na internet usando Crawl4AI.
Especializado em conversação inteligente com capacidades de pesquisa web.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
import asyncio
import json
from datetime import datetime

from ...llm.engine import LLMEngine
from ...embeddings.embedding import ONNXEmbedder
from ...vectorstore.faiss_store import LocalFaiss
from ...npu_monitor import npu_monitor, monitor_inference
from ...security.policies import Policy
from ...audit.evidence import EvidencePack
from ...tools.web_scraper import ARMCompatibleWebScraper

import logging
logger = logging.getLogger(__name__)


class ChatbotAgent:
    """Agente de chatbot com RAG e busca na internet"""

    def __init__(self, llm_engine: LLMEngine, embedding_service: ONNXEmbedder,
                 vector_store: LocalFaiss):
        self.llm = llm_engine
        self.embeddings = embedding_service
        self.vector_store = vector_store
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history_length = 10

    async def chat(self, message: str, user_context: Optional[Dict[str, Any]] = None,
                   enable_web_search: bool = True, first_access: bool = False) -> Dict[str, Any]:
        """
        Processa uma mensagem de chat com RAG e busca na internet opcional

        Args:
            message: Mensagem do usuário
            user_context: Contexto do usuário do RAG
            enable_web_search: Se deve usar busca na internet
            first_access: Se é o primeiro acesso do usuário

        Returns:
            Resposta com métricas de performance
        """
        start_time = asyncio.get_event_loop().time()

        # Verificar se é primeiro acesso
        if first_access or self._is_first_access_message(message):
            logger.info("🎯 Primeiro acesso detectado no chatbot")
            return {
                "response": "Olá! Bem-vindo ao sistema Itaú. Vou iniciar seu processo de onboarding para personalizar sua experiência.",
                "first_access_detected": True,
                "processing_time_seconds": 0.01,
                "npu_metrics": {
                    "utilization_percent": npu_monitor.get_current_metrics().utilization_percent,
                    "memory_used_mb": npu_monitor.get_current_metrics().memory_used_mb,
                    "temperature_celsius": npu_monitor.get_current_metrics().temperature_celsius,
                    "power_consumption_watts": npu_monitor.get_current_metrics().power_consumption_watts,
                    "inference_time_ms": npu_monitor.get_current_metrics().inference_time_ms,
                    "timestamp": npu_monitor.get_current_metrics().timestamp,
                    "performance_score": 75.0  # Valor padrão para compatibilidade
                },
                "rag_context_used": False,
                "web_search_performed": False
            }

        # Monitora uso da NPU durante a inferência
        with monitor_inference():
            try:
                # 1. Busca contexto relevante no RAG (incluindo contexto do usuário)
                rag_context = await self._get_rag_context(message, user_context)

                # 2. Personalizar resposta com contexto do usuário se disponível
                personalized_context = ""
                if user_context:
                    personalized_context = self._build_personalized_context(user_context)

                # 3. Decide se precisa de busca na internet
                needs_web_search = await self._should_search_web(message, rag_context)

                web_results = []
                if enable_web_search and needs_web_search and CRAWL4AI_AVAILABLE:
                    web_results = await self._search_web(message)

                # 3. Gera resposta usando LLM
                response = await self._generate_response(message, rag_context, web_results)

                # 4. Atualiza histórico de conversa
                self._update_conversation_history(message, response)

                # 5. Coleta métricas de performance
                end_time = asyncio.get_event_loop().time()
                processing_time = end_time - start_time

                npu_report = npu_monitor.get_performance_report()

                return {
                    "response": response,
                    "rag_context_used": bool(rag_context),
                    "web_search_performed": bool(web_results),
                    "processing_time_seconds": processing_time,
                    "npu_metrics": {
                        "performance_score": npu_report.get("performance_score", 50.0),
                        "average_metrics_1min": {
                            "avg_utilization_percent": getattr(npu_report.get("average_metrics_1min", {}).get("avg_utilization_percent", None), 'utilization_percent', 0.0) if npu_report.get("average_metrics_1min") else 0.0,
                            "avg_memory_used_mb": getattr(npu_report.get("average_metrics_1min", {}).get("avg_memory_used_mb", None), 'memory_used_mb', 0.0) if npu_report.get("average_metrics_1min") else 0.0,
                        },
                        "optimization_suggestions": npu_report.get("optimization_suggestions", [])
                    },
                    "conversation_length": len(self.conversation_history),
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                logger.error(f"Chatbot error: {e}")
                return {
                    "response": "Desculpe, ocorreu um erro no processamento. Tente novamente.",
                    "error": str(e),
                    "processing_time_seconds": asyncio.get_event_loop().time() - start_time,
                    "npu_metrics": {
                        "performance_score": 0.0,
                        "average_metrics_1min": {
                            "avg_utilization_percent": 0.0,
                            "avg_memory_used_mb": 0.0,
                        },
                        "optimization_suggestions": ["Erro no processamento"]
                    }
                }

    async def _get_rag_context(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Busca contexto relevante no RAG"""
        try:
            # Gera embedding da mensagem (método síncrono)
            message_embedding = self.embeddings.embed([message])[0]

            # Busca documentos similares no vector store (método síncrono)
            search_results = self.vector_store.search(message_embedding.reshape(1, -1), k=5)

            context_docs = []
            if search_results:
                for text, score in search_results:
                    if score > 0.3:  # Threshold de similaridade reduzido
                        context_docs.append(text)

            # Adiciona contexto do usuário se disponível
            if user_context:
                user_info = []
                if user_context.get("name"):
                    user_info.append(f"Nome: {user_context['name']}")
                if user_context.get("role"):
                    user_info.append(f"Cargo: {user_context['role']}")
                if user_context.get("preferences"):
                    user_info.append(f"Preferências: {user_context['preferences']}")

                if user_info:
                    context_docs.insert(0, "INFORMAÇÕES DO USUÁRIO: " + " | ".join(user_info))

            return context_docs

        except Exception as e:
            logger.error(f"RAG context error: {e}")
            return []

    async def _should_search_web(self, message: str, rag_context: List[str]) -> bool:
        """Decide se deve fazer busca na internet baseado na mensagem e contexto RAG"""

        # Palavras-chave que indicam necessidade de informação atualizada
        update_keywords = [
            "atual", "hoje", "agora", "recente", "último", "novo", "mudança",
            "alteração", "atualização", "modificação", "notícia", "evento"
        ]

        message_lower = message.lower()

        # Verifica se a mensagem contém palavras-chave de atualização
        needs_update = any(keyword in message_lower for keyword in update_keywords)

        # Verifica se temos contexto suficiente no RAG
        has_sufficient_context = len(rag_context) > 2 and any(len(ctx) > 100 for ctx in rag_context)

        # Decide baseado na análise
        if needs_update and not has_sufficient_context:
            return True

        # Para perguntas sobre produtos/serviços Itaú, geralmente não precisa de busca externa
        itau_keywords = ["itau", "conta", "cartão", "crédito", "investimento", "seguro"]
        if any(keyword in message_lower for keyword in itau_keywords):
            return False

        # Para perguntas gerais sobre mercado financeiro, pode precisar
        finance_keywords = ["mercado", "ação", "bolsa", "câmbio", "dólar", "inflação", "taxa"]
        if any(keyword in message_lower for keyword in finance_keywords):
            return True

        return False

    async def _search_web(self, query: str) -> List[Dict[str, Any]]:
        """Realiza busca na internet usando ARMCompatibleWebScraper"""
        try:
            # Verifica se o domínio é permitido pela política de segurança
            if not Policy.is_domain_allowed("google.com"):
                logger.warning("Google search not allowed by security policy")
                return []

            # Usa web scraper compatível com ARM
            with ARMCompatibleWebScraper() as scraper:
                search_results = scraper.search_web(query, max_results=3)

                # Converte para o formato esperado
                results = []
                for result in search_results:
                    results.append({
                        "source": "google_search",
                        "url": result.get("url", ""),
                        "content": result.get("title", "") + " " + result.get("snippet", ""),
                        "timestamp": datetime.now().isoformat()
                    })

                return results

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []

    async def _generate_response(self, message: str, rag_context: List[str],
                                web_results: List[Dict[str, Any]]) -> str:
        """Gera resposta usando LLM com contexto RAG e web"""

        # Prepara prompt com contexto
        system_prompt = """Você é um assistente inteligente especializado em operações bancárias e corporativas do Itaú.
        Use o contexto fornecido para dar respostas precisas, personalizadas e úteis.

        INSTRUÇÕES:
        - Seja sempre educado e profissional
        - Use o contexto do usuário para personalizar respostas quando relevante
        - Cite fontes quando usar informações externas
        - Mantenha privacidade e conformidade com LGPD
        - Se não souber algo, admita honestamente
        """

        # Adiciona contexto RAG
        context_text = ""
        if rag_context:
            context_text = "\n\nCONTEXTO RELEVANTE:\n" + "\n".join(f"- {ctx}" for ctx in rag_context[:3])

        # Adiciona resultados da web
        if web_results:
            context_text += "\n\nINFORMAÇÕES DA WEB:\n"
            for result in web_results:
                context_text += f"- Fonte: {result['source']}\n  {result['content'][:500]}...\n"

        # Adiciona histórico da conversa
        history_text = ""
        if self.conversation_history:
            history_text = "\n\nHISTÓRICO DA CONVERSA:\n"
            for i, msg in enumerate(self.conversation_history[-4:]):  # Últimas 4 mensagens
                role = "Usuário" if i % 2 == 0 else "Assistente"
                history_text += f"{role}: {msg['content']}\n"

        # Monta prompt completo
        full_prompt = f"{system_prompt}{context_text}{history_text}\n\nUsuário: {message}\n\nAssistente:"

        # Gera resposta usando LLM (assíncrono)
        response = await asyncio.to_thread(
            self.llm.generate_text,
            prompt=full_prompt,
            max_length=300,  # Aumentado para acomodar prompts maiores
            temperature=0.7
        )

        return response.strip()

    def _update_conversation_history(self, user_message: str, assistant_response: str):
        """Atualiza histórico de conversa"""
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": assistant_response})

        # Mantém apenas as últimas mensagens
        if len(self.conversation_history) > self.max_history_length * 2:
            self.conversation_history = self.conversation_history[-self.max_history_length * 2:]

    def clear_conversation_history(self):
        """Limpa histórico de conversa"""
        self.conversation_history.clear()

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Retorna resumo da conversa atual"""
        return {
            "total_messages": len(self.conversation_history),
            "conversation_pairs": len(self.conversation_history) // 2,
            "last_interaction": self.conversation_history[-1] if self.conversation_history else None,
            "topics_discussed": self._extract_topics()
        }

    def _extract_topics(self) -> List[str]:
        """Extrai tópicos discutidos da conversa"""
        if not self.conversation_history:
            return []

        all_text = " ".join([msg["content"] for msg in self.conversation_history])
        all_text_lower = all_text.lower()

        topics = []
        topic_keywords = {
            "Conta Corrente": ["conta", "corrente", "saldo", "transferência"],
            "Cartão de Crédito": ["cartão", "crédito", "limite", "fatura"],
            "Investimentos": ["investimento", "ação", "tesouro", "poupança"],
            "Empréstimos": ["empréstimo", "financiamento", "crédito pessoal"],
            "Seguros": ["seguro", "proteção", "vida", "automóvel"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in all_text_lower for keyword in keywords):
                topics.append(topic)

        return topics

    def _is_first_access_message(self, message: str) -> bool:
        """Detecta se a mensagem indica primeiro acesso"""
        first_access_keywords = [
            "primeiro acesso", "primeira vez", "novo usuário", "nova conta",
            "começar", "iniciar", "bem vindo", "olá", "oi",
            "não tenho conta", "sou novo", "nova aqui", "novo aqui",
            "primeira vez que entro", "primeira vez que uso"
        ]

        message_lower = message.lower().strip()
        return any(keyword in message_lower for keyword in first_access_keywords)

    def _build_personalized_context(self, user_context: Dict[str, Any]) -> str:
        """Constrói contexto personalizado baseado no perfil do usuário"""
        if not user_context:
            return ""

        context_parts = []

        # Informações pessoais
        if "personal_info" in user_context:
            personal = user_context["personal_info"]
            context_parts.append(f"Nome: {personal.get('nome', 'N/A')}")
            context_parts.append(f"Localização: {personal.get('localizacao', 'N/A')}")
            context_parts.append(f"Experiência bancária: {personal.get('experiencia_bancaria', 'N/A')}")

        # Informações profissionais
        if "professional_info" in user_context:
            prof = user_context["professional_info"]
            context_parts.append(f"Cargo: {prof.get('cargo', 'N/A')}")
            context_parts.append(f"Área: {prof.get('area', 'N/A')}")
            context_parts.append(f"Experiência: {prof.get('experiencia_anos', 'N/A')} anos")

        # Preferências
        if "preferences" in user_context:
            prefs = user_context["preferences"]
            context_parts.append(f"Sites frequentes: {prefs.get('sites_frequentes', 'N/A')}")
            context_parts.append(f"Ferramentas favoritas: {prefs.get('ferramentas_favoritas', 'N/A')}")

        # Resumo executivo se disponível
        if "context_summary" in user_context:
            context_parts.append(f"Resumo: {user_context['context_summary']}")

        return " | ".join(context_parts)


# Função para integração com LangGraph
async def run_chatbot(state: Dict[str, Any], llm_engine: LLMEngine,
                     embedding_service: ONNXEmbedder, vector_store: LocalFaiss,
                     ev: EvidencePack) -> Dict[str, Any]:
    """
    Função de execução do chatbot para integração com LangGraph
    """
    message = state.get("query", "")
    user_context = state.get("user_context", {})

    # Inicializa agente se não existir
    if not hasattr(run_chatbot, 'agent'):
        run_chatbot.agent = ChatbotAgent(llm_engine, embedding_service, vector_store)

    # Inicia monitoramento NPU
    npu_monitor.start_monitoring()

    try:
        result = await run_chatbot.agent.chat(message, user_context)

        # Log da interação
        ev.log_step("chatbot_interaction", {
            "message": message,
            "response": result["response"],
            "processing_time": result["processing_time_seconds"],
            "npu_metrics": result["npu_metrics"]
        })

        # Atualiza estado
        state["chatbot_response"] = result["response"]
        state["performance_metrics"] = {
            "processing_time_seconds": result["processing_time_seconds"],
            "npu_performance_score": result["npu_metrics"].get("performance_score", 50.0)
        }

        return state

    finally:
        # Para monitoramento (opcional, pode continuar rodando)
        pass
