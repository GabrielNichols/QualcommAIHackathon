from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore'  # Ignorar campos extras
    )

    app_env: str = "dev"
    app_port: int = 8080

    # Campos que serão processados como listas separadas por vírgula
    allow_domains_str: str = "itau.com.br"
    deny_domains_str: str = ""

    # Propriedades computadas para converter strings em listas
    @property
    def allow_domains(self) -> List[str]:
        """Converte string separada por vírgula em lista."""
        if not self.allow_domains_str:
            return []
        return [domain.strip() for domain in self.allow_domains_str.split(",") if domain.strip()]

    @property
    def deny_domains(self) -> List[str]:
        """Converte string separada por vírgula em lista."""
        if not self.deny_domains_str:
            return []
        return [domain.strip() for domain in self.deny_domains_str.split(",") if domain.strip()]

    data_dir: str = "./data"
    evidence_dir: str = "./data/evidence"
    index_dir: str = "./data/indexes"

    llm_model_path: str = "./models/llama-3.2-3b-qnn"
    embed_model_path: str = "./models/nomic-embed-text.onnx"

    mcp_ws_url: str = "ws://127.0.0.1:17872"

settings = Settings()
