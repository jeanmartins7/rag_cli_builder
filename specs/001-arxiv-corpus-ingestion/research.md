# Research: Ingestão de Corpus ArXiv

**Feature**: 001-arxiv-corpus-ingestion  
**Date**: 2026-06-06

## R1 — Cliente da API do ArXiv

**Decision**: Usar biblioteca `arxiv` (PyPI) com `Client(page_size=50, delay_seconds=5,
num_retries=8)` e loop externo de backoff exponencial (60s → 600s).

**Rationale**: Material de apoio (`resource/coleta_arxiv.ipynb`) já valida este padrão
contra HTTP 429/503. Retomada por `offset` e append em `arxiv_raw.jsonl` atendem FR-007.

**Alternatives considered**:
- `urllib` / `requests` direto — mais controle, mas reimplementa paginação e retries.
- Semantic Scholar / OpenAlex — válidos pelo enunciado, mas spec fixa ArXiv para esta feature.

## R2 — Montagem da query de coleta

**Decision**: Query ArXiv com `(all:"kw1" OR all:"kw2" OR ...) AND (cat:cs.CL OR cat:cs.LG OR cat:cs.AI)`,
filtragem adicional de ano no cliente Python (`YEAR_FROM=2023`, `YEAR_TO=2026`).

**Rationale**: Sintaxe `all:` busca título+abstract; filtro de ano no cliente evita query
excessivamente longa que aumenta falhas 503.

**Keywords mínimas** (FR-003):
`structural pruning`, `LLM compression`, `attention heads pruning`, `MLP pruning`,
`parameter efficient fine-tuning`

**Alternatives considered**:
- Filtro `submittedDate` na query — sintaxe mais frágil; filtro local é mais legível.

## R3 — Schema de `corpus.jsonl`

**Decision**: Normalizar campos do notebook bruto para o schema da spec:

| Campo spec | Origem ArXiv | Regra |
|------------|--------------|-------|
| `id` | `arxiv_id` | Sem sufixo de versão (`2401.12345v2` → `2401.12345`) |
| `title` | `title` | strip, não vazio |
| `abstract` | `summary` | strip, mín. 50 chars |
| `authors` | `authors` | `list[str]` |
| `categories` | `categories` | `list[str]` |
| `date` | `published` | ISO `YYYY-MM-DD` |

**Rationale**: FR-009/FR-010 exigem chaves em inglês alinhadas ao enunciado; notebook usa
`arxiv_id`/`published` no bruto.

**Alternatives considered**:
- Manter `arxiv_id` no corpus — rejeitado por conflito com FR-009.

## R4 — Deduplicação

**Decision**: Deduplicar por `id` (arxiv_id normalizado); secundariamente por `doi` quando
presente. Manter registro com `updated` mais recente.

**Rationale**: FR-006; notebook já deduplica por arxiv_id.

## R5 — Tokenização e normalização

**Decision**:
1. Concatenar `title + ". " + abstract` (separador documentado em `PreprocessConfig`)
2. Tokenizar com `re.findall(r"[a-z0-9]+", text.lower())` após lower-case
3. Remover pontuação implicitamente via regex alfanumérica
4. Remover stopwords via `sklearn.feature_extraction.text.ENGLISH_STOP_WORDS`

**Rationale**: Atende FR-012/FR-013 sem `nltk` obrigatório; sklearn está na lista aprovada.

**Alternatives considered**:
- `nltk.word_tokenize` — dependência extra para caminho padrão.
- `spacy` — fora do conjunto aprovado.

## R6 — Stemming opcional

**Decision**: `PreprocessConfig.use_stemming: bool = False`. Quando `True`, aplicar
`nltk.stem.SnowballStemmer("english")` após remoção de stopwords.

**Rationale**: FR-014 exige modularidade; comparação com/sem stemming é experimento de
relatório, não caminho padrão.

**Alternatives considered**:
- Stemmer regex simples — sem custo de dep, mas menos rigoroso para discussão acadêmica.

## R7 — Checkpoint e retomada

**Decision**: Persistir `data/.collection_checkpoint.json` com `{ "offset": int, "seen_ids": [...] }`
além do append em `arxiv_raw.jsonl`.

**Rationale**: Dupla redundância: raw file permite reconstruir ids; checkpoint acelera retomada.

## R8 — Volume alvo e validação

**Decision**: `TARGET_SIZE=2000` padrão; validar `1000 <= target <= 5000` em `CollectionConfig`.

**Rationale**: FR-005; falha rápida em configuração inválida.

## Resolved Clarifications

Nenhum `NEEDS CLARIFICATION` pendente — spec e defaults cobrem todas as decisões.
