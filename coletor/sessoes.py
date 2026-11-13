"""Sessões plenárias, votações nominais e presença.

A lista vem de sessoes.aspx (paginada por postback ASP.NET). Cada sessão tem um PDF
"Resultado da Votação" gerado pelo painel eletrônico, com:
  - cada votação, aberta por "Votações da Sessão": título, quórum, placar, resultado e o
    voto de cada vereador;
  - no fim, a "Lista de Presença da Sessão" (Presente / ---).

Atenção: a lista de presença do PDF marca "---" até para quem votou. Por isso a presença
é calculada como: votou em alguma votação OU aparece como "Presente".
"""
from __future__ import annotations

import io
import json
import re
from datetime import date
from pathlib import Path

import pypdf

from .http import Cliente
from .texto import chave_nome

PREF = "ctl00$ContentPlaceHolder1$"
CABECALHO = [re.compile(r"^ENVSENSE$"), re.compile(r"^\d\d/\d\d/\d{4}$"), re.compile(r"^\d\d:\d\d:\d\d \d+ / \d+$")]
MARCA = "Votações da Sessão"
PRESENCA = "Lista de Presença da Sessão"
APELIDOS = json.loads((Path(__file__).parent / "apelidos.json").read_text(encoding="utf-8"))
MATERIA_RX = re.compile(
    r"(PROJETO DE LEI COMPLEMENTAR|PROJETO DE LEI|PROJETO DE DECRETO LEGISLATIVO|PROJETO DE RESOLU..O|"
    r"PROPOSTA DE EMENDA . LEI ORG.NICA|REQUERIMENTO|MO..O|VETO|EMENDA IMPOSITIVA|EMENDA|INDICA..O)"
    r"[^\d]{0,40}?N[º°O]?\.?\s*(\d+)\s*/\s*(\d{4})", re.I)


# ---------------------------------------------------------------- lista de sessões
def _ler_pagina(sopa) -> list[dict]:
    out = []
    for td in sopa.select("td"):
        forte = td.select_one("div strong")
        if not forte or "Data:" not in td.get_text():
            continue
        titulo = re.sub(r"\s+", " ", forte.get_text(" ", strip=True))
        m = re.search(r"Data:\s*(\d\d)/(\d\d)/(\d{4})", td.get_text(" ", strip=True))
        if not m:
            continue
        docs = {}
        for a in td.select("a[href*='/SES/']"):
            nome = re.sub(r"\s*-\s*N.*$", "", a.get_text(strip=True))
            docs.setdefault(nome, a["href"].replace("http://", "https://"))
        sid = re.search(r"/SES/(\d+)/", next(iter(docs.values()), "")) if docs else None
        out.append({
            "id": sid.group(1) if sid else "",
            "titulo": titulo,
            "data": f"{m.group(3)}-{m.group(2)}-{m.group(1)}",
            "docs": docs,
        })
    return out


def listar(cli: Cliente, desde: date) -> list[dict]:
    url = "sessoes.aspx"
    datas = {PREF + "txt_data_inicio": desde.strftime("%d/%m/%Y"),
             PREF + "txt_data_final": date.today().strftime("%d/%m/%Y")}
    sopa = cli.sopa(cli.get(url).text)
    form = cli.campos_ocultos(sopa) | datas | {
        PREF + "ddl_tipo_sessao": "", PREF + "ddl_sessao_arquivo_tipo": "", PREF + "btn_buscar": "Buscar"}
    sopa = cli.sopa(cli.post(url, data=form).text)
    sessoes, pagina = [], 1
    while True:
        novas = _ler_pagina(sopa)
        sessoes.extend(novas)
        prox = None
        for a in sopa.select("a[href*=lbPaging]"):
            if a.get_text(strip=True) == str(pagina + 1):
                prox = re.search(r"__doPostBack\('([^']+)'", a["href"]).group(1)
        if not prox or not novas:
            break
        form = cli.campos_ocultos(sopa) | datas | {"__EVENTTARGET": prox, "__EVENTARGUMENT": ""}
        sopa = cli.sopa(cli.post(url, data=form).text)
        pagina += 1
    vistos, unicas = set(), []
    for s in sessoes:
        k = (s["id"], s["titulo"], s["data"])
        if k not in vistos and s["data"] >= desde.isoformat():
            vistos.add(k)
            unicas.append(s)
    print(f"  sessões desde {desde}: {len(unicas)} ({pagina} páginas)")
    return unicas


