# Landis AI — Réplica do Manus AI (v2)

> **Objetivo:** Continuar o legado do Manus AI — um agente geral autônomo com computador virtual, navegador, código, arquivos, integrações e entregáveis — usando apenas ferramentas open-source e camadas gratuitas.

Este documento é a **especificação canônica da réplica perfeita** construída sobre o código-base `ai-manus` (Simpleyyt). Ele consolida as informações do `objetivo.txt` (23-24/out/2026), da documentação oficial do Manus, e do guia prático "Como montar um Manus gratuito".

---

## 1. O que é o Manus (e o que a réplica deve ser)

**Manus AI é uma plataforma de agentes que tenta transformar instruções em linguagem natural em trabalho executado, usando computador virtual, navegador, arquivos, código, integrações e modelos de IA para produzir resultados como relatórios, planilhas, sites, apresentações, vídeos, jogos e automações.**

A réplica (Landis AI) replica essa **camada de execução**:

```
Intenção (linguagem natural)
  ↓
Orquestração (planejamento, decomposição, seleção de ferramentas)
  ↓
Execução (navegador + terminal + arquivos + código + APIs + conectores)
  ↓
Observação e verificação (erro → corrige, repete)
  ↓
Entrega (relatório, planilha, slide, site, dashboard, vídeo, automação)
```

Não é "chatbot com busca". É **agente com computador**.

### Diferença chatbot × agente

| Chatbot | Agente (Manus/Landis) |
|---------|----------------------|
| Responde dentro da conversa | Cria plano, divide subtarefas |
| Explica como fazer | Executa no sandbox |
| Usuário conduz passo a passo | Continua sem instrução por vários passos |
| Entrega texto | Entrega artefatos (pptx, xlsx, site, repo) |

---

## 2. Arquitetura da Réplica

### Visão em camadas

```
Interface (web, mobile, Slack, API, Telegram)
  ↓
Contexto (instrução, arquivos, projeto, skills, permissões)
  ↓
Orquestração (planner, executor, verificação, Wide Research)
  ↓
Execução (sandbox Docker, browser Use/Playwright, shell, file, search, MCP)
  ↓
Memória operacional (todo.md + filesystem como memória externa)
  ↓
Entrega (slides, docs, planilhas, sites, automações)
```

### Fluxo Plan-Act (já implementado)

1. **Planner** cria `Plan` com `title`, `goal`, `language`, `steps` (3-5 passos, inclui verify).
2. **Executor** executa um step por vez, chamando tools (shell/browser/file/search/mcp).
3. Se step falha → **Planner.update_plan** reescreve passos restantes.
4. Quando todos completos → **summarize** via `deliver_result`.
5. Todo evento via WebSocket (`/ws/chat`, `/ws/sessions`, `/ws/vnc/{session_id}`).

### Filesystem como memória

O contexto do LLM é limitado. Landis usa o disco como memória externa:

- `todo.md` reescrito a cada passo (planejador cuida disso, não executor).
- Páginas e resultados salvos em `/workspace/` e relidos via `cat`/`grep`/`glob`.
- Erros mantidos no contexto para correção.

### Sandbox

- **Docker local** (grátis para sempre, recomendado): `python:3.12-slim` + Chrome + VNC.
- **E2B** (créditos iniciais ~US$100, sessões 1h): scaffold em `backend/app/infrastructure/external/sandbox/e2b_sandbox.py`.
- **Daytona** (créditos, código público descontinuado jun/2026): scaffold em `daytona_sandbox.py`.
- Isolamento por tarefa, TTL 30min, rede `manus-network`, browser via VNC → NoVNC.

---

## 3. Componentes do Manus 2.0 e status na réplica

