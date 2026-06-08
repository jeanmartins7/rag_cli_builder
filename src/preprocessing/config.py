"""Preprocessing configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PreprocessConfig:
    """Frozen configuration for text preprocessing pipeline."""

    title_abstract_separator: str = ". "
    use_stemming: bool = False
    min_token_length: int = 2
    language: str = "english"
