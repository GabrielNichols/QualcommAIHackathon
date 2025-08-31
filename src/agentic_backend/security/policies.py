from __future__ import annotations
from typing import List
from ..settings import settings

class Policy:
    @staticmethod
    def is_domain_allowed(domain: str) -> bool:
        d = domain.lower()
        if any(d.endswith(bad) for bad in settings.deny_domains):
            return False
        if settings.allow_domains and not any(d.endswith(ok) for ok in settings.allow_domains):
            return False
        return True

    @staticmethod
    def require_hitl_for(action: str) -> bool:
        # exemplos: "submit_form", "purchase", "delete"
        return action in {"purchase", "submit_sensitive", "delete"}
