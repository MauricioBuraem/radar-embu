"""Propostas (indicações, requerimentos, moções, projetos...) via exportação CSV do NoPaper.

`consulta-producao.aspx?ano=AAAA` + postback no botão "CSV" devolve todas as
proposições do ano em um único arquivo (codificação Windows-1252).
"""
from __future__ import annotations

import re
from pathlib import Path

from .http import Cliente


def tipos_do_ano(cli: Cliente, ano: int) -> list[str]:
    """IDs internos dos tipos de proposição que têm registros no ano (consulta-tipo.aspx)."""
    sopa = cli.sopa(cli.get("consulta-tipo.aspx").text)
    ids = []
    for a in sopa.select(f"a[href*='ano_proposicao={ano}']"):
        m = re.search(r"tipo=(\d+)", a["href"])
        if m and m.group(1) not in ids:
            ids.append(m.group(1))
    return ids


def exportar_csv(cli: Cliente, consulta: str) -> str:
    """Abre a consulta e aciona o botão 'CSV'. A exportação falha (devolve HTML) se a consulta for grande demais."""
    url = f"consulta-producao.aspx?{consulta}"
    sopa = cli.sopa(cli.get(url).text)
    form = cli.campos_ocultos(sopa)
    form["ctl00$ContentPlaceHolder1$btn_export_csv"] = "CSV"
    r = cli.post(url, data=form)
    if "csv" not in r.headers.get("Content-Type", "").lower():
        raise RuntimeError(f"exportação CSV de '{consulta}' não devolveu CSV")
    return r.content.decode("cp1252")


def baixar_csv_ano(cli: Cliente, ano: int, cache: Path, forcar: bool) -> list[str]:
    """Um CSV por tipo de proposição (o ano inteiro de uma vez estoura o limite da exportação)."""
    pasta = cache / f"producao_{ano}"
    if pasta.exists() and not forcar and any(pasta.iterdir()):
        return [p.read_text(encoding="utf-8") for p in sorted(pasta.glob("*.csv"))]
    pasta.mkdir(parents=True, exist_ok=True)
    textos = []
    for tid in tipos_do_ano(cli, ano):
        txt = exportar_csv(cli, f"tipo={tid}&ano_proposicao={ano}")
        (pasta / f"tipo_{tid}.csv").write_text(txt, encoding="utf-8")
        textos.append(txt)
    return textos


# O CSV do NoPaper não escapa aspas nem quebras de linha dentro da ementa, então um leitor
# CSV comum desalinha as colunas. Lemos cada registro pelas pontas, que têm formato fixo:
#   início: ID,Processo,Ano,Tipo,Nº,Ano,
#   fim:    ,Protocolo,Autor(es),Data,Fase,Setor,Arquivado(Sim/Não),Situação
INICIO = re.compile(r"(?m)^(\d+),(\d+),(\d{4}),([^,\n]*),(\d+),(\d{4}),")
FIM = re.compile(r",(\d\d/\d\d/\d{4}),([^,]*),([^,]*),(Sim|Não),([^,]*)$")
PROT_AUTOR = re.compile(r"^(.*),(\d*),([^\d]*)$", re.S)


def _limpa(s: str) -> str:
    s = s.replace('""', '"').strip()
    s = re.sub(r'^"+|"+$', "", s)
    return re.sub(r"\s+", " ", s).strip()


def ler_csv(texto: str) -> list[dict]:
    ms = list(INICIO.finditer(texto))
    out = []
    for i, m in enumerate(ms):
        corpo = texto[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(texto)].rstrip("\r\n ")
        fim = FIM.search(corpo)
        if not fim:
            continue
        resto = corpo[:fim.start()]
        pa = PROT_AUTOR.match(resto)
        ementa, prot, autor = (pa.group(1), pa.group(2), pa.group(3)) if pa else (resto, "", "")
        d, mes, a = fim.group(1).split("/")
        item = {
            "id": m.group(1), "processo": m.group(2), "tipo": m.group(4).strip(),
            "numero": m.group(5), "ano": m.group(6),
            "ementa": _limpa(ementa), "protocolo": prot,
            "autores": [x for x in (_limpa(p) for p in re.split(r"[,;]", autor)) if x],
            "data": f"{a}-{mes}-{d}",
            "fase": fim.group(2).strip(), "setor": fim.group(3).strip(), "situacao": fim.group(5).strip(),
        }
        item["codigo"] = f"{item['tipo']} {item['numero']}/{item['ano']}"
        item["url"] = f"https://nopapercloud.cmembu.sp.gov.br/spl/processo.aspx?id={item['id']}"
        out.append(item)
    return out


def coletar(cli: Cliente, anos: list[int], cache: Path, ano_atual: int) -> list[dict]:
    todos = []
    for ano in anos:
        itens = [i for txt in baixar_csv_ano(cli, ano, cache, forcar=(ano >= ano_atual)) for i in ler_csv(txt)]
        print(f"  propostas {ano}: {len(itens)}")
        todos.extend(itens)
    # o mesmo ID pode aparecer em dois anos (processo x proposição); mantém o primeiro
    vistos, unicos = set(), []
    for it in todos:
        if it["id"] not in vistos:
            vistos.add(it["id"])
            unicos.append(it)
    return unicos
