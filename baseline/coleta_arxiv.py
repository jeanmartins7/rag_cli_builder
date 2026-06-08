import json
import time
from pathlib import Path

import arxiv
import pandas as pd
from tqdm import tqdm

# -----------------------------------------------------------------------------
# ESCOPO DA COLEÇÃO
# -----------------------------------------------------------------------------

KEYWORDS = [
    "structural pruning",
    "LLM compression",
    "attention heads pruning",
    "MLP pruning",
    "parameter efficient fine-tuning",
]

CATEGORIES = ["cs.CL", "cs.LG", "cs.AI"]

YEAR_FROM = 2018
YEAR_TO = 2026

TARGET_SIZE = 2000
PAGE_SIZE = 50

OUTPUT_DIR = Path("../data")
RAW_PATH = OUTPUT_DIR / "arxiv_raw.jsonl"
CORPUS_PATH = OUTPUT_DIR / "corpus.jsonl"


def build_query(keywords: list[str], categories: list[str]) -> str:
    """Monta a string de query no formato esperado pela API do ArXiv."""
    kw_part = " OR ".join([f'all:"{k}"' for k in keywords]) if keywords else ""
    cat_part = " OR ".join([f"cat:{c}" for c in categories]) if categories else ""

    parts = [p for p in [f"({kw_part})" if kw_part else "",
                          f"({cat_part})" if cat_part else ""] if p]
    return " AND ".join(parts) if parts else "all:*"


def already_collected_ids(path: Path) -> set:
    """Lê o arquivo .jsonl (se existir) e retorna os IDs já salvos."""
    if not path.exists():
        return set()
    ids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                ids.add(json.loads(line)["arxiv_id"])
            except Exception:
                continue
    return ids


def collect_arxiv(
    query: str, 
    target_size: int, 
    page_size: int, 
    year_from: int | None, 
    year_to: int | None,
    out_path: Path,
    max_outer_attempts: int = 6,
    initial_backoff_seconds: int = 60
) -> int:
    """
    Coleta artigos do ArXiv, salvando incrementalmente em JSONL.
    """
    client = arxiv.Client(page_size=page_size, delay_seconds=5, num_retries=8)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen = already_collected_ids(out_path)
    print(f"Já coletados anteriormente: {len(seen)} artigos.")

    offset = 0
    outer_attempt = 0

    while len(seen) < target_size and outer_attempt < max_outer_attempts:
        try:
            search = arxiv.Search(
                query=query,
                max_results=target_size * 3,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )

            print(f"\nIniciando/retomando do offset={offset} "
                  f"(salvos={len(seen)}, meta={target_size}).")

            with open(out_path, "a", encoding="utf-8") as f:
                pbar = tqdm(initial=len(seen), total=target_size, desc="coletando")
                
                for result in client.results(search, offset=offset):
                    offset += 1
                    year = result.published.year if result.published else None
                    if year_from is not None and (year is None or year < year_from):
                        continue
                    if year_to is not None and (year is None or year > year_to):
                        continue

                    arxiv_id = result.get_short_id().split("v")[0]
                    if arxiv_id in seen:
                        continue

                    record = {
                        "arxiv_id": arxiv_id,
                        "title": (result.title or "").strip(),
                        "abstract": (result.summary or "").strip().replace("\n", " "),
                        "authors": [a.name for a in result.authors],
                        "categories": list(result.categories or []),
                        "primary_category": result.primary_category,
                        "published": result.published.isoformat() if result.published else None,
                        "updated": result.updated.isoformat() if result.updated else None,
                        "doi": result.doi,
                        "pdf_url": result.pdf_url,
                        "entry_id": result.entry_id,
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f.flush()
                    seen.add(arxiv_id)
                    pbar.update(1)
                    pbar.set_postfix(offset=offset)

                    if len(seen) >= target_size:
                        break
                        
                pbar.close()

            break

        except Exception as e:
            outer_attempt += 1
            wait = min(initial_backoff_seconds * (2 ** (outer_attempt - 1)), 600)
            print(f"\n[aviso] coleta interrompida (tentativa {outer_attempt}/"
                  f"{max_outer_attempts}): {type(e).__name__}: {e}")
            print(f"[aviso] aguardando {wait}s antes de retomar do offset={offset}...")
            for _ in tqdm(range(wait), desc="backoff", leave=False):
                time.sleep(1)

    print(f"\nColeta finalizada. Total acumulado em {out_path}: {len(seen)} artigos.")
    if len(seen) < target_size:
        print(f"[atenção] Não atingiu a meta de {target_size} (parou em {len(seen)}).")
        print( "[atenção] Você pode rodar o script novamente para continuar de onde parou.")
    return len(seen)


def load_jsonl(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def normalize_and_deduplicate(raw_path: Path, corpus_path: Path) -> None:
    """Normaliza os dados brutos, deduplica e salva o corpus limpo."""
    if not raw_path.exists():
        print(f"Arquivo {raw_path} não encontrado.")
        return

    raw = load_jsonl(raw_path)
    print("Registros brutos:", len(raw))

    df = pd.DataFrame(raw)
    df["updated_dt"] = pd.to_datetime(df["updated"], errors="coerce")
    df = df.sort_values("updated_dt").drop_duplicates("arxiv_id", keep="last")

    df = df[df["title"].str.len() > 0]
    df = df[df["abstract"].str.len() > 50]

    print("Após deduplicação e limpeza:", len(df))

    cols = ["arxiv_id", "title", "abstract", "authors", "categories",
             "primary_category", "published", "doi", "pdf_url"]

    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    with open(corpus_path, "w", encoding="utf-8") as f:
        for _, row in df[cols].iterrows():
            f.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")

    print(f"Corpus salvo em: {corpus_path} ({len(df)} documentos).")

    df["year"] = pd.to_datetime(df["published"], errors="coerce").dt.year
    print("Distribuição por ano:")
    print(df["year"].value_counts().sort_index())
    print("\nDistribuição por categoria primária:")
    print(df["primary_category"].value_counts().head(10))


def run_collection():
    """
    Executa o pipeline completo de coleta e normalização.
    """
    print("Iniciando coleta e normalização de dados do ArXiv...")
    print("Configuração:")
    print(" - Keywords  :", KEYWORDS)
    print(" - Categories:", CATEGORIES)
    print(" - Years     :", YEAR_FROM, "->", YEAR_TO)
    print(" - Target    :", TARGET_SIZE)
    
    query = build_query(KEYWORDS, CATEGORIES)
    print("Query final:\n", query)

    collect_arxiv(
        query=query,
        target_size=TARGET_SIZE,
        page_size=PAGE_SIZE,
        year_from=YEAR_FROM,
        year_to=YEAR_TO,
        out_path=RAW_PATH,
    )
    
    normalize_and_deduplicate(RAW_PATH, CORPUS_PATH)
    print("Pipeline de coleta e normalização concluído.")


if __name__ == "__main__":
    run_collection()
