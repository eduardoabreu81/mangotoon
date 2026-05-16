# Comic Library Downloader — Especificação Técnica

## 1. Visão Geral do Projeto

**Nome:** ComicLib  
**Tipo:** Aplicação web full-stack (Python FastAPI + Frontend HTML/JS)  
**Objetivo:** Baixar scans de quadrinhos de múltiplos sites, armazenar localmente e disponibilizar leitura offline via browser  
**LLM:** DeepSeek v4 (configurado no OpenCode) para scraping inteligente

---

## 2. Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Web)                          │
│   Leitor web estilo Mangapark + Biblioteca + Gestão de leitura │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────▼────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │  LLM     │  │ Scraper   │  │ Biblioteca│  │ Reader API     │  │
│  │ Engine   │  │ Engine    │  │ Manager   │  │                │  │
│  └──────────┘  └───────────┘  └──────────┘  └─────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼────────────────────┐
         ▼                   ▼                    ▼
   ┌───────────┐      ┌────────────┐       ┌─────────────┐
   │  Arquivos │      │  Google    │       │  Sites      │
   │  Locais   │      │  Drive     │       │  (sources)  │
   │  (imgs)   │      │  (futuro)  │       │             │
   └───────────┘      └────────────┘       └─────────────┘
```

---

## 3. Especificação de Componentes

### 3.1 Backend — FastAPI

#### Endpoints principais:

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/library` | Lista todos os quadrinhos na biblioteca |
| GET | `/api/library/{id}` | Detalhes de um quadrinho |
| POST | `/api/library/add` | Adiciona URL para baixar |
| DELETE | `/api/library/{id}` | Remove da biblioteca |
| GET | `/api/reader/{id}/{chapter}/{page}` | Serve imagem do capítulo |
| POST | `/api/reader/{id}/progress` | Atualiza progresso de leitura |
| GET | `/api/reader/{id}/progress` | Pega progresso de leitura |
| GET | `/api/download/{id}/status` | Status do download |
| POST | `/api/settings` | Salva configurações |
| GET | `/api/settings` | Pega configurações |

#### Modelos de dados:

```python
class Comic(BaseModel):
    id: str                    # UUID gerado
    title: str                 # Nome do quadrinho
    source_url: str            # URL original
    source_site: str           # Domínio do site (mangadex.org, etc)
    cover_url: str            # URL da capa
    total_chapters: int        # Total de capítulos
    downloaded_chapters: list  # Capítulos baixados
    status: str                # "pending" | "downloading" | "complete" | "error"
    last_read_chapter: int     # Último capítulo lido
    last_read_page: int        # Última página lida
    created_at: datetime
    updated_at: datetime

class Chapter(BaseModel):
    number: float              # Número do capítulo (1, 1.5, 2, etc)
    title: str                 # Título do capítulo
    pages: list[str]           # Lista de URLs/caminhos das páginas
    downloaded: bool          # Se já foi baixado
    path: str                  # Caminho local se baixado

class ReadingProgress(BaseModel):
    comic_id: str
    chapter: float
    page: int
    completed: bool
    updated_at: datetime
```

### 3.2 LLM Engine (Scraping Inteligente)

**Responsabilidade:** usar DeepSeek para analisar sites e determinar estratégia de scraping.

**Fluxo:**
1. Recebe URL → Extrai domínio base
2. Consulta `site_handlers/` para ver se há handler específico
3. Se não houver, usa LLM para:
   - Acessar sitemap do site ou detectar estrutura
   - Identificar links de capítulos vs ads/links errados
   - Determinar se há Cloudflare/JSCaptcha
   - Gerar script de scraping customizado

**Prompt base para LLM:**
```
Você é um expert em web scraping. Analise a URL: {url}

1. Acesse a página principal
2. Encontre todos os links de capítulos de mangá/comic
3. Filtre apenas links válidos (ignore ads, links de navegação, etc)
4. Identifique a estrutura de páginas de capítulo
5. Determine como extrair as imagens do capítulo (lazy loading, data attributes, etc)
6. Verifique se há proteção (Cloudflare, CAPTCHA, etc)

Responda em JSON com a estratégia de scraping.
```

### 3.3 Scraper Engine

**Features:**
- Download paralelo com rate limiting adaptativo
- Detecção e bypass de ads (filtra iframes, links externos, etc)
- Retry automático com backoff exponencial
- Detecção de Cloudflare (ativa modo browser fingerprint se necessário)
- Suporte a sitemap.xml e listagem de páginas
- Cookie jar para sessões persistentes

**Sites suportados (v1):**
- MangaDex (API própria, fácil)
- Mangapark (estrutura simples)
- LR-Scan (estrutura variável)
- TuMangaOnline (ES,相似的 estrutura)

