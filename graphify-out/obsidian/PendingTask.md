---
source_file: "skills\context-agent\scripts\models.py"
type: "code"
community: "Community 20"
location: "L27"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Community_20
---

# PendingTask

## Connections
- [[Carrega o contexto ativo do arquivo markdown.]] - `uses` [INFERRED]
- [[Copia ACTIVE_CONTEXT.md para MEMORY.md no diretório de auto-memory do Claude.]] - `uses` [INFERRED]
- [[Encontra decisões nas mensagens.]] - `uses` [INFERRED]
- [[Encontra erros e suas soluções.]] - `uses` [INFERRED]
- [[Encontra tarefas concluídas.]] - `uses` [INFERRED]
- [[Encontra tarefas pendentes. Foca em checkboxes não marcados nas mensagens do use]] - `uses` [INFERRED]
- [[Extrai descobertasfindings importantes.]] - `uses` [INFERRED]
- [[Gera um resumo estruturado a partir das entradas da sessão.]] - `uses` [INFERRED]
- [[Gerador de resumos estruturados de sessão. Analisa mensagens e gera session-NNN]] - `uses` [INFERRED]
- [[Gerencia o ACTIVE_CONTEXT.md — arquivo que é sincronizado com MEMORY.md. Limite]] - `uses` [INFERRED]
- [[Identifica tópicos principais das mensagens do usuário.]] - `uses` [INFERRED]
- [[Merge uma nova sessão no contexto ativo.]] - `uses` [INFERRED]
- [[Retorna o próximo número de sessão disponível.]] - `uses` [INFERRED]
- [[Salva ACTIVE_CONTEXT.md respeitando limite de linhas.]] - `uses` [INFERRED]
- [[Salva resumo como arquivo markdown.]] - `uses` [INFERRED]
- [[Tarefa pendente identificada em uma sessão.]] - `rationale_for` [EXTRACTED]
- [[Verifica se ACTIVE_CONTEXT.md e MEMORY.md estão sincronizados.]] - `uses` [INFERRED]
- [[_extract_pending_tasks()]] - `calls` [INFERRED]
- [[load_active_context()]] - `calls` [INFERRED]
- [[models.py]] - `contains` [EXTRACTED]
- [[update_active_context()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/Community_20