| Componente Manus 2.0 | O que faz | Status na réplica |
|---------------------|-----------|-------------------|
| **Cascade** (agent harness) | Novo harness de agente (set/2026) | ✅ Equivalente: `PlanActFlow` + `AgentLoopFlow` (planner/executor loop, masking por estado) |
| **Manus Studio** | Workspace compartilhado pessoa + IA | ✅ Projects com `instruction`, shared sessions, Library |
| **Cloud Computer** | VM persistente para bots/sites | 🟡 Scaffold: `CloudComputer` model + Docker/E2B persistente (este commit) |
| **Automations** | Schedule / Triggered / Advanced | 🟡 Scaffold: `Automation` model + Celery beat (este commit) |
| **Wide Research** | Paralelização (até 250 itens) | ✅ Implementado: `WideResearchCoordinator` com `asyncio.gather`, max 3 paralelos (cota grátis) |
| **Browser Operator** | Opera navegador local autenticado | ✅ `BrowserToolkit` com takeover + VNC |
| **Video Editor** | Timeline com componentes | ⏳ Planejado: usa FAL AI + FFmpeg no sandbox |
| **Game Dev** | Cria jogos multiplayer | ⏳ Planejado: sandbox + Vite + deploy |
| **Skills + MCP** | Procedimentos reutilizáveis + conectores | ✅ `SkillToolkit` + `MCPToolkit` + catalog `/skills/{name}/SKILL.md` |
| **Computer Use (local)** | CLI no computador do usuário | ⏳ Planejado: `My Computer` via aprovação explícita |
| **Slides (Nano Banana Pro)** | 12 slides, PPTX/PDF/Google Slides | ✅ Skill `slides` + python-pptx |
| **Website Builder** | Full-stack + Stripe/Maps/Auth | ✅ Sandbox + `deploy & expose` planejado |
| **Search** | Bing, Google, Tavily, etc | ✅ + **SearXNG**, **Exa**, **Firecrawl**, **Brave** (este commit) |

---

## 4. Como montar grátis (guia prático condensado)

### 4.1 LLM (gargalo, não software)

| Provedor | Limite grátis (out/2026) | Uso recomendado |
|----------|--------------------------|-----------------|
| **Ollama local** | só sua RAM | Principal (sem limite) |
| **OpenRouter :free** | 20 req/min, 50/dia (1000/dia após US$10) | Reserva |
| **Groq** | 30 req/min, 1k/dia, 200k tokens/dia | Subtarefas curtas |
| **Google AI Studio** | varia, aparece no console | Reserva (cuidado: treino fora UE/CH/UK) |
| **Cloudflare Workers AI** | 10k neurons/dia | Cota fixa |
| Mistral Free | US$10/mês créditos | Desative treino |

**Modelos Ollama por RAM:**

- 16 GB: `gpt-oss:20b` (tool calling OK)
- 24-32 GB: `qwen3-coder:30b` (melhor local)
- 8-12 GB: `qwen3:8b` / `gemma3` (tarefas simples)

> Exija **tool calling**. Modelos pequenos sem tool calling travam o loop.

**Arquitetura recomendada custo zero:**

```
Principal: Ollama (localhost:11434)
Reserva: OpenRouter :free ou Gemini
Fallback: Groq (resumir, classificar)
Na frente: LiteLLM para troca automática quando cota estoura
```

Este commit mantém `LLM_PROVIDER=langchain|openai` + `MODEL_PROVIDER=openai|deepseek|anthropic|ollama|orcarouter`.

Exemplos em `docs/en/configuration.md` e `.env.example`.

### 4.2 Sandbox grátis

```bash
mkdir -p workspace
docker run -d --name agent-sandbox --memory 2g --cpus 2 \
  -v "$PWD/workspace:/workspace" -w /workspace \
  python:3.12-slim sleep infinity
docker exec agent-sandbox pip install -q requests beautifulsoup4 pandas matplotlib python-pptx python-docx openpyxl
```

Nuvem opcional: E2B (créditos iniciais), Daytona (gerenciado).

**Segurança mínima:**

- Monte só `workspace`, nunca `~`.
- Limite CPU/memória, nunca deixe chaves dentro do container.
- Ative `[sandbox]` no config (OpenManus vem desligado).

### 4.3 Busca e navegador (grátis)

**Busca:**