# ---------------------------------------------------------------- PDF de votação
def linhas_pdf(dados: bytes) -> list[str]:
    pdf = pypdf.PdfReader(io.BytesIO(dados))
    linhas = []
    for p in pdf.pages:
        for ln in (p.extract_text() or "").splitlines():
            ln = ln.strip()
            if ln and not any(rx.match(ln) for rx in CABECALHO):
                linhas.append(ln)
    return linhas


def _extrair_para_txt(pdf: str, txt: str) -> str:
    """Roda num processo separado: extrair texto do PDF é lento (~15 s cada)."""
    try:
        L = linhas_pdf(Path(pdf).read_bytes())
    except Exception as e:  # arquivo que não é PDF (já apareceu .doc) ou corrompido
        return f"erro: {e}"
    Path(txt).write_text("\n".join(L), encoding="utf-8")
    return "ok"


def textos_das_sessoes(cli: Cliente, sessoes: list[dict]) -> dict[str, list[str]]:
    """Baixa os PDFs (um por vez, com intervalo) e extrai o texto em paralelo, com cache em .txt."""
    import hashlib
    import os
    from concurrent.futures import ProcessPoolExecutor

    pend, saida = {}, {}
    for s in sessoes:
        url = s["docs"].get("Resultado da Votação")
        s["tem_votacao"] = bool(url)
        if not url:
            continue
        base = hashlib.sha1(url.split("?")[0].encode()).hexdigest()[:20]
        txt = cli.cache_dir / f"{base}.txt"
        chave = s["id"] + s["data"]
        if txt.exists():
            saida[chave] = txt.read_text(encoding="utf-8").splitlines()
            continue
        try:
            cli.arquivo(url)
        except Exception as e:
            s["erro"] = str(e)
            continue
        pend[chave] = (str(cli.cache_dir / f"{base}.pdf"), str(txt), s)
    if pend:
        print(f"  extraindo texto de {len(pend)} PDFs em paralelo...")
        with ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2) - 1)) as ex:
            futs = {ch: ex.submit(_extrair_para_txt, pdf, txt) for ch, (pdf, txt, _) in pend.items()}
            for ch, f in futs.items():
                r = f.result()
                pdf, txt, s = pend[ch]
                if r == "ok":
                    saida[ch] = Path(txt).read_text(encoding="utf-8").splitlines()
                else:
                    s["erro"] = r
    return saida


def _tokens(nome: str) -> set[str]:
    t = chave_nome(nome).replace(" jr", " junior").split()
    return {p for p in t if p not in {"da", "de", "do", "das", "dos", "e"}}


IGNORAR = {"root"}  # usuário técnico do painel eletrônico


class Casador:
    """Casa o início de uma linha do PDF com um vereador conhecido."""

    def __init__(self, vereadores: list[dict]):
        pares = {chave_nome(v["nome"]): v["id"] for v in vereadores if v.get("nome")}
        pares.update({v["chave"]: v["id"] for v in vereadores})
        pares.update({k: v for k, v in APELIDOS.items() if not k.startswith("_")})
        self.chaves = sorted(pares.items(), key=lambda x: -len(x[0]))
        self.partidos: set[str] = set()
        self.nomes = [(_tokens(v["ap"]), _tokens(v.get("nome") or ""), v["id"]) for v in vereadores]

    def por_nome_civil(self, chave: str):
        """Casa nome completo do PDF com a ficha quando não há ambiguidade:
        todas as palavras do nome parlamentar estão no nome do PDF ("Gustavo Arenzon" ⊂
        "Gustavo de Lorena Infante Arenzon"), ou o nome do PDF está contido no nome civil."""
        t = _tokens(chave)
        if len(t) < 2:
            return None
        achados = {vid for ap, civ, vid in self.nomes if (len(ap) >= 2 and ap <= t) or (civ and t <= civ)}
        return achados.pop() if len(achados) == 1 else None

    def casar(self, linha: str):
        k = chave_nome(linha)
        for chave, vid in self.chaves:
            if k.startswith(chave + " "):
                resto = " ".join(linha.split()[len(chave.split()):])
                self.partidos.add(re.sub(r"\s+\S+$", "", resto))  # "Partido X (SIGLA)"
                return vid, resto
        return None

    def adicionar(self, chave: str, vid: str):
        self.chaves.append((chave, vid))
        self.chaves.sort(key=lambda x: -len(x[0]))


