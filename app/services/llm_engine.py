"""LLM Engine for intelligent scraping using DeepSeek via OpenRouter"""

import os
import json
import httpx
from typing import Optional
from app.services.models import SiteStrategy


class LLMEngine:
    """Uses DeepSeek to analyze sites and generate scraping strategies"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "deepseek/deepseek-chat-v4-pro"

    async def analyze_site(self, url: str) -> SiteStrategy:
        """
        Analyze a URL and determine the best scraping strategy.
        Uses DeepSeek to understand site structure and generate parsing instructions.
        """
        if not self.api_key:
            return self._get_fallback_strategy(url)

        prompt = f"""Você é um expert em web scraping. Analise a URL: {url}

1. Acesse a página principal e identifique:
   - Nome do site (domínio)
   - Se tem API própria (ex: MangaDex tem API REST)
   - Se usa Cloudflare ou proteção similar
   - Se requer JavaScript (requer Playwright)

2. Encontre a estrutura de capítulos:
   - Seletores CSS para encontrar links de capítulos
   - URLs dos capítulos disponíveis

3. Identifique como obter as imagens das páginas:
   - Como as imagens são carregadas (lazy loading, data attributes, etc)
   - Se há CDN ou imagens externas

4. Determine se há sitemap.xml útil

Responda APENAS em JSON válido com esta estrutura:
{{
  "site_name": "nome do site",
  "base_url": "url base",
  "has_api": true/false,
  "api_endpoint": "url da api se existir",
  "uses_cloudflare": true/false,
  "uses_javascript": true/false,
  "chapter_list_selector": "seletor css para lista de capítulos",
  "page_image_selector": "seletor css para imagem da página",
  "sitemap_url": "url do sitemap se existir",
  "parse_instructions": "instruções detalhadas de como fazer parse"
}}

Se não tiver certeza de algo, use valores padrão.
JSON apenas, sem texto adicional."""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    # Extract and parse JSON from response
                    json_str = self._extract_json(content)
                    if json_str:
                        parsed = json.loads(json_str)
                        return SiteStrategy(**parsed)

        except Exception as e:
            print(f"LLM analysis failed: {e}")

        return self._get_fallback_strategy(url)

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from LLM response"""
        # Try to find JSON in markdown code blocks
        import re
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return match.group(1)

        # Try raw JSON
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)

        return None

    def _get_fallback_strategy(self, url: str) -> SiteStrategy:
        """Get a fallback strategy when LLM is unavailable"""
        from urllib.parse import urlparse
        parsed = urlparse(url)

        # Detect common sites
        if "mangadex.org" in parsed.netloc:
            return SiteStrategy(
                site_name="MangaDex",
                base_url="https://mangadex.org",
                has_api=True,
                api_endpoint="https://api.mangadex.org",
                uses_javascript=False,
            )
        elif "mangapark" in parsed.netloc:
            return SiteStrategy(
                site_name="Mangapark",
                base_url=f"https://{parsed.netloc}",
                uses_javascript=True,
            )
        else:
            return SiteStrategy(
                site_name=parsed.netloc,
                base_url=f"https://{parsed.netloc}",
                uses_javascript=True,
            )

    async def filter_links(self, url: str, links: list[str]) -> list[str]:
        """
        Use LLM to filter out invalid links (ads, navigation, etc)
        Returns only valid chapter/content links.
        """
        if not self.api_key or len(links) <= 10:
            return links  # No filtering needed for small lists

        prompt = f"""Você é um expert em filtrar links de quadrinhos/mangás.
Temos a URL base: {url}
E uma lista de links:
{json.dumps(links[:50], indent=2)}

Remova todos os links que são:
- Anúncios (ads)
- Links de navegação do site
- Links para outras seções (não capítulos)
- Links quebrados ou inválidos

Retorne APENAS um JSON array com os links válidos.
Exemplo: ["link1", "link2", "link3"]

Se não tiver certeza, inclua o link (melhor incluir do que excluir)."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    json_str = self._extract_json(content)
                    if json_str:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, list):
                            return parsed

        except Exception as e:
            print(f"Link filtering failed: {e}")

        return links  # Return all if filtering fails