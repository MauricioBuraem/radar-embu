"""Coletor do Radar Embu.

Uso:
    python -m coletor                 # coleta desde 2025-01-01 e grava dados/embu.json
    python -m coletor --desde 2026-01-01 --sem-sessoes
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

from . import analise, propostas, sessoes, vereadores
from .http import Cliente
from .analise import TEMAS

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2025-01-01", help="data de início (posse da legislatura)")
    ap.add_argument("--sem-sessoes", action="store_true", help="pula sessões/votações (mais rápido)")
    ap.add_argument("--intervalo", type=float, default=1.0, help="segundos entre requisições")
    a = ap.parse_args()

    desde = date.fromisoformat(a.desde)
    hoje = date.today()
    cache = DADOS / "cache"
    cli = Cliente(cache / "arquivos", intervalo=a.intervalo)

    print("1/3 vereadores")
    vers = vereadores.coletar(cli)

    print("2/3 propostas")
    props = propostas.coletar(cli, list(range(desde.year, hoje.year + 1)), cache, hoje.year)
    props = [p for p in props if p["data"] >= desde.isoformat()]

    sess, nao_casados = [], set()
    if not a.sem_sessoes:
        print("3/3 sessões e votações")
        sess, nao_casados = sessoes.coletar(cli, desde, vers)

    res = analise.analisar(props, vers, sess)
    saida = {
        "gerado_em": datetime.now().astimezone().isoformat(timespec="minutes"),
        "fonte": "https://nopapercloud.cmembu.sp.gov.br/spl/",
        "posse": desde.isoformat(),
        # Subsídio da legislatura 2025–2028, aprovado pela Câmara em 11/10/2022 (fonte: imprensa local).
        # TODO: trocar a fonte pelo ato oficial publicado pela Câmara quando localizado.
        "salario": {"v": 12661.12, "fonte": "Verbo Online, 09/11/2022",
                    "u": "https://verboonline.com.br/2022/11/09/vereadores-de-embu-sobem-salario-e-ainda-aprovam-13o-e-ferias-para-si-proprios/"},
        "cadeiras": 21,
        "temas": {k: n for k, n, _ in TEMAS},
        "vereadores": vers,
        "propostas": props,
        "sessoes": [{k: v for k, v in s.items() if k != "docs"} | {"url_votacao": s.get("docs", {}).get("Resultado da Votação", "")} for s in sess],
        **res,
        "nomes_nao_casados_pdf": sorted(nao_casados),
    }
    DADOS.mkdir(exist_ok=True)
    (DADOS / "embu.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nok: {len(props)} propostas, {len(vers)} vereadores, {len(sess)} sessões, "
          f"{res['n_votacoes']} votações nominais, {cli.n_req} requisições -> dados/embu.json")


if __name__ == "__main__":
    main()
