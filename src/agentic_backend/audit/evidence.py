from __future__ import annotations
import os, io, zipfile, json, time
from typing import List, Dict, Any
from ..settings import settings

class EvidencePack:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.records: List[Dict[str, Any]] = []
        os.makedirs(settings.evidence_dir, exist_ok=True)

    def log_step(self, kind: str, detail: Dict[str, Any]):
        self.records.append({
            "ts": time.time(),
            "kind": kind,
            "detail": detail,
        })

    def build_zip(self) -> str:
        out = os.path.join(settings.evidence_dir, f"evidence_{self.job_id}.zip")
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("log.json", json.dumps(self.records, ensure_ascii=False, indent=2))
            # screenshots/artefatos devem ser adicionados aqui (paths vindos das tools MCP)
        return out