```bash
docker run -d -p 8080:8080 searxng/searxng  # habilite json em settings.yml → search.formats
```

Alternativas: Tavily (1000 créd/mês, sem cartão), DuckDuckGo (lib, sem chave, pode bloquear).

> Brave Search free acabou fev/2026 (US$5 créditos), Bing API descontinuada.

**Navegador (browser-use, MIT, 100k+ stars):**

```bash
uv pip install browser-use
uvx browser-use install  # Chromium
```

Para screenshots, use modelo com visão (`qwen3-vl:8b`).

### 4.4 Instalação OpenManus (alternative path, 20min)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://github.com/FoundationAgents/OpenManus.git
cd OpenManus
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -r requirements.txt
playwright install
cp config/config.example.toml config/config.toml
# editar config.toml → [llm] ollama ou openrouter
python main.py
```

Este repo (Landis) **já é** o caminho C (AI Manus com WebUI + sandbox + progresso realtime).

### 4.5 Agente mínimo (60 linhas, referência)

Ver `objetivo.txt` seção 10 (`mini_manus.py`): loop modelo → tool → sandbox → observação, com `todo.md` e `finish`.

---

## 5. Wide Research — Detalhe de implementação

**Na réplica:**

```python
coordinator = WideResearchCoordinator(
    agent_id=agent_id,
    llm=llm,
    sandbox=sandbox,
    browser=browser,
    search_engine=search_engine,
    max_parallel=3,  # cota grátis: 2-3, mais estoura
)
tasks = coordinator.decompose(goal="compare 100 products", items=product_list)
async for event in coordinator.run_parallel(tasks):
    yield event  # progress → WebSocket
await coordinator.synthesize(goal, results)
```

- Cada subagente tem contexto limpo.
- Salva em `/workspace/wide_research/{id}.md`.
- Agregador cria `/workspace/wide_research_report.md` + tabela.

Limite comercial (250 itens, 100 subagentes) é alegação de fornecedor; na réplica, 3 paralelos é o prático para cotas grátis.

---

## 6. Automations — Três padrões

1. **Schedule:** cron (ex: `0 9 * * 1` → toda segunda 9h)
2. **Triggered:** evento (PR, reembolso > limite, email novo)
3. **Advanced:** fontes + condições + ações (ex: extrair fatura → atualizar planilha → Slack)

Modelo em `backend/app/domain/models/automation.py`, com `AutomationRun` para histórico.

Execução:

- `TASK_BACKEND=local`: asyncio loop checa `next_run_at`
- `TASK_BACKEND=celery`: Celery Beat scheduler

---

## 7. Segurança — o que o Manus ensinou

**Superfície de ataque do agente > chatbot:** lê emails, navega, tem tokens (Gmail, Dropbox, GitHub).

Caso Dark Reading (set/2026, Salt Labs): email com prompt injection + código ofuscado → payload → roubo de credenciais. Meta confirmou e corrigiu via bug bounty.

**Mitigações na réplica:**

- Prompt injection: tratar web/email como não confiável, não executar instruções de conteúdo externo sem confirmação humana.
- Mínimo privilégio: só monte `workspace`, OAuth escopo mínimo, prefira contas de teste.
- Aprovação humana antes de enviar/publicar/comprar/alterar produção.
- Isolamento sandbox impede afetar outros sandboxes, mas não impede exfiltração via API autorizada.
- Segredos nunca no container; `.env` fora do git (`.gitignore` já cobre).

---

## 8. Planos e custos (referência out/2026, pode mudar)

- Free: US$0, 300 créditos/dia, 1 tarefa concorrente, 2 automações, 7 dias retenção sandbox.
- Pro: US$20/mês (4000 créd), US$40/mês (8000 créd, teste 7 dias).
- Team: US$20/assento/mês (créditos compartilhados).
- Consumo: tokens + VM + navegação + APIs; ex: 200 créd análise visual, 360 site, 900 app complexo.

Na réplica, custo = sua infra (Docker local = grátis, LLM local = grátis, Tavily 1k/mês grátis, SearXNG ilimitado).

---

## 9. Roadmap Landis (derivado de ai-manus + Manus 2.0)

- [x] Browser takeover, MCP
- [x] Multi-user, Docker Compose
- [x] Settings, Library, sharing
- [x] Native structured output, composable prompts, memory compaction
- [x] Bing/Google/Tavily/Serper/You.com search
- [x] **SearXNG/Exa/Firecrawl/Brave search (este commit)**
- [x] **Wide Research paralelo (este commit)**
- [x] **Cloud Computer scaffold (este commit)**
- [x] **Automations scaffold (este commit)**
- [ ] Deploy & Expose tools
- [ ] Windows & mobile access
- [ ] K8s/Docker Swarm
- [ ] Video Editor (FAL + timeline)
- [ ] Game Dev (multiplayer Cloud Computer)
- [ ] My Computer (CLI local com aprovação)

---

## 10. Como usar esta réplica agora

```bash
# 1. Clone
git clone https://github.com/afm04720-stack/ai-manus.git
cd ai-manus
git checkout arena/be0c3161-ai-manus

