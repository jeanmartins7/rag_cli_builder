# RAG CLI Builder

Sistema de recuperação de artigos científicos — o componente **"R"** (Retrieval) de um
pipeline RAG — desenvolvido como Trabalho Prático de Inteligência Artificial (FACOM/UFMS,
2026/1).

## Visão geral

Pipeline modular de Information Retrieval sobre coleção ArXiv: coleta, pré-processamento,
dois recuperadores paralelos (BM25 esparso + KNN/denso), avaliação TREC (P@k, R@k, MAP,
nDCG) e módulos opcionais acopláveis.

## Arquitetura

```
src/collection/ → src/preprocessing/ → src/retrievers/ (bm25 ∥ dense) → eval/runs/*.trec
                                              ↓
                                    src/modules/ (opcional, acoplável)
                                              ↓
                                    src/evaluation/ → métricas IR
```

## Governança

Princípios de arquitetura modular, performance, dependências enxutas e padrões TREC:
[constituição do projeto](.specify/memory/constitution.md) (v1.1.0).

## Materiais de apoio

Notebooks e templates iniciais estão em `resource/`:

- `resource/coleta_arxiv.ipynb` — coleta via API do ArXiv
- `resource/material_de_apoio/baseline_bm25.ipynb` — baseline BM25
- `resource/material_de_apoio/eval/` — evaluate.py, queries e qrels de exemplo
- `resource/material_de_apoio/skeleton/` — estrutura sugerida do repositório

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Reprodução determinística

### 1. Coleta do corpus (Tarefa 1.1)

```bash
# Coleta real via API ArXiv (~horas; retomável)
python scripts/collect_corpus.py --target 2000

# Ou via notebook
jupyter notebook notebooks/01_coleta_arxiv.ipynb
```

### 2. Validação do corpus

```bash
python scripts/validate_corpus.py
```

### 3. Pré-processamento (Tarefa 1.2)

```python
from src.preprocessing.config import PreprocessConfig
from src.preprocessing.pipeline import preprocess_query
cfg = PreprocessConfig(use_stemming=False)
print(preprocess_query("structural pruning of attention heads", cfg))
```

### 4. Recuperação e runs TREC

```bash
jupyter notebook notebooks/02_baseline_bm25.ipynb
jupyter notebook notebooks/03_retrieval_knn.ipynb
```

### 5. Busca interativa (demo)

```bash
python scripts/search.py "structural pruning of attention heads" --method bm25
```

### Corpus de desenvolvimento

Se a API ArXiv estiver indisponível, gere um corpus mínimo para smoke tests:

```bash
python scripts/generate_dev_corpus.py
```

Substitua por coleta real antes da entrega.

## Especificação e tarefas

- [spec.md](specs/001-arxiv-corpus-ingestion/spec.md)
- [plan.md](specs/001-arxiv-corpus-ingestion/plan.md)
- [tasks.md](specs/001-arxiv-corpus-ingestion/tasks.md)
- [quickstart.md](specs/001-arxiv-corpus-ingestion/quickstart.md)
