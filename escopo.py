# -----------------------------------------------------------------------------
# DEFINA AQUI O ESCOPO DA SUA COLEÇÃO
# -----------------------------------------------------------------------------
from pathlib import Path

# Palavras-chave / frases que descrevem o seu tema. Serão buscadas em
# título e abstract (operador 'all:' do ArXiv).
KEYWORDS = [
    "fraud detection",
    "anomaly detection",
    "credit card fraud",
    "financial transactions",
    "money laundering",
]

# Categorias do ArXiv a considerar.
CATEGORIES = ["cs.LG", "cs.CR", "stat.ML"]

# Janela temporal (ano de submissão). Use None para não restringir.
YEAR_FROM = 2018
YEAR_TO = 2026

# Tamanho-alvo aproximado da coleção (redefinido para 10 para teste rápido).
TARGET_SIZE = 10

# Tamanho de cada página retornada pela API.
PAGE_SIZE = 10
