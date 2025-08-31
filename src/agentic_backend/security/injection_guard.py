from __future__ import annotations
from typing import Tuple

DANGEROUS_MARKERS = ["ignore previous", "override", "system instruction", "exfiltrate"]

def scan_prompt_injection(text: str) -> Tuple[bool, str]:
    low = text.lower()
    for marker in DANGEROUS_MARKERS:
        if marker in low:
            return True, f"Possível prompt-injection detectada: '{marker}'"
    return False, ""
