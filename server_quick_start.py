#!/usr/bin/env python3
"""
Servidor Quick Start para testar LLM local
Servidor simples e direto para validação da resposta da LLM
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agentic_backend.llm.engine import LLMEngine

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Componentes globais
_llm_engine = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    processing_time_seconds: float
    timestamp: str

async def load_llm():
    """Carrega apenas o LLM Engine"""
    global _llm_engine

    if _llm_engine is not None:
        return _llm_engine

    try:
        logger.info("🔧 CARREGANDO LLM ENGINE...")

        # Caminho do modelo
        model_path = "./models/llama-3.2-3b-qnn"

        if not os.path.exists(model_path):
            logger.error(f"❌ Caminho do modelo não encontrado: {model_path}")
            return None

        logger.info(f"📁 Carregando modelo de: {model_path}")

        # Inicializa LLM Engine
        _llm_engine = LLMEngine(model_path)
        logger.info("✅ LLM Engine carregado com sucesso!")

        return _llm_engine

    except Exception as e:
        logger.error(f"❌ Erro ao carregar LLM: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

# Cria aplicação FastAPI
app = FastAPI(
    title="Agentic Browser Backend - Quick Start",
    description="Servidor simplificado para teste da LLM local",
    version="1.0.0"
)

# Configura CORS para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Carrega componentes na inicialização"""
    logger.info("🚀 INICIANDO SERVIDOR QUICK START...")
    logger.info("Endpoints disponíveis:")
    logger.info("  GET  /health - Health check")
    logger.info("  POST /chat - Teste da LLM local")
    logger.info("  GET  /status - Status dos componentes")
    logger.info("")
    logger.info("Acesse: http://localhost:8080/docs para ver a documentação")

    await load_llm()

@app.get("/health")
async def health_check():
    """Health check básico"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "quick-start-llm-test"
    }

@app.get("/status")
async def get_status():
    """Status dos componentes"""
    global _llm_engine

    llm_status = "loaded" if _llm_engine is not None else "not_loaded"

    return {
        "llm_engine": llm_status,
        "model_path": "./models/llama-3.2-3b-qnn",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Endpoint de chat para teste da LLM local"""
    global _llm_engine

    start_time = asyncio.get_event_loop().time()

    # Verifica se LLM está carregado
    if _llm_engine is None:
        return ChatResponse(
            response="🤖 LLM Engine ainda não foi carregado. Aguarde alguns segundos e tente novamente.",
            conversation_id=request.conversation_id or "temp",
            processing_time_seconds=0.1,
            timestamp=datetime.now().isoformat()
        )

    try:
        logger.info(f"💬 Processando mensagem: {request.message[:50]}...")

        # Prompt simples para teste
        prompt = f"""Você é um assistente útil e amigável.

Usuário: {request.message}

Responda de forma direta e útil:"""

        logger.info(f"🤖 Enviando prompt para LLM (tamanho: {len(prompt)} caracteres)")

        # Gera resposta usando LLM
        response = await asyncio.to_thread(
            _llm_engine.generate_text,
            prompt=prompt,
            max_length=512,
            temperature=0.7
        )

        processing_time = asyncio.get_event_loop().time() - start_time

        # Limpa resposta
        clean_response = response.strip()

        logger.info(f"✅ Resposta gerada em {processing_time:.2f}s")
        logger.info(f"📝 Resposta: {clean_response[:100]}...")

        return ChatResponse(
            response=clean_response,
            conversation_id=request.conversation_id or f"chat_{hash(request.message)}",
            processing_time_seconds=processing_time,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"❌ Erro no processamento: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

        return ChatResponse(
            response=f"Desculpe, ocorreu um erro: {str(e)}",
            conversation_id=request.conversation_id or "error",
            processing_time_seconds=asyncio.get_event_loop().time() - start_time,
            timestamp=datetime.now().isoformat()
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server_quick_start:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )
