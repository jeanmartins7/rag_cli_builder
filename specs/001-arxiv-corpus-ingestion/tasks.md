---
description: "Tarefas de execução — pipeline RAG retrieval (entrega 2026-06-19)"
---

# Tasks: Sistema de Recuperação de Artigos Científicos

**Input**: `specs/001-arxiv-corpus-ingestion/` (spec.md, plan.md, research.md, data-model.md, contracts/)

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Constitution**: `.specify/memory/constitution.md` v1.1.0

**Prazo de entrega**: 2026-06-19 23:59 (AVA)

**Organization**: Fases cronológicas com dependências explícitas; MVP = Fase 1 concluída.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Paralelizável (arquivos distintos, sem dependência de tarefas incompletas)
- **[US1] / [US2]**: User stories da spec de ingestão (demais fases sem label de story)

---

## Phase 0: Setup do Projeto

**Purpose**: Estrutura modular, dependências e artefatos de avaliação antes da fundação de dados.

**Depends on**: nada

**Blocks**: Fase 1

- [X] T001 Create modular directory structure (src/collection/, src/preprocessing/, src/retrievers/, src/evaluation/, src/modules/, data/, notebooks/, eval/) per plan.md
- [X] T002 Update requirements.txt with arxiv, tqdm, pandas, numpy, scikit-learn, rank_bm25 and approved retrieval deps
- [X] T003 [P] Add data/*.jsonl and data/.collection_checkpoint.json to .gitignore
- [X] T004 [P] Copy eval/evaluate.py and query/qrels templates from resource/material_de_apoio/eval/ to eval/

**Checkpoint**: Ambiente instalável via `pip install -r requirements.txt`

---

## Phase 1: Fundação de Dados (Passos 1 e 2)

**Purpose**: Coletar corpus ArXiv sobre poda estrutural/compressão de LLMs (2023–2026) e implementar pré-processamento reutilizável.

**Depends on**: Phase 0

**Blocks**: Fase 2 (recuperadores precisam de corpus + preprocessing)

### User Story 1 — Coleta (Priority P1)

**Goal**: `data/corpus.jsonl` com 1k–5k artigos únicos, schema TREC-ready.

**Independent Test**: Executar notebook de coleta; validar schema, volume e zero duplicatas por id/DOI.

- [X] T005 Implement CollectionConfig dataclass with validate() in src/collection/config.py
- [X] T006 [P] Implement build_arxiv_query() in src/collection/query_builder.py
- [X] T007 Implement fetch_arxiv_raw() with retry/backoff and incremental save in src/collection/fetcher.py
- [X] T008 Implement normalize_corpus() with id/DOI dedup in src/collection/normalizer.py
- [X] T009 [US1] Create notebooks/01_coleta_arxiv.ipynb adapted from resource/coleta_arxiv.ipynb calling src/collection/
- [X] T010 [US1] Configure collection params in notebooks/01_coleta_arxiv.ipynb (theme LLM pruning, 2023–2026, cs.CL/cs.LG/cs.AI, TARGET_SIZE=2000, OR keywords per spec FR-003)
- [ ] T011 [US1] Execute notebooks/01_coleta_arxiv.ipynb to generate data/corpus.jsonl (Tarefa 1.1 — coleta e corpus)
- [ ] T012 [US1] Validate data/corpus.jsonl against specs/001-arxiv-corpus-ingestion/contracts/corpus-record.schema.json per quickstart.md §4

### User Story 2 — Pré-processamento (Priority P2)

**Goal**: Pipeline determinístico título+abstract → tokens (lower-case, sem pontuação, sem stopwords).

**Independent Test**: Processar 10 artigos + 1 query; mesma configuração → mesma saída.

- [X] T013 Implement PreprocessConfig frozen dataclass in src/preprocessing/config.py
- [X] T014 [US2] Implement build_indexable_text() with tokenization, lower-casing, punctuation removal, stopword removal in src/preprocessing/pipeline.py (Tarefa 1.2)
- [X] T015 [US2] Implement preprocess_query() and preprocess_document() in src/preprocessing/pipeline.py
- [X] T016 [US2] Add optional use_stemming branch (nltk SnowballStemmer) in src/preprocessing/pipeline.py
- [X] T017 [US2] Add preprocessing demo cells to notebooks/01_coleta_arxiv.ipynb for one document and one sample query

**Checkpoint Fase 1**: `data/corpus.jsonl` válido + `src/preprocessing/pipeline.py` importável pelos recuperadores.

---

## Phase 2: Recuperadores Baseline (Passos 3 e 4)

**Purpose**: BM25 esparso e KNN/denso em paralelo, runs TREC independentes.

**Depends on**: Phase 1 (corpus.jsonl + preprocessing)

**Blocks**: Fase 3 (avaliação precisa de runs)

- [X] T018 Implement BM25Retriever (k1, b documented) on title+abstract via preprocessing in src/retrievers/bm25.py
- [X] T019 Create notebooks/02_baseline_bm25.ipynb adapted from resource/material_de_apoio/baseline_bm25.ipynb using src/retrievers/bm25.py
- [ ] T020 Generate eval/runs/bm25.trec in TREC format (qid Q0 doc_id rank score system) via notebooks/02_baseline_bm25.ipynb
- [X] T021 [P] Implement DenseRetriever with TF-IDF and vectorized cosine KNN in src/retrievers/dense.py
- [X] T022 Create notebooks/03_retrieval_knn.ipynb orchestrating src/retrievers/dense.py
- [ ] T023 Generate eval/runs/knn.trec in TREC format via notebooks/03_retrieval_knn.ipynb

**Checkpoint Fase 2**: Dois arquivos `.trec` independentes para o mesmo conjunto de queries de teste.

---

## Phase 3: Avaliação Experimental (Passo 5)

**Purpose**: Queries, qrels via pooling, métricas IR e análise qualitativa.

**Depends on**: Phase 2 (runs BM25 + KNN)

**Blocks**: Fase 4 (módulo opcional compara contra baselines)

- [ ] T024 Create 10–20 focused test queries in eval/queries.tsv (distinct from collection query; LLM pruning subtopics)
- [ ] T025 Pool top-10/20 from eval/runs/bm25.trec and eval/runs/knn.trec; manually annotate eval/qrels.tsv (TREC format)
- [ ] T026 Run python eval/evaluate.py --qrels eval/qrels.tsv --runs eval/runs/bm25.trec eval/runs/knn.trec --k 10
- [ ] T027 Document P@10, R@10, MAP, nDCG@10 comparison table in relatorio/ or eval/metrics_summary.md
- [ ] T028 Write qualitative analysis (≥2 queries: hits and failures) in relatorio/sections/avaliacao.tex or eval/qualitative.md

**Checkpoint Fase 3**: Métricas reportáveis + qrels reproduzíveis.

---

## Phase 4: Módulo de Aprofundamento (Passo 6)

**Purpose**: 1 módulo (Mestrado) ou 2 módulos (Doutorado, incluindo M1 ou M5) acoplável aos runs base.

**Depends on**: Phase 3 (qrels + baselines avaliados)

**Blocks**: Fase 5 (relatório final com resultados do módulo)

- [ ] T029 Select enhancement module(s) M1–M5 per degree level and document choice in README.md
- [ ] T030 Implement chosen module as loose-coupled component in src/modules/ consuming TREC runs
- [ ] T031 Generate new eval/runs/<module>.trec and re-run eval/evaluate.py against baselines
- [ ] T032 Document module impact and discipline connection (e.g., M1↔classificação) in relatorio/sections/metodologia.tex

**Checkpoint Fase 4**: Novo run avaliado e comparado com BM25/KNN.

---

## Phase 5: Entregáveis e Submissão

**Purpose**: Reprodutibilidade, relatório SBC, demo, vídeo e empacotamento AVA.

**Depends on**: Phase 3 mínimo; Phase 4 se módulo obrigatório

**Deadline**: 2026-06-19 23:59

- [X] T033 Create scripts/search.py demo (query text in → ranked articles out) using src/retrievers/ and src/preprocessing/
- [X] T034 Update README.md with deterministic reproduction steps, collection decisions, and GenAI declaration if applicable
- [ ] T035 Write relatorio/relatorio.tex in SBC format (≤10 pages: intro, related, methodology, evaluation, results, conclusion)
- [ ] T036 Record ≤8 min presentation video; add URL to relatorio/ footnote and LINKS.txt
- [ ] T037 Package submission .zip (PDF, code, eval/, README.md, requirements.txt, LINKS.txt) for AVA upload

**Checkpoint Final**: Critérios C1–C10 do enunciado atendidos.

---

## Dependencies & Execution Order

```text
Phase 0 (Setup)
    │
    ▼
Phase 1 (Fundação de Dados) ── T005–T012 [US1] ── T013–T017 [US2]
    │
    ▼
Phase 2 (BM25 ∥ KNN) ── T018–T020 BM25 ── T021–T023 KNN (paralelo após T018)
    │
    ▼
Phase 3 (Avaliação) ── T024 queries → T025 qrels → T026–T028 métricas
    │
    ▼
Phase 4 (Módulo opcional) ── T029–T032
    │
    ▼
Phase 5 (Entregáveis) ── T033–T037
```

### Critical path

`T001 → T011 (corpus.jsonl) → T014 (preprocessing) → T020+T023 (runs) → T025 (qrels) → T026 (métricas) → T035 (relatório) → T037 (zip)`

### Story completion order

| Story | Phase | Depends on |
|-------|-------|------------|
| US1 Coleta | 1 | Phase 0 |
| US2 Pré-processamento | 1 | T011 (corpus exists) |
| Baselines | 2 | US1 + US2 |
| Avaliação | 3 | Baselines |
| Módulo | 4 | Avaliação |
| Entrega | 5 | Avaliação (+ Módulo se aplicável) |

---

## Parallel Execution Examples

### Within Phase 1 (after T008)

```bash
# Parallel: query builder already done; while collection runs, start preprocessing scaffold
Task T013: src/preprocessing/config.py
Task T006: src/collection/query_builder.py  # if not done
```

### Within Phase 2 (after T018)

```bash
# BM25 and KNN in parallel (different files)
Task T019–T020: notebooks/02_baseline_bm25.ipynb + eval/runs/bm25.trec
Task T021–T023: src/retrievers/dense.py + notebooks/03_retrieval_knn.ipynb
```

### Within Phase 5

```bash
# Report writing parallel to demo polish
Task T033: scripts/search.py
Task T034: README.md
Task T035: relatorio/relatorio.tex  # start during Phase 3 evaluation
```

---

## Implementation Strategy

### MVP (Week 1 target)

1. Complete Phase 0 + Phase 1 (T001–T017)
2. **Stop and validate**: `corpus.jsonl` + preprocessing pipeline per quickstart.md
3. Demo: one query preprocessed end-to-end

### Incremental delivery

| Increment | Delivers | Validates |
|-----------|----------|-----------|
| MVP | Fase 1 | SC-001–SC-006 (ingestão) |
| +Fase 2 | BM25 + KNN runs | Constitution Princípio II |
| +Fase 3 | Métricas + qrels | Critério C6 |
| +Fase 4 | Módulo M1–M5 | Critério C5 |
| +Fase 5 | Entrega AVA | Critérios C8–C10 |

### Risk mitigations

| Risk | Mitigation task |
|------|-----------------|
| ArXiv API 429/503 | T007 retry/backoff; re-run T011 |
| Corpus < 1000 docs | Broaden keywords in T010; document in relatório |
| Coleta lenta | Run T011 overnight; incremental checkpoint |
| Pouco tempo até 19/06 | Priorizar MVP → Fase 2 → Fase 3; Fase 4 se Mestrado (1 módulo) |

---

## Task Summary

| Phase | Tasks | Parallel opportunities |
|-------|-------|------------------------|
| 0 Setup | T001–T004 (4) | T003, T004 |
| 1 Fundação de Dados | T005–T017 (13) | T006; T013 after T011 |
| 2 Recuperadores | T018–T023 (6) | T021–T023 after T018 |
| 3 Avaliação | T024–T028 (5) | T027–T028 during report draft |
| 4 Módulo | T029–T032 (4) | — |
| 5 Entregáveis | T033–T037 (5) | T033–T035 |
| **Total** | **37** | **8 tasks marked [P]** |

### MVP scope

**T001–T017** (Phase 0 + Phase 1) — entrega Tarefas 1.1 e 1.2 do usuário:
- **T011** = Tarefa 1.1 (coleta → `corpus.jsonl`)
- **T014** = Tarefa 1.2 (pré-processamento título+abstract)

### Independent test criteria

| Story | Test |
|-------|------|
| US1 | `corpus.jsonl` validado por quickstart §4; zero duplicatas |
| US2 | 10 docs + 1 query → tokens determinísticos; stemming off por padrão |
| Fase 2 | `bm25.trec` e `knn.trec` existem para mesmas qids |
| Fase 3 | `evaluate.py` imprime MAP para ambos os sistemas |
| Fase 5 | README reproduz coleta + uma busca de exemplo |
