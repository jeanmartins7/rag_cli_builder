"""Deterministic preprocessing: title+abstract → tokens."""

from __future__ import annotations

import re

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from src.preprocessing.config import PreprocessConfig

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _apply_stemming(tokens: list[str], config: PreprocessConfig) -> list[str]:
    if not config.use_stemming:
        return tokens
    from nltk.stem import SnowballStemmer

    stemmer = SnowballStemmer(config.language)
    return [stemmer.stem(t) for t in tokens]


def _filter_tokens(tokens: list[str], config: PreprocessConfig) -> list[str]:
    stopwords = ENGLISH_STOP_WORDS
    return [
        t
        for t in tokens
        if len(t) >= config.min_token_length and t not in stopwords
    ]


def _preprocess_text(text: str, config: PreprocessConfig) -> list[str]:
    tokens = _tokenize(text)
    tokens = _filter_tokens(tokens, config)
    return _apply_stemming(tokens, config)


def build_indexable_text(
    title: str,
    abstract: str,
    config: PreprocessConfig,
) -> list[str]:
    """Concatenate title+abstract and apply FR-013 preprocessing pipeline."""
    combined = f"{title.strip()}{config.title_abstract_separator}{abstract.strip()}"
    return _preprocess_text(combined, config)


def preprocess_query(query: str, config: PreprocessConfig) -> list[str]:
    """Apply same pipeline to a free-text query (FR-015)."""
    return _preprocess_text(query.strip(), config)


def preprocess_document(article: dict, config: PreprocessConfig) -> list[str]:
    """Extract title/abstract from CorpusArticle and preprocess."""
    return build_indexable_text(
        article["title"],
        article["abstract"],
        config,
    )
