"""Gera site/dados.js (formato enxuto) e site/fotos/ a partir de dados/embu.json.

Uso: python -m coletor.site
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import requests

from .texto import norm

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados" / "embu.json"
SITE = RAIZ / "site"

# "O vereador Fulano, no uso das atribuições ... INDICA ao Chefe do Poder Executivo Municipal a ..."
VERBO = re.compile(r"\b(indica|requer|solicita|apresenta|propoe|propõe|indicar|solicitar)\b[,:]?\s*", re.I)
DESTINO = re.compile(
    r"^(?:(?:ao|a|à|aos|junto\s+ao)\s+)?(?:excelent[ií]ssimo\s+|exmo\.?\s+)?(?:senhor\s+|sr\.?\s+)?"
    r"(?:chefe\s+do\s+)?(?:poder\s+executivo|prefeito|prefeita|executivo)(?:\s+municipal)?"
    r"(?:\s*(?:,|e|através|atraves|por\s+meio)\s+(?:d[aoe]s?\s+)?(?:secretaria|órgão|orgao|departamento)s?[^,]{0,80})?\s*[,:]?\s*", re.I)
ENCHIMENTO = re.compile(
    r"^(?:que\s+(?:seja|sejam|se\s+fa[cç]a|determine|providencie)\s+(?:realizad[oa]s?|feit[oa]s?|efetuad[oa]s?)?\s*|"
    r"a\s+necessidade(?:\s+urgente)?\s+de\s+|a\s+realiza[cç][aã]o\s+de\s+|que\s+)", re.I)
PROPRIO = re.compile(
    r"\b(rua|avenida|av\.|estrada|travessa|alameda|viela|pra[cç]a|rodovia|jardim|vila|parque|bairro|"
    r"ch[aá]cara|recanto|residencial|escola|emef|emei|ubs|creche)\s+([^,;.()]{2,60})", re.I)
MINUSC = {"da", "de", "do", "das", "dos", "e", "a", "o", "na", "no", "em"}


def _titulo_proprio(m):
    pal = m.group(2).split()
    out = [p if p.lower() in MINUSC and i else p[:1].upper() + p[1:] for i, p in enumerate(pal)]
    return m.group(1)[:1].upper() + m.group(1)[1:] + " " + " ".join(out)


def texto_limpo(ementa: str, grupo: str) -> str:
    t = ementa.strip()
    letras = [c for c in t if c.isalpha()]
    caixa_alta = letras and sum(c.isupper() for c in letras) / len(letras) > 0.6
    if caixa_alta:
        t = t.lower()
    if grupo in "bc" and re.match(r"^(o|a|os|as)\s+vereador", t, re.I):
        m = VERBO.search(t)
        if m and m.end() < len(t) - 15:
            t = t[m.end():]
            t = DESTINO.sub("", t, count=1)
            t = ENCHIMENTO.sub("", t, count=1)
    if caixa_alta:
        t = PROPRIO.sub(_titulo_proprio, t)
    t = t.strip(" ,.;:-")
    return t[:1].upper() + t[1:] if t else ementa


def baixar_fotos(vereadores: list[dict]) -> set[str]:
    """Usa as fotos já padronizadas em site/fotos (marca/padronizar_fotos.py). Vereador novo
    sem foto tratada recebe a foto crua da ficha, até alguém rodar o padronizador."""
    pasta = SITE / "fotos"
    pasta.mkdir(parents=True, exist_ok=True)
    ok = {p.stem for p in pasta.glob("*.jpg")}
    s = requests.Session()
    s.headers["User-Agent"] = "RadarEmbu/0.1"
    for v in vereadores:
        if v["id"] in ok or not v.get("foto"):
            continue
        p = pasta / f"{v['id']}.jpg"
        print(f"  foto sem padronizar: {v['ap']} (rode marca/padronizar_fotos.py)")
        if not p.exists():
            try:
                r = s.get(v["foto"], timeout=60)
                r.raise_for_status()
                p.write_bytes(r.content)
            except Exception as e:
                print("  foto falhou:", v["ap"], e)
                continue
        ok.add(v["id"])
    return ok


def main():
    d = json.loads(DADOS.read_text(encoding="utf-8"))
    V = d["vereadores"]
    ajustes = json.loads((Path(__file__).parent / "ajustes.json").read_text(encoding="utf-8"))
    for v in V:
        if v["id"] in ajustes.get("nomes", {}):
            v["ap"] = ajustes["nomes"][v["id"]]
    # ordena: em exercício primeiro, depois por nome
    V.sort(key=lambda v: (not v.get("em_exercicio", True), norm(v["ap"])))
    idx = {v["id"]: i for i, v in enumerate(V)}
    fotos = baixar_fotos(V)

    props = sorted(d["propostas"], key=lambda p: (p["data"], int(p["id"])), reverse=True)
    pos = {p["id"]: i for i, p in enumerate(props)}
    items = []
    for p in props:
        items.append([
            p["id"], p["codigo"], texto_limpo(p["ementa"], p["grupo"]), p["data"].replace("-", ""),
            p["grupo"], p["situacao"], [idx[v] for v in p["vereadores"] if v in idx], p["tema"],
            p["fase"],
        ])

    # votações: link para a proposta quando o título cita "PROJETO DE LEI Nº 89/2026" etc.
    por_codigo = {}
    for p in props:
        por_codigo[(norm(p["tipo"])[:12], p["numero"], p["ano"])] = p["url"]

    def url_materia(m: str) -> str:
        mm = re.match(r"(.+?) (\d+)/(\d{4})$", m or "")
        if not mm:
            return ""
        return por_codigo.get((norm(mm.group(1))[:12], mm.group(2), mm.group(3)), "")

    sess_ok = [s for s in d["sessoes"] if s.get("votacoes") or s.get("presenca")]
    vv = []
    for v in V:
        naos = []
        for s in sess_ok:
            for vt in s.get("votacoes", []):
                voto = norm(vt["votos"].get(v["id"], ""))
                if voto in ("nao", "absteve") or voto.startswith("abst"):
                    naos.append({"d": s["data"], "t": vt["titulo"][:300], "v": "nao" if voto == "nao" else "abs",
                                 "m": vt.get("materia", ""), "u": url_materia(vt.get("materia", "")) or s.get("url_votacao", ""),
                                 "r": vt.get("resultado", "")})
        naos.sort(key=lambda x: x["d"], reverse=True)
        vv.append({
            "id": v["id"], "ap": v["ap"], "nome": v.get("nome", ""), "part": v.get("sigla", ""),
            "foto": v["id"] in fotos, "email": v.get("email", ""),
            "tel": v.get("tel", "") or v.get("cel", ""), "url": v.get("url", ""),
            "mesa": ("Suplente da Mesa" if v.get("mesa_ultima") == "Suplente" else v.get("mesa_ultima", "")),
            "mesa_fim": v.get("mesa_fim", ""),
            "ex": bool(v.get("em_exercicio")), "sf": bool(v.get("sem_ficha")),
            "P": v.get("P", 0), "F": v.get("F", 0), "S": v.get("sessoes", 0),
            "vs": v.get("sim", 0), "vn": v.get("nao", 0), "va": v.get("abst", 0),
            "cat": {k: v.get("cat", {}).get(k, 0) for k in "bchlo"}, "naos": naos,
        })

    rep = [{"r": g["rua"], "b": g["bairro"], "th": g["tema"], "n": g["n"], "a": g["n_vereadores"],
            "d0": g["de"].replace("-", ""), "d1": g["ate"].replace("-", ""),
            "ids": [pos[i] for i in g["ids"] if i in pos]} for g in d["repetidos"]]

    ult = max((s["data"] for s in sess_ok), default="")
    rx = {
        "ger": d["gerado_em"][:10], "gerh": d["gerado_em"], "posse": d["posse"],
        "sal": d["salario"], "cadeiras": d.get("cadeiras", 21),
        "v": vv, "items": items, "rep": rep,
        "bairros": [b for b, _ in d["bairros"]], "bairrosn": [n for _, n in d["bairros"]],
        "catot": d["catot"], "nvot": d["n_votacoes"], "unan": d["unanimes"],
        "sess": len(sess_ok), "ult": ult, "semreg": d["sessoes_sem_registro"],
        "fonte": d["fonte"],
    }
    txt = "window.RX=" + json.dumps(rx, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (SITE / "dados.js").write_text(txt, encoding="utf-8")
    print(f"site/dados.js: {len(txt) / 1e6:.2f} MB, {len(items)} propostas, {len(vv)} vereadores, {len(fotos)} fotos")


if __name__ == "__main__":
    main()