# 2. Configure LLM (exemplo Ollama local, recomendado grátis)
cp .env.example .env
# edite .env:
# MODEL_PROVIDER=ollama
# MODEL_NAME=qwen3-coder:30b
# API_BASE=http://host.docker.internal:11434/v1
# API_KEY=ollama
# SEARCH_PROVIDER=searxng
# SEARXNG_URL=http://searxng:8080

# 3. Busca grátis ilimitada (SearXNG)
docker run -d --name searxng -p 8080:8080 searxng/searxng

# 4. Sobe stack
./dev.sh up -d
# frontend 5173, backend 8000, sandbox 8080, VNC 5902, MongoDB 27017, Redis

# 5. Teste rápido
curl -X POST http://localhost:8000/api/v1/sessions -H "Content-Type: application/json" -d '{}'
# ou abra http://localhost:5173 → crie tarefa → veja plano + execução + arquivos
```

Para produção com LLM na nuvem (OpenRouter free):

```env
MODEL_PROVIDER=openai
MODEL_NAME=nvidia/nemotron-nano-9b-v2:free  # or qwen3:free
API_BASE=https://openrouter.ai/api/v1
API_KEY=sk-or-v1-...
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-...
```

---

## 11. APIs essenciais (Landis) — NÃO commitar chaves

O `objetivo.txt` lista chaves que **não devem ser commitadas**. Use `.env` local (fora do git):

```ini
# LLM
OPENROUTER_API_KEY=sk-or-v1-...
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIza...
NVIDIA_API_KEY=nvapi-...

# Search & scraping
TAVILY_API_KEY=tvly-...
EXA_API_KEY=...
FIRECRAWL_API_KEY=fc-...
BROWSERBASE_API_KEY=bb_live_...
BROWSERLESS_API_KEY=...
E2B_API_KEY=e2b_...

# Media
FAL_API_KEY=fal_...

# Cloud sandbox
DAYTONA_API_KEY=dtn_...

# Opcional
SEARXNG_URL=http://searxng:8080
```

> ⚠️ **Se você colou chaves reais no objetivo.txt, rotacione todas imediatamente** (revogue no dashboard do provedor e gere novas). Nunca commitar `.env`.

---

## 12. Referências

- Manus: welcome, tools, 2.0, Wide Research, Sandbox, Context Engineering, skills, integrações, modelos, preços, privacidade, Trust Center
- Reuters, TechCrunch, MIT Technology Review, CNBC, Dark Reading (prompt injection)
- OpenAI Agent, Deep Research, Gemini, Claude computer use, Devin, Cursor
- E2B How Manus uses E2B, kortix.com/docs/host, browser-use, SearXNG
- ai-manus docs, simpleyyt.com rebuild manus

---

**Landis AI é um tributo open-source. Não afiliado a Manus/Butterfly Effect/Meta. Use como assistente supervisionado, mínimo privilégio, revise toda saída antes de ação consequente.**
