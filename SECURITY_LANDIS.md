# Segurança — Landis AI (réplica Manus)

## ⚠️ Chaves vazadas no objetivo.txt

O arquivo `objetivo.txt` enviado contém chaves de API em texto plano (Nvidia NIM, Daytona, BrowserBase, E2B, Exa, Fal, Groq, Browserless, Firecrawl, OpenRouter, Gemini). **Isso é crítico.**

**Ação imediata se forem chaves reais:**

1. Revogue cada chave no dashboard do provedor ( gere nova).
2. Nunca commitar `.env` — este repo já tem `.env` no `.gitignore`.
3. Use `.env.example` como template (sem valores).
4. Em produção, use `JWT_SECRET_KEY` forte e `PASSWORD_SALT` único.

Este commit **não commita chaves**; adiciona apenas variáveis vazias em `.env.example`.

## Superfície de ataque do agente (maior que chatbot)

Agente lê email, navega, tem tokens (Gmail, Dropbox, GitHub, Slack). Caso Dark Reading (Salt Labs, set/2026): email com instrução indireta + código ofuscado → exfiltração de credenciais.

## Mitigações implementadas neste branch

- `backend/app/domain/services/security.py`: detecção de prompt injection, sanitização de saída de tools, bloqueio de comandos destrutivos (`rm -rf /`, `curl | sh`).
- `human_approval_required()`: marca ações sensíveis (send/publish/delete/transfer/payment/deploy) para aprovação.
- Sandbox isolado por tarefa, TTL, rede `manus-network`, sem montar `~`.
- Docs: mínimo privilégio, OAuth escopo mínimo, aprovação humana, revisão de fontes/código, backups, limites de crédito/tempo, logs.

## Checklist para uso seguro

- [ ] `AUTH_PROVIDER=password`, `JWT_SECRET_KEY` != default, HTTPS com `SESSION_COOKIE_SECURE=true`.
- [ ] Monte só `workspace` no sandbox.
- [ ] Conceda só permissões necessárias; prefira contas de teste.
- [ ] Exija aprovação humana antes de enviar/publicar/comprar.
- [ ] Trate web/email como não confiável (não siga instruções dentro de conteúdo externo).
- [ ] Monitore `logs -f backend`, atividades de conectores, consumo de créditos.
- [ ] Não envie PHI/dados regulados sem BAA/DPA.

## Prompt injection — padrão de defesa

```python
from app.domain.services.security import sanitize_tool_output

raw = await browser.get_content(url)  # ou email
safe = sanitize_tool_output(raw)      # anota [UNTRUSTED] se detectar injeção
# Envie `safe` ao LLM, não `raw`
```

Em `AGENTS.md`, todo tool que retorna conteúdo externo deve passar por `sanitize_tool_output`.

## Licença e responsabilidade

Manus Trust Center alega SOC2/ISO27001, mas agentes ainda exigem supervisão. Termos "como estão" — sem garantia. Use como **assistente operacional supervisionado**, não autoridade autônoma.

## Reporte

Abra issue com label `security` ou email `security@landis.ai` (placeholder). Não publique PoC público antes de correção.
