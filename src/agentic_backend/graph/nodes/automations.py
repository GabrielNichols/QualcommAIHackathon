from __future__ import annotations
from typing import Dict, Any
from ...tools.mcp_client import MCPClient
from ...audit.evidence import EvidencePack

async def run(state: Dict[str, Any], mcp: MCPClient, ev: EvidencePack) -> Dict[str, Any]:
    # Gravar→generalizar: aqui você aplicaria parâmetros da automação (sites, datas, filtros)
    spec = state.get("automation_spec", {})
    steps = spec.get("steps", [])
    for step in steps:
        kind = step.get("kind")
        if kind == "open":
            res = await mcp.open_tab(step["url"])
            ev.log_step("open_tab", step | {"result": res})
        elif kind == "click":
            res = await mcp.click(step["selector"])
            ev.log_step("click", step | {"result": res})
        elif kind == "fill":
            res = await mcp.fill(step["selector"], step["value"])
            ev.log_step("fill", step | {"selector": step["selector"], "value": "***", "result": res})
    return state
