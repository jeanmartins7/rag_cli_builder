# Data Model: Ingestão de Corpus ArXiv

**Feature**: 001-arxiv-corpus-ingestion  
**Date**: 2026-06-06

## Entity Relationship Overview

```text
CollectionConfig ──► ArxivFetcher ──► RawArticle (arxiv_raw.jsonl)
                                           │
                                           ▼
                                    CorpusNormalizer ──► CorpusArticle (corpus.jsonl)
                                           │
                                           ▼
                              PreprocessConfig ──► IndexableText (tokens)
```

## Entities

### CollectionConfig

Configuração imutável da coleta (Passo 1).

| Field | Type | Validation | Default |
|-------|------|------------|---------|
| `theme` | str | não vazio | tema poda estrutural LLM |
| `keywords` | list[str] | ≥1 termo; inclui FR-003 mínimos | ver research.md R2 |
| `categories` | list[str] | subset de cs.CL, cs.LG, cs.AI | `["cs.CL","cs.LG","cs.AI"]` |
| `year_from` | int | 2023 | 2023 |
| `year_to` | int | 2026, ≥ year_from | 2026 |
| `target_count` | int | 1000 ≤ n ≤ 5000 | 2000 |
| `page_size` | int | 25–100 | 50 |
| `raw_path` | Path | gravável | `data/arxiv_raw.jsonl` |
| `corpus_path` | Path | gravável | `data/corpus.jsonl` |
| `checkpoint_path` | Path | gravável | `data/.collection_checkpoint.json` |

### RawArticle (arxiv_raw.jsonl)

Registro append-only durante coleta. Superset dos campos do wrapper `arxiv`.

| Field | Type | Notes |
|-------|------|-------|
| `arxiv_id` | str | ID curto sem versão |
| `title` | str | |
| `abstract` | str | de `summary` |
| `authors` | list[str] | |
| `categories` | list[str] | |
| `published` | str | ISO datetime |
| `updated` | str | usado na dedup |
| `doi` | str \| null | dedup secundária |

### CorpusArticle (corpus.jsonl)

Documento normalizado — **uma linha JSON por artigo**.

| Field | Type | Validation |
|-------|------|------------|
| `id` | str | regex `^\d{4}\.\d{4,5}$` (ArXiv id) |
| `title` | str | len > 0 |
| `abstract` | str | len ≥ 50 |
| `authors` | list[str] | len ≥ 1 |
| `categories` | list[str] | len ≥ 1; valores prefixo `cs.` |
| `date` | str | ISO date `YYYY-MM-DD` |

**Uniqueness**: `id` único no arquivo; `doi` único quando não null.

### CollectionCheckpoint

| Field | Type | Purpose |
|-------|------|---------|
| `offset` | int | último offset consumido da API |
| `seen_ids` | list[str] | ids já persistidos |
| `query_hash` | str | detecta mudança de parâmetros |

**State transition**: Se `query_hash` mudar, operador MUST confirmar antes de sobrescrever.

### PreprocessConfig

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `title_abstract_separator` | str | `". "` | FR-012 |
| `use_stemming` | bool | `False` | FR-014 |
| `min_token_length` | int | `2` | remove tokens curtos |
| `language` | str | `"english"` | stopwords sklearn |

### IndexableText

Saída do pré-processamento (não persistida por padrão; gerada on-demand).

| Field | Type | Description |
|-------|------|-------------|
| `doc_id` | str \| null | null para queries |
| `tokens` | list[str] | tokens pós pipeline |
| `text_normalized` | str | `" ".join(tokens)` para BM25/TF-IDF |

## Validation Rules Summary

1. Rejeitar artigos sem `title` ou com `abstract` < 50 chars na normalização.
2. `target_count` fora de [1000, 5000] → erro de configuração.
3. `corpus.jsonl` pós-normalização: zero duplicatas por `id` ou `doi`.
4. Pré-processamento: mesma `PreprocessConfig` para documento e query (FR-015).

## Quality Metrics (sanity checks)

| Metric | Expected |
|--------|----------|
| Document count | `target_count` ± tolerância se API esgotada |
| Empty abstract rate | 0% no corpus final |
| Category coverage | ≥90% registros com interseção cs.CL/LG/AI |
| Year distribution | maioria em 2023–2026 |
