from __future__ import annotations
from typing import Dict, Any, List
from ...tools.mcp_client import MCPClient
from ...security.policies import Policy
from ...audit.evidence import EvidencePack
from ...llm.engine import LLMEngine
from ...embeddings.embedding import ONNXEmbedder
from ...vectorstore.faiss_store import LocalFaiss
import asyncio
import logging

log = logging.getLogger(__name__)

async def run(state: Dict[str, Any], llm_engine: LLMEngine, embedder: ONNXEmbedder, vector_store: LocalFaiss = None) -> Dict[str, Any]:
    """
    Researcher que usa IA real para pesquisa inteligente com RAG.

    Args:
        state: Estado atual da conversa
        llm_engine: Engine de LLM para geração de respostas
        embedder: Embedder para gerar embeddings
        vector_store: Vector store para busca por similaridade (opcional)

    Returns:
        Estado atualizado com resposta do researcher
    """
    query = state.get("query", "")
    plan = [f"Pesquisar fontes para: {query}", "Usar RAG para encontrar contexto", "Gerar resposta com LLM"]
    state["plan"] = plan

    print(f"🔍 RESEARCHER: Recebendo query: '{query}'")

    try:
        # PASSO 1: Usar RAG para encontrar contexto relevante
        print("📚 PASSO 1: Buscando contexto no RAG...")

        rag_context = ""
        if embedder and vector_store:
            # Gerar embedding da query
            query_embedding = embedder.embed([query])[0]
            print(f"🔧 Embedding gerado: shape={query_embedding.shape}")

            # Buscar documentos similares
            search_results = vector_store.search(query_embedding.reshape(1, -1), k=5)
            print(f"🔍 Busca FAISS encontrou {len(search_results)} resultados")

            # Construir contexto dos documentos encontrados
            relevant_docs = []
            for doc_text, score in search_results:
                if score > 0.3:  # Threshold de similaridade
                    relevant_docs.append(doc_text)
                    print(f"📄 Documento relevante (score: {score:.3f}): {doc_text[:100]}...")

            if relevant_docs:
                rag_context = "\n".join(relevant_docs)
                print(f"✅ Contexto RAG construído: {len(rag_context)} caracteres")
            else:
                print("⚠️ Nenhum documento relevante encontrado no RAG")
        else:
            print("⚠️ RAG não disponível (embedder ou vector_store não fornecidos)")

        # PASSO 2: Usar LLM para gerar resposta baseada no contexto
        print("🤖 PASSO 2: Gerando resposta com LLM...")

        if rag_context:
            # Tem contexto do RAG - usar para resposta informada
            research_prompt = f"""
Você é um pesquisador especialista em Itaú e bancos brasileiros.
Baseando-se nestas informações encontradas:

{rag_context}

Responda à pergunta: {query}

Forneça uma resposta precisa, útil e baseada nas informações fornecidas.
Se as informações não forem suficientes, diga claramente.
"""
        else:
            # Sem contexto - resposta baseada em conhecimento geral
            research_prompt = f"""
Você é um pesquisador especialista em Itaú e bancos brasileiros.

Pergunta: {query}

Forneça uma resposta baseada em seu conhecimento sobre o Itaú.
Seja preciso e útil.
"""

        print(f"📝 Prompt para LLM: {research_prompt[:200]}...")

        # Gerar resposta usando LLM
        final_response = await asyncio.to_thread(
            llm_engine.generate_text,
            research_prompt,
            max_length=300,
            system_prompt="Você é um assistente especializado em informações sobre Itaú e serviços bancários."
        )

        print(f"✅ Resposta gerada: {final_response[:200]}...")

        # PASSO 3: Atualizar estado
        state["response"] = final_response
        state["researcher_response"] = final_response
        state["rag_context_used"] = rag_context
        state["research_completed"] = True

        print("🎉 RESEARCHER: Pesquisa concluída com sucesso!")

    except Exception as e:
        log.error(f"❌ Erro no researcher: {e}")
        print(f"❌ ERRO no researcher: {e}")

        # Fallback se algo falhar
        state["response"] = f"Desculpe, não foi possível completar a pesquisa sobre: {query}"
        state["researcher_response"] = f"Erro na pesquisa: {str(e)}"
        state["research_completed"] = False

    return state
