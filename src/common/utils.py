import json
from pathlib import Path

def load_corpus(path: Path) -> list[dict]:
    """Carrega o corpus a partir de um arquivo .jsonl."""
    docs = []
    if not path.exists():
        print(f"Arquivo de corpus não encontrado em: {path}")
        return docs
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return docs
