from __future__ import annotations
from typing import Dict, Any
import logging

log = logging.getLogger(__name__)

def route(state: Dict[str, Any]) -> str:
    """
    Roteia para o agente apropriado baseado no estado e contexto.
    Prioriza onboarding para primeiro acesso.
    """

    # Primeiro acesso - sempre vai para onboarding
    if state.get("first_access", False):
        log.info("🎯 Primeiro acesso detectado (flag) - roteando para onboarding")
        return "onboarding"

    # Detectar primeiro acesso pelo conteúdo da mensagem
    message = state.get("message", "").lower() if state.get("message") else ""
    if message:
        first_access_indicators = [
            "primeiro acesso", "primeira vez", "novo usuário", "nova conta",
            "começar", "iniciar", "não tenho conta", "sou novo", "nova aqui",
            "novo aqui", "primeira vez que entro", "primeira vez que uso",
            "novo no sistema", "nova no sistema"
        ]

        if any(indicator in message.lower() for indicator in first_access_indicators):
            log.info("🎯 Primeiro acesso detectado (conteúdo) - roteando para onboarding")
            return "onboarding"

    # Verificar se usuário precisa de atualização de contexto
    if state.get("update_context", False):
        log.info("🔄 Atualização de contexto solicitada - roteando para onboarding")
        return "onboarding"

    # Verificar se deve ir para chatbot (conversação geral)

    # Palavras-chave que indicam conversação geral (não pesquisa específica)
    chatbot_keywords = [
        "olá", "oi", "bom dia", "boa tarde", "boa noite",
        "quero", "gostaria", "poderia", "pode me", "me ajude",
        "como", "qual", "quando", "onde", "por que", "o que",
        "explique", "conte", "fale", "diga"
    ]

    # Verificar se a mensagem contém palavras de conversação
    is_conversation = any(keyword in message for keyword in chatbot_keywords)

    # Se não há especificação de tarefa específica E é conversação, vai para chatbot
    if is_conversation and not any([
        state.get("form_spec"),
        state.get("automation_spec"),
        state.get("overlay_mode"),
        "pesquisa" in message,
        "buscar" in message,
        "procurar" in message,
        "encontrar" in message
    ]):
        log.info("💬 Conversação geral detectada - roteando para chatbot")
        return "chatbot"

    # Roteamento normal baseado no objetivo
    if state.get("form_spec"):
        log.info("📝 Formulário detectado - roteando para form_filler")
        return "form_filler"

    if state.get("automation_spec"):
        log.info("⚙️ Automação detectada - roteando para automations")
        return "automations"

    if state.get("overlay_mode"):
        log.info("👁️ Modo overlay detectado - roteando para overlay")
        return "overlay"

    # Padrão: researcher para pesquisas específicas
    log.info("🔍 Requisição de pesquisa - roteando para researcher")
    return "researcher"
