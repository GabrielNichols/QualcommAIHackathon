"""
Cliente MCP (Model Context Protocol) simplificado via WebSocket.
O Electron/Browser deve expor um servidor MCP com ferramentas como
openTab, click, fill, extract, screenshot, etc.
"""
from __future__ import annotations
import asyncio
import json
import websockets
from typing import Any, Dict, Optional

class MCPClient:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self._conn: Optional[websockets.WebSocketClientProtocol] = None
        self._msgid = 0

    async def connect(self):
        if self._conn is None:
            self._conn = await websockets.connect(self.ws_url)

    async def disconnect(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def _call(self, method: str, params: Dict[str, Any]) -> Any:
        await self.connect()
        self._msgid += 1
        req = {"jsonrpc": "2.0", "id": self._msgid, "method": method, "params": params}
        await self._conn.send(json.dumps(req))
        resp_raw = await self._conn.recv()
        resp = json.loads(resp_raw)
        if "error" in resp:
            raise RuntimeError(resp["error"])
        return resp.get("result")

    # Exemplos de tools MCP
    async def open_tab(self, url: str) -> Any:
        return await self._call("tool/openTab", {"url": url})

    async def find(self, selector: Optional[str] = None, text: Optional[str] = None) -> Any:
        return await self._call("tool/find", {"selector": selector, "text": text})

    async def click(self, selector: str) -> Any:
        return await self._call("tool/click", {"selector": selector})

    async def fill(self, selector: str, value: str) -> Any:
        return await self._call("tool/fill", {"selector": selector, "value": value})

    async def extract(self, schema: Dict[str, Any]) -> Any:
        return await self._call("tool/extract", {"schema": schema})

    async def screenshot(self, area: Optional[Dict[str, int]] = None) -> Any:
        return await self._call("tool/screenshot", {"area": area or {}})
