"""Vereadores da legislatura: lista em parlamentares.aspx e ficha em parlamentar.aspx?id=N."""
from __future__ import annotations

import re

from .http import Cliente
from .texto import chave_nome


def _campo(sopa, rotulo: str) -> str:
    for lab in sopa.select("#dados_parlamentar .kt-widget__label"):
        if lab.get_text(strip=True).lower().startswith(rotulo.lower()):
            val = lab.find_next_sibling("span")
            return re.sub(r"^[\s/]+|[\s/]+$", "", val.get_text(" ", strip=True)) if val else ""
    return ""


def coletar(cli: Cliente) -> list[dict]:
    # sem ?leg= a página mostra a legislatura atual (16ª, 2025–2028) com titulares e suplentes
    # que já assumiram; ?leg=15 é a anterior. Quem está em exercício hoje sai das sessões.
    sopa = cli.sopa(cli.get("parlamentares.aspx").text)
    ids = []
    for a in sopa.select("a[href*='parlamentar.aspx?id=']"):
        m = re.search(r"id=(\d+)", a["href"])
        if m and m.group(1) not in ids:
            ids.append(m.group(1))
    out = []
    for pid in ids:
        s = cli.sopa(cli.get(f"parlamentar.aspx?id={pid}").text)
        nome = s.select_one("#nome_parlamentar")
        partido = s.select_one("#partido")
        foto = s.select_one("#ContentPlaceHolder1_foto_parlamentar img")
        texto = s.get_text(" ", strip=True)
        mesa = re.search(r"Participação na Mesa Diretora\s+(.+?)\s*\((\d\d/\d\d/\d{4}) a (\d\d/\d\d/\d{4}|o momento)", texto)
        ap = nome.get_text(strip=True) if nome else pid
        part = partido.get_text(strip=True) if partido else ""
        sigla = re.search(r"\(([^)]+)\)\s*$", part)
        out.append({
            "id": pid,
            "ap": ap,
            "nome": _campo(s, "Nome civil") or ap,
            "partido": part,
            "sigla": (sigla.group(1).strip() if sigla else part),
            "email": _campo(s, "E-mail"),
            "tel": _campo(s, "Telefone"),
            "cel": _campo(s, "Celular"),
            "foto": foto["src"] if foto and foto.get("src") else "",
            "url": f"https://nopapercloud.cmembu.sp.gov.br/spl/parlamentar.aspx?id={pid}",
            # o NoPaper só tem a 1ª formação da Mesa (até 31/01/2026); guarda o período para o site
            "mesa_ultima": mesa.group(1).strip() if mesa else "",
            "mesa_fim": ("" if not mesa or mesa.group(3) == "o momento"
                         else "-".join(reversed(mesa.group(3).split("/")))),
            "chave": chave_nome(ap),
        })
    print(f"  vereadores na legislatura: {len(out)}")
    return out
