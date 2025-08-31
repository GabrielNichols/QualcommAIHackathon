from __future__ import annotations
import asyncio
from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from .settings import settings
from .utils.logging import setup_logging
from .utils.ids import new_job_id
from .graph.graph import build_graph
from .tools.mcp_client import MCPClient
from .audit.evidence import EvidencePack
from .graph.nodes.chatbot import ChatbotAgent
from .llm.engine import LLMEngine
from .embeddings.embedding import ONNXEmbedder
from .vectorstore.faiss_store import LocalFaiss
from .npu_monitor import npu_monitor

app = FastAPI(title="Agentic Browser Backend")
setup_logging()
_graph = build_graph()

class JobRequest(BaseModel):
    query: str | None = None
    form_spec: dict | None = None
    automation_spec: dict | None = None
    overlay_mode: bool = False

class ChatMessage(BaseModel):
    message: str
    user_context: Optional[Dict[str, Any]] = None
    enable_web_search: bool = True
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    processing_time_seconds: float
    npu_metrics: Dict[str, Any]
    rag_context_used: bool
    web_search_performed: bool
    timestamp: str

class ConversationSummary(BaseModel):
    conversation_id: str
    total_messages: int
    conversation_pairs: int
    topics_discussed: List[str]
    last_interaction: Optional[Dict[str, str]]

class NPUMetricsResponse(BaseModel):
    current_metrics: Dict[str, Any]
    average_metrics_1min: Dict[str, float]
    performance_score: float
    optimization_suggestions: List[str]
    timestamp: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run")
async def run_job(payload: JobRequest = Body(...)):
    job_id = new_job_id()
    ev = EvidencePack(job_id)
    mcp = MCPClient(settings.mcp_ws_url)

    # Estado inicial
    state = {
        "job_id": job_id,
        "query": payload.query,
        "form_spec": payload.form_spec,
        "automation_spec": payload.automation_spec,
        "overlay_mode": payload.overlay_mode,
    }

    # Usar nossa implementação SimpleGraph diretamente
    try:
        result = await _graph.invoke(state)
        return {"job_id": job_id, "state": result}
    except Exception as e:
        return {"job_id": job_id, "error": str(e), "state": state}

# Instância global do chatbot (inicializada sob demanda)
_chatbot_agent: Optional[ChatbotAgent] = None

async def get_chatbot_agent() -> ChatbotAgent:
    """Obtém ou inicializa o agente chatbot"""
    global _chatbot_agent
    if _chatbot_agent is None:
        # Inicializar componentes (em produção, usar injeção de dependência)
        llm_engine = LLMEngine()
        embedding_service = ONNXEmbedder(model_path="./models/nomic-embed-text.onnx/model.onnx")
        vector_store = LocalFaiss(dim=768, index_dir="./data/indexes")
        _chatbot_agent = ChatbotAgent(llm_engine, embedding_service, vector_store)

        # Iniciar monitoramento NPU
        npu_monitor.start_monitoring()

    return _chatbot_agent

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(message: ChatMessage = Body(...)):
    """
    Endpoint para conversação com o agente chatbot.

    - **message**: Mensagem do usuário
    - **user_context**: Contexto do usuário (opcional)
    - **enable_web_search**: Habilitar busca na internet (padrão: True)
    - **conversation_id**: ID da conversa para continuidade (opcional)

    Retorna resposta do chatbot com métricas de performance.
    """
    try:
        agent = await get_chatbot_agent()

        # Verificar se é primeiro acesso
        first_access = getattr(message, 'first_access', False)

        result = await agent.chat(
            message=message.message,
            user_context=message.user_context,
            enable_web_search=message.enable_web_search,
            first_access=first_access
        )

        # Gerar ID da conversa se não fornecido
        conversation_id = message.conversation_id or new_job_id()

        return ChatResponse(
            response=result["response"],
            conversation_id=conversation_id,
            processing_time_seconds=result["processing_time_seconds"],
            npu_metrics=result["npu_metrics"],
            rag_context_used=result["rag_context_used"],
            web_search_performed=result["web_search_performed"],
            timestamp=result["timestamp"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no chatbot: {str(e)}")

@app.get("/chat/summary/{conversation_id}", response_model=ConversationSummary)
async def get_conversation_summary(conversation_id: str):
    """
    Obtém resumo de uma conversa específica.

    - **conversation_id**: ID da conversa
    """
    try:
        agent = await get_chatbot_agent()
        summary = agent.get_conversation_summary()

        return ConversationSummary(
            conversation_id=conversation_id,
            total_messages=summary["total_messages"],
            conversation_pairs=summary["conversation_pairs"],
            topics_discussed=summary["topics_discussed"],
            last_interaction=summary["last_interaction"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter resumo: {str(e)}")

@app.post("/chat/clear/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """
    Limpa o histórico de uma conversa específica.

    - **conversation_id**: ID da conversa a ser limpa
    """
    try:
        agent = await get_chatbot_agent()
        agent.clear_conversation_history()

        return {"status": "success", "message": f"Conversa {conversation_id} limpa com sucesso"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar conversa: {str(e)}")

@app.get("/npu/metrics", response_model=NPUMetricsResponse)
async def get_npu_metrics():
    """
    Obtém métricas atuais de performance da NPU Snapdragon X Plus.

    Retorna métricas em tempo real e médias de 1 minuto.
    """
    try:
        report = npu_monitor.get_performance_report()

        return NPUMetricsResponse(
            current_metrics=report["current_metrics"],
            average_metrics_1min=report["average_metrics_1min"],
            performance_score=report["performance_score"],
            optimization_suggestions=report["optimization_suggestions"],
            timestamp=report["timestamp"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter métricas NPU: {str(e)}")

@app.post("/npu/monitoring/start")
async def start_npu_monitoring():
    """Inicia monitoramento da NPU"""
    try:
        npu_monitor.start_monitoring()
        return {"status": "success", "message": "Monitoramento NPU iniciado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar monitoramento: {str(e)}")

@app.post("/npu/monitoring/stop")
async def stop_npu_monitoring():
    """Para monitoramento da NPU"""
    try:
        npu_monitor.stop_monitoring()
        return {"status": "success", "message": "Monitoramento NPU parado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao parar monitoramento: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agentic_backend.server:app", host="0.0.0.0", port=settings.app_port, reload=True)
