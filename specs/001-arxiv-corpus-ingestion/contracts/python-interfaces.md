# Python Module Contracts: Ingestão

**Feature**: 001-arxiv-corpus-ingestion

Interfaces públicas que recuperadores e notebooks MUST consumir.

## `src.collection.config`

```python
@dataclass(frozen=True)
class CollectionConfig:
    theme: str
    keywords: list[str]
    categories: list[str]
    year_from: int
    year_to: int
    target_count: int
    page_size: int = 50
    raw_path: Path = Path("data/arxiv_raw.jsonl")
    corpus_path: Path = Path("data/corpus.jsonl")
    checkpoint_path: Path = Path("data/.collection_checkpoint.json")

    def validate(self) -> None: ...
```

## `src.collection.query_builder`

```python
def build_arxiv_query(keywords: list[str], categories: list[str]) -> str:
    """Retorna query ArXiv: (all:"kw1" OR ...) AND (cat:cs.CL OR ...)."""
```

## `src.collection.fetcher`

```python
def fetch_arxiv_raw(config: CollectionConfig) -> int:
    """
    Coleta incremental com retry/backoff. Append em config.raw_path.
    Atualiza config.checkpoint_path. Retorna total de ids únicos.
    """
```

## `src.collection.normalizer`

```python
def normalize_corpus(config: CollectionConfig) -> int:
    """
    Lê raw_path, deduplica por id/doi, valida schema, escreve corpus_path.
    Retorna número de documentos no corpus final.
    """
```

## `src.preprocessing.config`

```python
@dataclass(frozen=True)
class PreprocessConfig:
    title_abstract_separator: str = ". "
    use_stemming: bool = False
    min_token_length: int = 2
```

## `src.preprocessing.pipeline`

```python
def build_indexable_text(
    title: str,
    abstract: str,
    config: PreprocessConfig,
) -> list[str]:
    """Concatena título+abstract e aplica pipeline FR-013."""

def preprocess_query(query: str, config: PreprocessConfig) -> list[str]:
    """Mesmo pipeline aplicado a consulta livre (FR-015)."""

def preprocess_document(article: dict, config: PreprocessConfig) -> list[str]:
    """Convenience: extrai title/abstract de CorpusArticle e chama build_indexable_text."""
```

## Notebook contract (`notebooks/01_coleta_arxiv.ipynb`)

1. Instanciar `CollectionConfig` com parâmetros do tema (LLM pruning).
2. Chamar `fetch_arxiv_raw(config)` — idempotente, retomável.
3. Chamar `normalize_corpus(config)` → `corpus.jsonl`.
4. Exibir resumo: query, contagem, distribuição por ano/categoria.
5. Demonstrar `preprocess_document` e `preprocess_query` em 1 exemplo.
