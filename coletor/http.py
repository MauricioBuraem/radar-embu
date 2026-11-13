"""Cliente HTTP educado para o NoPaper da Câmara de Embu das Artes.

- Espera um intervalo entre requisições para não sobrecarregar o servidor.
- Tenta de novo em falhas temporárias.
- Guarda em disco arquivos que não mudam (PDFs de sessões já encerradas).
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://nopapercloud.cmembu.sp.gov.br/spl/"
UA = "RadarEmbu/0.1 (coletor de dados publicos; projeto independente)"


class Cliente:
    def __init__(self, cache_dir: Path, intervalo: float = 1.0):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA
        self.intervalo = intervalo
        self._ultimo = 0.0
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.n_req = 0

    def _espera(self):
        dt = time.monotonic() - self._ultimo
        if dt < self.intervalo:
            time.sleep(self.intervalo - dt)
        self._ultimo = time.monotonic()

    def req(self, metodo: str, url: str, **kw) -> requests.Response:
        if not url.startswith("http"):
            url = BASE + url
        kw.setdefault("timeout", 120)
        erro = None
        for tentativa in range(4):
            self._espera()
            try:
                r = self.s.request(metodo, url, **kw)
                self.n_req += 1
                if r.status_code >= 500:
                    raise requests.HTTPError(f"{r.status_code} em {url}")
                r.raise_for_status()
                return r
            except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
                erro = e
                time.sleep(3 * (tentativa + 1))
        raise RuntimeError(f"falhou depois de 4 tentativas: {url}: {erro}")

    def get(self, url: str, **kw) -> requests.Response:
        return self.req("GET", url, **kw)

    def post(self, url: str, **kw) -> requests.Response:
        return self.req("POST", url, **kw)

    def sopa(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    @staticmethod
    def campos_ocultos(sopa: BeautifulSoup) -> dict:
        """Campos __VIEWSTATE etc. necessários para os postbacks do ASP.NET."""
        return {i["name"]: i.get("value", "") for i in sopa.select("input[type=hidden][name]")}

    def arquivo(self, url: str, ext: str = ".pdf") -> bytes:
        """Baixa um arquivo e guarda em cache (o nome no NoPaper já tem carimbo de data e hash)."""
        chave = hashlib.sha1(url.split("?")[0].encode()).hexdigest()[:20]
        p = self.cache_dir / f"{chave}{ext}"
        if p.exists() and p.stat().st_size > 0:
            return p.read_bytes()
        dados = self.get(url).content
        p.write_bytes(dados)
        return dados