def _titulo(linhas: list[str]) -> str:
    """O PDF repete o título: primeiro quebrado em linhas, depois inteiro. Remove a repetição."""
    junto = " ".join(linhas)
    for s in range(1, len(linhas)):
        a, b = " ".join(linhas[:s]), " ".join(linhas[s:])
        if a == b or b.startswith(a) and len(a) > 30:
            return b
    return junto


def ler_votacao(L: list[str], cas: Casador, nao_casados: set) -> dict:
    marcas = [i for i, ln in enumerate(L) if ln == MARCA]
    try:
        ip = L.index(PRESENCA)
    except ValueError:
        ip = len(L)
    votacoes = []
    for n, ini in enumerate(marcas):
        fim = marcas[n + 1] if n + 1 < len(marcas) else ip
        bloco = L[ini + 1:fim]
        try:
            jt = bloco.index("Tipo:")
        except ValueError:
            continue
        campos, k = {}, jt
        while k < len(bloco) and not bloco[k].startswith("Parlamentar Partido Voto"):
            if bloco[k].endswith(":"):
                prox = bloco[k + 1] if k + 1 < len(bloco) else ""
                campos[bloco[k][:-1]] = "" if prox.endswith(":") else prox
                k += 1 if prox.endswith(":") else 2
            else:
                k += 1
        votos = {}
        for ln in bloco[k:]:
            if ln.startswith("Parlamentar Partido Voto"):
                continue
            m = cas.casar(ln)
            if m:
                votos[m[0]] = m[1].rsplit(" ", 1)[-1]
            elif re.search(r"\([^)]*\)\s*\S+$", ln):
                nao_casados.add(ln)
        titulo = _titulo(bloco[:jt])
        mt = MATERIA_RX.search(titulo)
        votacoes.append({
            "titulo": titulo[:400],
            "materia": (f"{mt.group(1).upper()} {mt.group(2)}/{mt.group(3)}" if mt else ""),
            "quorum": campos.get("Tipo", ""),
            "placar": campos.get("Votos", ""),
            "resultado": campos.get("Resultado", ""),
            "votos": votos,
        })
    presenca = {}
    for ln in L[ip + 1:]:
        if ln.startswith("Nome Partido Status"):
            continue
        m = cas.casar(ln)
        if m:
            presenca[m[0]] = m[1].rsplit(" ", 1)[-1]
        elif re.search(r"\([^)]*\)\s*\S+$", ln) and not chave_nome(ln).startswith(tuple(IGNORAR)):
            nao_casados.add(ln)
    return {"votacoes": votacoes, "presenca": presenca}


def _novos_nomes(nao_casados: set, partidos: set[str]) -> dict[str, tuple[str, str]]:
    """Nomes que aparecem nos PDFs mas não têm ficha: chave -> (nome, partido)."""
    novos = {}
    for ln in nao_casados:
        for p in sorted(partidos, key=len, reverse=True):
            i = ln.find(" " + p + " ")
            if i > 0:
                nome = ln[:i].strip()
                novos[chave_nome(nome)] = (nome, p)
                break
    return novos


def coletar(cli: Cliente, desde: date, vereadores: list[dict]) -> tuple[list[dict], set]:
    cas = Casador(vereadores)
    sessoes = listar(cli, desde)
    textos = textos_das_sessoes(cli, sessoes)

    # 1ª passada: descobre nomes sem ficha; 2ª: lê tudo já com eles
    nc: set = set()
    for L in textos.values():
        ler_votacao(L, cas, nc)
    for chave, (nome, partido) in _novos_nomes(nc, cas.partidos).items():
        if chave in IGNORAR:
            continue
        existente = cas.por_nome_civil(chave)
        if existente:
            cas.adicionar(chave, existente)
            continue
        vid = "x-" + chave.replace(" ", "-")
        sigla = re.search(r"\(([^)]+)\)", partido)
        vereadores.append({
            "id": vid, "ap": nome.title().replace(" Do ", " do ").replace(" Da ", " da ").replace(" De ", " de "),
            "nome": "", "partido": partido, "sigla": sigla.group(1).strip() if sigla else partido,
            "email": "", "tel": "", "cel": "", "foto": "", "url": "", "mesa_ultima": "",
            "chave": chave, "sem_ficha": True,
        })
        cas.adicionar(chave, vid)
    nao_casados: set = set()
    for s in sessoes:
        L = textos.get(s["id"] + s["data"])
        if L is not None:
            s.update(ler_votacao(L, cas, nao_casados))
    return sessoes, nao_casados
