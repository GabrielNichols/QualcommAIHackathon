from __future__ import annotations
from typing import Dict, Any
from ...tools.mcp_client import MCPClient
from ...audit.evidence import EvidencePack

async def run(state: Dict[str, Any], mcp: MCPClient, ev: EvidencePack) -> Dict[str, Any]:
    # Modo assistido: normalmente orquestrado via eventos do front.
    # Aqui, apenas logamos o estado. A lógica de overlay vive no Electron + LLM.
    ev.log_step("overlay", {"active": True})
    return state
