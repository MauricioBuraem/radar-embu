"""Utilitários de texto (normalização sem acento, chaves de nome)."""
from __future__ import annotations

import re
import unicodedata


def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", sem_acento(s).lower()).strip()


def chave_nome(s: str) -> str:
    """Chave para casar 'Bulhões do Embu' (CSV/ficha) com 'BULHÕES DO EMBU' (PDF de votação)."""
    s = re.sub(r"[^a-z0-9 ]", " ", norm(s))
    return re.sub(r"\s+", " ", s).strip()
