# Implementation Plan: Ingestão de Corpus ArXiv

**Branch**: `feat/tema-pesquisa` | **Date**: 2026-06-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-arxiv-corpus-ingestion/spec.md`

## Summary

Implementar as etapas de ingestão (Passo 1 e 2) do pipeline RAG: coleta tolerante
a falhas de artigos do ArXiv sobre poda estrutural e compressão de LLMs open source
(2023–2026, categorias cs.CL/cs.LG/cs.AI), geração de `data/corpus.jsonl` com schema
normalizado, e módulo de pré-processamento reutilizável (título + abstract → tokens
normalizados). Lógica reutilizável em `src/collection/` e `src/preprocessing/`;
notebook `notebooks/01_coleta_arxiv.ipynb` orquestra a coleta chamando esses módulos.

## Technical Context

**Language/Version**: Python 3.11+ com type hints (PEP 484) em funções públicas

**Primary Dependencies**:
- Coleta: `arxiv`, `pandas`, `tqdm` (material de apoio; ver Complexity Tracking)
- Pré-processamento: `scikit-learn` (stopwords), `numpy`, `re` (stdlib)
- Stemming opcional: `nltk` somente quando `use_stemming=True` (justificado)

**Storage**: `data/arxiv_raw.jsonl` (bruto incremental), `data/corpus.jsonl` (normalizado),
`data/.collection_checkpoint.json` (offset/ids para retomada)

**Testing**: Validação manual via sanity checks no notebook + script de verificação de
schema; testes unitários opcionais em `tests/unit/test_preprocessing.py`

**Target Platform**: Linux/macOS, virtualenv local, Jupyter para orquestração

**Project Type**: Módulos Python (`src/`) + notebook fino de orquestração

**Performance Goals**: Coleta incremental sem recarregar corpus inteiro; pré-processamento
em lote com list comprehension / vetorização onde aplicável (não crítico para 2k docs)

**Constraints**: Sem APIs RAG comerciais; corpus 1k–5k; dedup por id/DOI; mesmo pipeline
para documentos e queries

**Scale/Scope**: ~2.000 artigos padrão; 6 campos obrigatórios por documento; 4 etapas de
pré-processamento

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Reference: `.specify/memory/constitution.md` v1.1.0

| Principle | Gate | Status |
|-----------|------|--------|
| I. Arquitetura Modular | `src/collection/` e `src/preprocessing/` isolados; notebook só orquestra | ✅ PASS |
| II. Performance e Qualidade | Type hints + docstrings; tokenização eficiente; sem loops desnecessários | ✅ PASS |
| III. Restrições e Dependências | Sem RAG comercial; deps extras justificadas (arxiv, tqdm, nltk opcional) | ✅ PASS* |
| IV. Padrões de Dados | `corpus.jsonl` schema fixo; reprodutibilidade via README/quickstart | ✅ PASS** |
| Escopo Acadêmico | Corpus 1k–5k alinhado ao tema; queries/qrels fora desta feature | ✅ PASS*** |

\* Ver Complexity Tracking para `arxiv`, `tqdm`, `nltk` (stemming opcional).  
\** Runs TREC fora de escopo desta feature (etapa de recuperação).  
\*** Avaliação com queries/qrels será feature separada.

**Violations requiring Complexity Tracking justification**: `arxiv`, `tqdm`; `nltk` apenas
se stemming habilitado (ver tabela abaixo).

## Project Structure

### Documentation (this feature)

```text
specs/001-arxiv-corpus-ingestion/
├── plan.md              # Este arquivo
├── research.md          # Decisões técnicas (Phase 0)
├── data-model.md        # Entidades e validação (Phase 1)
├── quickstart.md        # Reprodução determinística (Phase 1)
├── contracts/           # Schemas e interfaces (Phase 1)
└── tasks.md             # Gerado por /speckit-tasks
```

### Source Code (repository root)

```text
data/
├── arxiv_raw.jsonl          # append-only durante coleta
├── corpus.jsonl             # saída normalizada (schema spec)
└── .collection_checkpoint.json
src/
├── collection/
│   ├── __init__.py
│   ├── config.py            # CollectionConfig dataclass
│   ├── query_builder.py     # build ArXiv query string
│   ├── fetcher.py           # paginação, retry, incremental save
│   └── normalizer.py        # raw → corpus.jsonl, dedup id/DOI
├── preprocessing/
│   ├── __init__.py
│   ├── config.py            # PreprocessConfig (stemming flag, separator)
│   └── pipeline.py          # preprocess_document(), preprocess_query()
notebooks/
└── 01_coleta_arxiv.ipynb    # orquestra collection + sanity checks
resource/
└── coleta_arxiv.ipynb       # referência original (material de apoio)
```

**Structure Decision**: Toda lógica de coleta e pré-processamento vive em `src/`;
o notebook importa módulos e expõe parâmetros do tema (keywords, anos, TARGET_SIZE).
Isso satisfaz Princípio I e permite que recuperadores importem `preprocessing` sem
depender do notebook.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `arxiv` | Wrapper oficial usado no material de apoio; paginação e rate limit | HTTP raw exige reimplementar retry/offset |
| `tqdm` | Feedback de progresso em coletas longas (horas) | Print manual não escala para 2k+ artigos |
| `nltk` (opcional) | SnowballStemmer para comparação com/sem stemming no relatório | Stemmer caseiro menos defensável academicamente |

## Phase 0 Output

→ [research.md](./research.md) — decisões resolvidas, sem NEEDS CLARIFICATION pendentes.

## Phase 1 Output

→ [data-model.md](./data-model.md)  
→ [contracts/](./contracts/)  
→ [quickstart.md](./quickstart.md)

## Post-Design Constitution Re-check

| Principle | Post-design status |
|-----------|-------------------|
| I. Arquitetura Modular | ✅ Interfaces `CollectionConfig`, `fetch_corpus()`, `preprocess_text()` desacopladas |
| II. Performance e Qualidade | ✅ `PreprocessConfig` frozen dataclass; funções tipadas documentadas em contracts |
| III. Restrições | ✅ Deps extras documentadas; lógica de query e tokenização visível em src/ |
| IV. Padrões de Dados | ✅ JSON Schema em contracts/corpus-record.schema.json |
