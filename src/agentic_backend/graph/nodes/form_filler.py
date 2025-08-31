from __future__ import annotations
from typing import Dict, Any
from ...tools.mcp_client import MCPClient
from ...security.policies import Policy
from ...audit.evidence import EvidencePack

async def run(state: Dict[str, Any], mcp: MCPClient, ev: EvidencePack) -> Dict[str, Any]:
    spec = state.get("form_spec", {})
    url = spec.get("url")
    if url and Policy.is_domain_allowed(url.split("//",1)[-1]):
        tab = await mcp.open_tab(url)
        ev.log_step("open_tab", {"url": url, "result": tab})
        # Preenche cada campo
        for field in spec.get("fields", []):
            await mcp.fill(field["selector"], field["value"])
            ev.log_step("fill", {"selector": field["selector"], "value": "***"})
        # Screenshot como evidência
        shot = await mcp.screenshot()
        ev.log_step("screenshot", {"path": shot.get("path")})
    return state