### 3.4 Biblioteca Local

**Formato de armazenamento:**

```
/comic-library/
├── config.json              # Configurações do app
├── library.json             # Metadados da biblioteca
└── comics/
    └── {comic_id}/
        ├── metadata.json     # Metadados do quadrinho
        ├── cover.jpg        # Capa
        └── chapters/
            ├── 1/
            │   ├── 001.jpg
            │   ├── 002.jpg
            │   └── ...
            ├── 2/
            └── ...
```

**Metadados (`metadata.json`):**
```json
{
  "id": "uuid",
  "title": "One Piece",
  "source_url": "https://mangadex.org/title/...",
  "source_site": "mangadex.org",
  "cover_path": "cover.jpg",
  "chapters": [
    {"number": 1, "title": "Romance Dawn", "path": "chapters/1", "pages": 17},
    {"number": 2, "title": "Luffy", "path": "chapters/2", "pages": 14}
  ],
  "reading_progress": {
    "last_chapter": 1,
    "last_page": 5,
    "completed_chapters": []
  }
}
```

### 3.5 Frontend — Web Reader

**Tela principal (Biblioteca):**
- Grid de capas com hover mostrando título + progresso
- Filtro por: site origem, status (lido/não lido), progresso
- Busca por título
- Botão adicionar URL (modal)

**Reader:**
- Layout estilo Mangapark: imagem centralizada + navegação lateral
- Navegação por swipe (mobile) ou teclado (← →)
- Indicador de página: "Página 5/17"
- Menu: capítulos, ajustes de zoom, fullscreen
- Barra inferior: progresso do capítulo

**Gestão de leitura:**
- Marca como lido/não lido
- Histórico de leitura por quadrinho
- Filtro "Em andamento" / "Completo"

---

## 4. Stack Técnico

| Camada | Tecnologia |
|--------|-------------|
| Backend | Python 3.11+ / FastAPI |
| LLM | DeepSeek via OpenCode (OpenRouter) |
| HTTP Client | httpx (async) + playwright (para sites com JS) |
| Armazenamento | JSON (metadata) +文件系统 (imagens) |
| Frontend | HTML5 + CSS3 + Vanilla JS (sem framework) |
| Server | Uvicorn (dev) + gunicorn (prod) |

---

## 5. Fluxo de Adição de Comic

```
1. Usuário cola URL na modal
   ↓
2. Backend recebe URL → identifica site
   ↓
3. LLM Engine analisa site → determina estratégia
   ↓
4. Scraper extrai lista de capítulos (filtrando ads)
   ↓
5. Baixa capa + metadados → salva em /comics/{id}/
   ↓
6. Download de capítulos começa em background
   ↓
7. Status atualizado em tempo real (Server-Sent Events ou polling)
   ↓
8. Comic aparece na biblioteca com progresso
```

---

## 6. Considerações de Scraping

| Site | Método | Dificuldade |
|------|--------|-------------|
| MangaDex | API REST | ★☆☆☆☆ |
| Mangapark | HTML parsing | ★★☆☆☆ |
| LR-Scan | HTML + sitemap | ★★★☆☆ |
| TuMangaOnline | HTML + lazy load | ★★☆☆☆ |
| Sites unknown | LLM-guided | ★★★★☆ |

---

## 7. Roadmap de Implementação

**Fase 1 — Core:**
- [x] SPEC.md
- [ ] Projeto base (FastAPI + pasta comics/)
- [ ] Endpoint básico `/api/library`
- [ ] Scraper simples (MangaDex como primeiro site)

**Fase 2 — LLM Integration:**
- [ ] LLM Engine com DeepSeek
- [ ] Handler genérico para sites desconhecidos
- [ ] Detecção de ads/links inválidos

**Fase 3 — Biblioteca & Reader:**
- [ ] Frontend biblioteca (grid + modal adicionar)
- [ ] Frontend reader (estilo Mangapark)
- [ ] Progress tracking

**Fase 4 — Polish:**
- [ ] Suporte a mais sites
- [ ] Google Drive connector (futuro)
- [ ] Docker-compose

---

## 8. Definições de Sucesso

1. ✅ Usuário adiciona URL → sistema detecta site → baixa automaticamente
2. ✅ LLM filtra links inválidos/ads com precisão > 90%
3. ✅ Quadrinho fica disponível offline após download
4. ✅ Reader carrega em < 500ms por página (local)
5. ✅ Progresso de leitura persiste entre sessões

---

*Documento gerado em: 2025-05-16*  
*Atualizado por: Hermes Agent + OpenCode (DeepSeek v4)*