"""
Web Scraper compatível com ARM usando BeautifulSoup + requests.
Alternativa leve ao Crawl4AI para extração de conteúdo web.
"""

import requests
import time
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import logging

logger = logging.getLogger(__name__)


class ARMCompatibleWebScraper:
    """
    Web scraper compatível com ARM usando BeautifulSoup e requests.
    Implementação leve e confiável para extração de conteúdo web.
    """

    def __init__(self, user_agent: Optional[str] = None, timeout: int = 10):
        """
        Inicializa o web scraper.

        Args:
            user_agent: User agent para requests (opcional)
            timeout: Timeout em segundos para requests
        """
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.timeout = timeout
        self.session = requests.Session()

        # Configurar headers
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def scrape_url(self, url: str, extract_metadata: bool = True) -> Dict[str, Any]:
        """
        Faz scraping de uma URL específica.

        Args:
            url: URL a ser raspada
            extract_metadata: Se deve extrair metadados da página

        Returns:
            Dicionário com conteúdo extraído
        """
        try:
            logger.info(f"Fazendo scraping de: {url}")

            # Fazer request
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Parse do HTML
            soup = BeautifulSoup(response.content, 'lxml')

            # Extrair conteúdo principal
            content = self._extract_main_content(soup)

            # Extrair metadados se solicitado
            metadata = {}
            if extract_metadata:
                metadata = self._extract_metadata(soup, url)

            # Limpar e formatar conteúdo
            clean_content = self._clean_content(content)

            return {
                'url': url,
                'title': self._extract_title(soup),
                'content': clean_content,
                'metadata': metadata,
                'status_code': response.status_code,
                'success': True,
                'error': None
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de request para {url}: {e}")
            return {
                'url': url,
                'title': '',
                'content': '',
                'metadata': {},
                'status_code': None,
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Erro inesperado ao raspar {url}: {e}")
            return {
                'url': url,
                'title': '',
                'content': '',
                'metadata': {},
                'status_code': None,
                'success': False,
                'error': str(e)
            }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrai o título da página."""
        # Tentar title tag primeiro
        title_tag = soup.find('title')
        if title_tag and title_tag.get_text().strip():
            return title_tag.get_text().strip()

        # Tentar h1
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.get_text().strip():
            return h1_tag.get_text().strip()

        return "Sem título"

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extrai o conteúdo principal da página."""
        # Remover elementos não desejados
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            element.decompose()

        # Tentar encontrar conteúdo principal por seletores comuns
        content_selectors = [
            'main',
            '[class*="content"]',
            '[class*="main"]',
            '[class*="article"]',
            '[class*="post"]',
            'article',
            '.entry-content',
            '#content',
            '#main'
        ]

        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                return content_element.get_text(separator=' ', strip=True)

        # Fallback: usar body
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)

        # Último fallback: todo o texto da página
        return soup.get_text(separator=' ', strip=True)

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extrai metadados da página."""
        metadata = {
            'description': '',
            'keywords': [],
            'author': '',
            'published_date': '',
            'domain': urlparse(url).netloc
        }

        # Meta description
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        if desc_meta:
            metadata['description'] = desc_meta.get('content', '')

        # Meta keywords
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta:
            keywords_content = keywords_meta.get('content', '')
            if keywords_content:
                metadata['keywords'] = [k.strip() for k in keywords_content.split(',')]

        # Meta author
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta:
            metadata['author'] = author_meta.get('content', '')

        # Open Graph description (fallback)
        if not metadata['description']:
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc:
                metadata['description'] = og_desc.get('content', '')

        return metadata

    def _clean_content(self, content: str) -> str:
        """Limpa e formata o conteúdo extraído."""
        if not content:
            return ""

        # Remover múltiplos espaços em branco
        content = re.sub(r'\s+', ' ', content)

        # Remover caracteres especiais indesejados
        content = re.sub(r'[\\n\\r\\t]+', ' ', content)

        # Limitar tamanho (evitar conteúdos muito grandes)
        max_length = 10000
        if len(content) > max_length:
            content = content[:max_length] + "..."

        return content.strip()

    def search_web(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Faz busca na web usando Google (através de scraping).

        Args:
            query: Termo de busca
            max_results: Número máximo de resultados

        Returns:
            Lista de resultados da busca
        """
        try:
            # URL de busca do Google
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={max_results * 2}"

            # Fazer scraping da página de resultados
            search_results = self.scrape_url(search_url, extract_metadata=False)

            if not search_results['success']:
                return []

            # Parse dos resultados (simplificado)
            soup = BeautifulSoup(search_results['content'], 'lxml')

            results = []
            # Tentar encontrar links de resultados
            result_links = soup.find_all('a', href=True)

            for link in result_links[:max_results]:
                href = link['href']
                # Filtrar apenas links de resultados (não de navegação)
                if href.startswith('/url?q=') and 'google.com' not in href:
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    title = link.get_text().strip()

                    if title and actual_url:
                        results.append({
                            'title': title,
                            'url': actual_url,
                            'snippet': '',
                            'source': 'google_search'
                        })

            return results

        except Exception as e:
            logger.error(f"Erro na busca web: {e}")
            return []

    def scrape_multiple_urls(self, urls: List[str], delay: float = 1.0) -> List[Dict[str, Any]]:
        """
        Faz scraping de múltiplas URLs com delay entre requests.

        Args:
            urls: Lista de URLs a raspar
            delay: Delay em segundos entre requests

        Returns:
            Lista de resultados do scraping
        """
        results = []

        for i, url in enumerate(urls):
            logger.info(f"Processando URL {i+1}/{len(urls)}: {url}")

            result = self.scrape_url(url)
            results.append(result)

            # Adicionar delay entre requests (exceto no último)
            if i < len(urls) - 1:
                time.sleep(delay)

        return results

    def close(self):
        """Fecha a sessão HTTP."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Função utilitária para criar scraper com configurações padrão
def create_web_scraper(user_agent: Optional[str] = None, timeout: int = 10) -> ARMCompatibleWebScraper:
    """
    Cria um ARMCompatibleWebScraper com configurações padrão.

    Args:
        user_agent: User agent personalizado (opcional)
        timeout: Timeout em segundos

    Returns:
        Instância configurada do scraper
    """
    return ARMCompatibleWebScraper(user_agent=user_agent, timeout=timeout)


# Exemplo de uso
if __name__ == "__main__":
    # Exemplo de uso
    with create_web_scraper() as scraper:
        result = scraper.scrape_url("https://www.google.com")
        print(f"Título: {result['title']}")
        print(f"Conteúdo: {result['content'][:200]}...")

        # Busca web
        search_results = scraper.search_web("Itaú banco", max_results=2)
        for result in search_results:
            print(f"Resultado: {result['title']} - {result['url']}")
