#!/usr/bin/env python3
"""
Script de inicialização do projeto Agentic Browser Backend.
- Cria estrutura de diretórios
- Baixa modelos do Hugging Face
- Configura ambiente
- Executa testes básicos

Uso:
    python scripts/init_project.py
    python scripts/init_project.py --no-models  # Pula download de modelos
    python scripts/init_project.py --test      # Executa testes após setup
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

class ProjectInitializer:
    """Inicializador do projeto Agentic Browser Backend."""

    def __init__(self):
        self.root_dir = Path.cwd()
        self.models_dir = self.root_dir / "models"
        self.data_dir = self.root_dir / "data"
        self.test_data_dir = self.root_dir / "tests" / "data"

    def create_directories(self):
        """Criar estrutura de diretórios necessária."""
        directories = [
            self.models_dir,
            self.models_dir / "llama-3.2-3b-qnn",
            self.models_dir / "nomic-embed-text.onnx",
            self.data_dir,
            self.data_dir / "evidence",
            self.data_dir / "indexes",
            self.test_data_dir,
            self.test_data_dir / "evidence",
            self.test_data_dir / "indexes"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Diretório criado: {directory}")

    def setup_env_file(self):
        """Configurar arquivo .env."""
        env_example = self.root_dir / ".env.example"
        env_file = self.root_dir / ".env"

        if env_file.exists():
            logger.info("Arquivo .env já existe")
            return

        if env_example.exists():
            shutil.copy(env_example, env_file)
            logger.info("Arquivo .env criado a partir de .env.example")
        else:
            # Criar .env básico
            env_content = """# Configurações básicas
APP_ENV=dev
APP_PORT=8080

# Lista de domínios permitidos para automação
ALLOW_DOMAINS=itau.com.br,b3.com.br,cvm.gov.br,bcb.gov.br,sharepoint.com
DENY_DOMAINS=facebook.com,twitter.com,instagram.com

# Caminhos locais
DATA_DIR=./data
EVIDENCE_DIR=./data/evidence
INDEX_DIR=./data/indexes

# Modelos (serão atualizados após download)
LLM_MODEL_PATH=./models/llama-3.2-3b-qnn/model.onnx
EMBED_MODEL_PATH=./models/nomic-embed-text.onnx/model.onnx

# MCP
MCP_WS_URL=ws://127.0.0.1:17872
"""
            env_file.write_text(env_content, encoding='utf-8')
            logger.info("Arquivo .env criado com configurações básicas")

    def download_models(self, skip_models: bool = False):
        """Baixar modelos do Hugging Face."""
        if skip_models:
            logger.info("Pulando download de modelos (--no-models)")
            return

        download_script = self.root_dir / "scripts" / "download_models.py"

        if not download_script.exists():
            logger.warning("Script de download não encontrado. Pulando...")
            return

        logger.info("Iniciando download de modelos...")
        try:
            result = subprocess.run([
                sys.executable, str(download_script),
                "--update-env"
            ], capture_output=True, text=True, cwd=self.root_dir)

            if result.returncode == 0:
                logger.info("✅ Modelos baixados com sucesso!")
            else:
                logger.warning("⚠️  Falha no download de modelos:")
                logger.warning(result.stderr)

        except Exception as e:
            logger.error(f"Erro ao executar download: {e}")

    def install_dependencies(self):
        """Instalar dependências do projeto."""
        logger.info("Instalando dependências...")

        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-e", "."
            ], capture_output=True, text=True, cwd=self.root_dir)

            if result.returncode == 0:
                logger.info("✅ Dependências instaladas!")
            else:
                logger.error("❌ Erro na instalação:")
                logger.error(result.stderr)
                return False

        except Exception as e:
            logger.error(f"Erro na instalação: {e}")
            return False

        return True

    def run_basic_tests(self, run_tests: bool = False):
        """Executar testes básicos."""
        if not run_tests:
            return

        logger.info("Executando testes básicos...")

        try:
            # Teste de importação
            result = subprocess.run([
                sys.executable, "-c",
                "from agentic_backend.server import app; print('✅ Imports OK')"
            ], capture_output=True, text=True, cwd=self.root_dir)

            if result.returncode == 0:
                logger.info("✅ Testes básicos passaram!")
            else:
                logger.error("❌ Falha nos testes:")
                logger.error(result.stderr)

        except Exception as e:
            logger.error(f"Erro nos testes: {e}")

    def create_test_data(self):
        """Criar dados de teste."""
        # Arquivo de teste para extração
        test_html = self.test_data_dir / "test_page.html"
        test_html.write_text("""
<!DOCTYPE html>
<html>
<head><title>Test Page - Itaú</title></head>
<body>
    <h1>Relatório de Investimentos</h1>
    <div class="summary">
        <p>Valor total: R$ 1.250.000,00</p>
        <p>Data: 15/08/2024</p>
    </div>
    <table class="investments">
        <tr><th>Ativo</th><th>Quantidade</th><th>Preço</th></tr>
        <tr><td>PETR4</td><td>1000</td><td>R$ 25,50</td></tr>
        <tr><td>VALE3</td><td>500</td><td>R$ 58,90</td></tr>
    </table>
    <form id="contact">
        <input name="nome" value="João Silva">
        <input name="email" value="joao@itau.com.br">
        <button type="submit">Enviar</button>
    </form>
</body>
</html>
        """, encoding='utf-8')

        logger.info(f"Dados de teste criados: {test_html}")

    def show_summary(self):
        """Mostrar resumo da inicialização."""
        print("\n" + "="*60)
        print("🎉 AGENTIC BROWSER BACKEND - INICIALIZAÇÃO CONCLUÍDA")
        print("="*60)
        print(f"📁 Diretório raiz: {self.root_dir}")
        print(f"🤖 Modelos: {self.models_dir}")
        print(f"📊 Dados: {self.data_dir}")
        print()
        print("🚀 Para iniciar o servidor:")
        print("   uvicorn agentic_backend.server:app --reload --port 8080")
        print()
        print("🧪 Para executar testes:")
        print("   python -m pytest tests/")
        print()
        print("📚 Para mais informações:")
        print("   cat README.md")
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description="Inicialização do Agentic Browser Backend")
    parser.add_argument("--no-models", action="store_true", help="Pular download de modelos")
    parser.add_argument("--test", action="store_true", help="Executar testes após setup")
    parser.add_argument("--no-deps", action="store_true", help="Pular instalação de dependências")

    args = parser.parse_args()

    initializer = ProjectInitializer()

    logger.info("🚀 Iniciando configuração do Agentic Browser Backend...")

    # Criar estrutura
    initializer.create_directories()

    # Configurar ambiente
    initializer.setup_env_file()

    # Instalar dependências
    if not args.no_deps:
        if not initializer.install_dependencies():
            sys.exit(1)

    # Baixar modelos
    initializer.download_models(args.no_models)

    # Criar dados de teste
    initializer.create_test_data()

    # Executar testes
    initializer.run_basic_tests(args.test)

    # Mostrar resumo
    initializer.show_summary()

if __name__ == "__main__":
    import argparse
    main()
