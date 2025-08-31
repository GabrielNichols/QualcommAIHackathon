from __future__ import annotations
from typing import Dict, Any
from ...audit.evidence import EvidencePack
import json
from datetime import datetime

async def run(state: Dict[str, Any], llm_engine) -> Dict[str, Any]:
    """
    Reporter Agent com IA real - gera relatórios inteligentes e evidências.
    """

    # 1. Usar LLM para gerar resumo executivo
    query = state.get("query", "")
    selected_agent = state.get("selected_agent", "unknown")
    warnings = state.get("warnings", [])

    summary_prompt = f"""
    Você é especialista em geração de relatórios corporativos.
    Com base nestas informações de execução:

    Query original: "{query}"
    Agente executado: {selected_agent}
    Avisos de segurança: {warnings}

    Gere um resumo executivo profissional incluindo:
    1. Objetivo da operação
    2. Ações realizadas
    3. Resultados obtidos
    4. Status de segurança
    5. Recomendações

    Mantenha tom profissional e conciso.
    """

    try:
        executive_summary = llm_engine.generate_text(summary_prompt, max_length=500)
        state["executive_summary"] = executive_summary
    except Exception as e:
        state["executive_summary"] = f"Erro ao gerar resumo: {str(e)}"

    # 2. Gerar relatório técnico detalhado
    technical_report = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "agent": selected_agent,
        "security_warnings": warnings,
        "tabs_opened": len(state.get("tabs", [])),
        "findings_count": len(state.get("findings", [])),
        "citations_generated": bool(state.get("citations")),
        "processing_time": state.get("processing_time_seconds", 0),
        "npu_metrics": state.get("npu_metrics", {}),
        "status": "success" if not state.get("error") else "error"
    }

    # Usar LLM para analisar métricas de performance
    if technical_report["npu_metrics"]:
        metrics_analysis_prompt = f"""
        Analise estas métricas de performance da NPU: {technical_report['npu_metrics']}

        Forneça uma avaliação breve sobre:
        1. Eficiência energética
        2. Utilização da NPU
        3. Performance geral
        4. Recomendações de otimização
        """

        try:
            metrics_analysis = llm_engine.generate_text(metrics_analysis_prompt, max_length=200)
            technical_report["performance_analysis"] = metrics_analysis
        except Exception as e:
            technical_report["performance_analysis"] = f"Erro na análise: {str(e)}"

    state["technical_report"] = technical_report

    # 3. Gerar evidências estruturadas
    evidence_data = {
        "execution_summary": executive_summary,
        "technical_details": technical_report,
        "raw_state": {k: v for k, v in state.items() if k not in ['executive_summary', 'technical_report']}
    }

    # Salvar evidências (simulação - em produção usaria EvidencePack real)
    try:
        evidence_path = f"./data/evidence/evidence_{state.get('job_id', 'test')}.json"
        with open(evidence_path, 'w', encoding='utf-8') as f:
            json.dump(evidence_data, f, ensure_ascii=False, indent=2)

        state["evidence_path"] = evidence_path
        state["evidence_generated"] = True

    except Exception as e:
        state["evidence_error"] = str(e)
        state["evidence_generated"] = False

    # 4. Log da execução completa
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "job_id": state.get("job_id", "unknown"),
        "query": query,
        "agent": selected_agent,
        "success": technical_report["status"] == "success",
        "warnings_count": len(warnings),
        "processing_time": technical_report["processing_time"]
    }

    state["execution_log"] = log_entry

    return state
