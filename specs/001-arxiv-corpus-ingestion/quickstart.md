# Quickstart: Ingestão de Corpus ArXiv

**Feature**: 001-arxiv-corpus-ingestion  
**Prerequisites**: Python 3.11+, conexão com internet (API ArXiv)

## 1. Ambiente

```bash
cd /home/jeanverso/git/rag_cli_builder
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Parâmetros de coleta (tema: poda estrutural LLM)

| Parâmetro | Valor |
|-----------|-------|
| Anos | 2023 – 2026 |
| Categorias | cs.CL, cs.LG, cs.AI |
| Volume alvo | 2000 (ajustável 1000–5000) |
| Saída | `data/corpus.jsonl` |

Keywords OR (mínimo):
`structural pruning`, `LLM compression`, `attention heads pruning`, `MLP pruning`,
`parameter efficient fine-tuning`

## 3. Executar coleta

```bash
jupyter notebook notebooks/01_coleta_arxiv.ipynb
```

Ou, após implementação dos módulos `src/`:

```bash
python -c "
from pathlib import Path
from src.collection.config import CollectionConfig
from src.collection.fetcher import fetch_arxiv_raw
from src.collection.normalizer import normalize_corpus

config = CollectionConfig(
    theme='Structural pruning and LLM compression during fine-tuning',
    keywords=[
        'structural pruning', 'LLM compression', 'attention heads pruning',
        'MLP pruning', 'parameter efficient fine-tuning',
    ],
    categories=['cs.CL', 'cs.LG', 'cs.AI'],
    year_from=2023,
    year_to=2026,
    target_count=2000,
)
config.validate()
n_raw = fetch_arxiv_raw(config)
n_corpus = normalize_corpus(config)
print(f'Raw ids: {n_raw}, Corpus docs: {n_corpus}')
"
```

**Retomada**: Se a coleta falhar (HTTP 429/503), reexecute o mesmo comando/célula;
progresso em `data/arxiv_raw.jsonl` e checkpoint é preservado.

## 4. Verificar corpus

```bash
python -c "
import json
from pathlib import Path
path = Path('data/corpus.jsonl')
lines = path.read_text().strip().splitlines()
assert 1000 <= len(lines) <= 5000 or len(lines) > 0, 'ajuste target_count'
sample = json.loads(lines[0])
for key in ('id','title','abstract','authors','categories','date'):
    assert key in sample, f'missing {key}'
print(f'OK: {len(lines)} documents, sample id={sample[\"id\"]}')
"
```

## 5. Testar pré-processamento

```bash
python -c "
from src.preprocessing.config import PreprocessConfig
from src.preprocessing.pipeline import preprocess_query, build_indexable_text

cfg = PreprocessConfig(use_stemming=False)
tokens = preprocess_query(
    'structural pruning of attention heads in large language models', cfg
)
print('Query tokens:', tokens[:15])

doc_tokens = build_indexable_text(
    'AMP: Attention and MLP Pruning',
    'We propose structural pruning during fine-tuning of open-source LLMs.',
    cfg,
)
print('Doc tokens:', doc_tokens[:15])
"
```

## 6. Artefatos esperados

| Arquivo | Descrição |
|---------|-----------|
| `data/arxiv_raw.jsonl` | Coleta bruta incremental |
| `data/corpus.jsonl` | Corpus normalizado (schema spec) |
| `data/.collection_checkpoint.json` | Estado de retomada |

## Troubleshooting

- **HTTP 429/503**: aguardar 15–30 min; reduzir `page_size` para 25.
- **Volume < alvo**: API esgotou resultados — documentar no relatório; ampliar keywords.
- **Duplicatas**: rerodar `normalize_corpus`; dedup é idempotente.
