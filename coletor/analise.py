"""Classificação das propostas, ruas/bairros, pedidos repetidos e números por vereador."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict

from .texto import chave_nome, norm, sem_acento

# ------------------------------------------------------------------ tipo -> grupo
# b = pedido no bairro, c = cobrança/pergunta, h = homenagem, l = proposta de lei, o = outros
HOMENAGEM = re.compile(r"aplauso|congratula|parabeniza|pesar|falecimento|titulo de cidadao|cidadao embuense|"
                       r"medalha|comenda|honra|diploma|denomina|da nome|institui o dia|institui a semana|"
                       r"dia municipal|semana municipal|calendario oficial|data comemorativa|homenage")


def grupo(tipo: str, ementa: str) -> str:
    t, e = norm(tipo), norm(ementa)
    if t.startswith("indica"):
        return "b"
    if t.startswith("requerimento"):
        return "c"
    if t.startswith("mocao"):
        return "h" if HOMENAGEM.search(e) else "o"
    if "decreto legislativo" in t or ("projeto de lei" in t) or "lei complementar" in t:
        return "h" if HOMENAGEM.search(e) else "l"
    return "o"


# ------------------------------------------------------------------ assunto
TEMAS = [
    ("luz", "Iluminação", r"ilumina|lampada|luminaria|poste|refletor|\bled\b"),
    ("asf", "Asfalto e buracos", r"tapa[- ]?buraco|buraco|asfalt|recape|pavimenta|operacao tapa"),
    ("tra", "Trânsito", r"sinaliza|lombada|transito|semaforo|faixa de pedestre|redutor de velocidade|rotatoria|estacionamento|placa"),
    ("agu", "Água e esgoto", r"esgoto|vazamento|drenagem|alagamento|enchente|\bagua\b|bueiro|boca de lobo|galeria|corrego|sabesp|canaliza"),
    ("lim", "Limpeza e poda", r"rocag|limpeza|capina|poda|\bmato\b|entulho|cata[- ]?bagulho|arvore|descarte|lixo|coleta"),
    ("cal", "Calçadas", r"calcada|passeio publico|sarjeta|meio[- ]fio|\bguia"),
    ("laz", "Praças e lazer", r"praca|playground|academia ao ar livre|parque|quadra|campo de futebol|area de lazer"),
    ("sau", "Saúde", r"\bubs\b|saude|medic|hospital|\bupa\b|dengue|vacina|pronto[- ]socorro"),
    ("edu", "Escolas", r"escola|emei|emef|creche|aluno|educa"),
    ("seg", "Segurança", r"seguranca|guarda civil|\bgcm\b|ronda|camera|policia|monitoramento"),
    ("bus", "Ônibus", r"onibus|transporte publico|transporte coletivo|abrigo|ponto de parada"),
]
TEMAS_RX = [(k, nome, re.compile(rx)) for k, nome, rx in TEMAS]


def tema(ementa: str) -> str:
    e = norm(ementa)
    for k, _, rx in TEMAS_RX:
        if rx.search(e):
            return k
    return ""


# ------------------------------------------------------------------ ruas e bairros
LOGR = r"(?:rua|r\.|avenida|av\.?|estrada|estr\.|travessa|tv\.|alameda|al\.|viela|praca|rodovia|largo|passagem|caminho|servidao)"
PARADA = (r"(?=\s*(?:,|;|\(|\)|/|\.(?:\s|$)|\s[-–]\s|\bn[º°o]\.?\s*\d|\bnumero\b|\baltura\b|\bproximo\b|\bproxima\b|\bem frente\b|"
          r"\bjunto\b|\bentre\b|\bate\b|\bdesde\b|\bno bairro\b|\bbairro\b|\bnos bairros\b|\bno jardim\b|\bna vila\b|\bno parque\b|"
          r"\bno municipio\b|\bem toda\b|\bem toda a\b|\bcom a\b|\bcom o\b|\be na\b|\be no\b|\be da\b|\bque\b|$))")
RUA_RX = re.compile(r"\b(" + LOGR + r")\s+([^\s,;()].{1,70}?)" + PARADA)
BAIRRO_PREF = r"(?:jardim|jd\.?|vila|vl\.?|parque|pq\.?|chacara|chacaras|recanto|conjunto|cj\.?|nucleo|residencial|sitio|estancia)"
RUA_GENERICA = re.compile(r"^\w+\.? (localizad|situad|existente|public|municipal|proxim|do bairro|da regiao|da cidade|em frente|ao lado)")
BAIRRO_RX = re.compile(r"\bbairro\s+(?:do\s+|da\s+|de\s+)?([^\s,;()].{1,40}?)" + PARADA)
BAIRRO_RX2 = re.compile(r"\b(" + BAIRRO_PREF + r"\s+[^\s,;()].{1,35}?)" + PARADA)
ABREV = {"r.": "rua", "av": "avenida", "av.": "avenida", "estr.": "estrada", "tv.": "travessa", "al.": "alameda",
         "jd": "jardim", "jd.": "jardim", "vl": "vila", "vl.": "vila", "pq": "parque", "pq.": "parque", "cj": "conjunto", "cj.": "conjunto"}
NAO_BAIRRO = re.compile(r"^(sao paulo|santa casa|santo andre|vila? ?municipal|cidade de embu|cidade|estancia turistica|sitio eletronico)")


def _bonito(s: str) -> str:
    menores = {"da", "de", "do", "das", "dos", "e"}
    pal = s.split()
    return " ".join(p if (i and p in menores) else p[:1].upper() + p[1:] for i, p in enumerate(pal))


def _expande(s: str) -> str:
    pal = s.split()
    if pal and pal[0] in ABREV:
        pal[0] = ABREV[pal[0]]
    return " ".join(pal)


def ruas_bairros(ementa: str) -> tuple[list[str], list[str]]:
    # casa sem acento, mas devolve o trecho com a grafia original (mesmas posições:
    # tirar o acento de um caractere composto não muda o tamanho do texto)
    orig = unicodedata.normalize("NFC", re.sub(r"\s+", " ", ementa)).lower()
    e = sem_acento(orig)
    if len(e) != len(orig):
        orig = e

    def trecho(m, g):
        return orig[m.start(g):m.end(g)]

    ruas = []
    for m in RUA_RX.finditer(e):
        chave = _expande(f"{m.group(1)} {m.group(2)}".strip(" .-"))
        if (len(chave.split()) >= 2 and not RUA_GENERICA.search(chave)
                and not re.search(r"\b(municipio|cidade|toda|todas|diversas|varias)\b", chave)):
            ruas.append(_bonito(_expande(f"{trecho(m, 1)} {trecho(m, 2)}".strip(" .-"))))
    bairros = []
    for rx in (BAIRRO_RX, BAIRRO_RX2):
        for m in rx.finditer(e):
            b = _expande(m.group(1).strip(" .-"))
            if NAO_BAIRRO.search(b) or len(b) < 4:
                continue
            b = _bonito(_expande(trecho(m, 1).strip(" .-")))
            if b not in bairros and not any(norm(b) in norm(r) for r in ruas):
                bairros.append(b)
    return list(dict.fromkeys(ruas)), bairros


# ------------------------------------------------------------------ montagem
def analisar(propostas: list[dict], vereadores: list[dict], sessoes: list[dict]) -> dict:
    por_chave = {v["chave"]: v for v in vereadores}
    por_chave.update({chave_nome(v["nome"]): v for v in vereadores if v.get("nome")})

    def achar(autor: str):
        k = chave_nome(autor)
        if k in por_chave:
            return por_chave[k]
        # "Abidan Henrique da Silva" -> "Abidan Henrique"
        cands = [v for ck, v in por_chave.items() if k.startswith(ck + " ")]
        return max(cands, key=lambda v: len(v["chave"])) if cands else None

    autores_sem_vereador = Counter()
    for it in propostas:
        it["grupo"] = grupo(it["tipo"], it["ementa"])
        it["tema"] = tema(it["ementa"]) if it["grupo"] in "bc" else ""
        it["ruas"], it["bairros"] = ruas_bairros(it["ementa"])
        ids = []
        for a in it["autores"]:
            v = achar(a)
            if v:
                ids.append(v["id"])
            else:
                autores_sem_vereador[a] += 1
        it["vereadores"] = ids

    # pedidos repetidos: mesma rua + mesmo assunto, só indicações
    grupos = defaultdict(list)
    for it in propostas:
        if it["grupo"] == "b" and it["tema"]:
            for r in it["ruas"]:
                grupos[(chave_nome(r), it["tema"])].append(it)
    repetidos = []
    for (_, th), itens in grupos.items():
        if len(itens) < 3:
            continue
        itens.sort(key=lambda x: x["data"], reverse=True)
        bairro = Counter(b for x in itens for b in x["bairros"]).most_common(1)
        repetidos.append({
            "rua": itens[0]["ruas"][0] if itens[0]["ruas"] else "",
            "bairro": bairro[0][0] if bairro else "",
            "tema": th, "n": len(itens),
            "n_vereadores": len({v for x in itens for v in x["vereadores"]}),
            "de": itens[-1]["data"], "ate": itens[0]["data"],
            "ids": [x["id"] for x in itens],
        })
    repetidos.sort(key=lambda g: (-g["n"], -g["n_vereadores"]))

    # mesma localidade com grafias diferentes ("São Luiz"/"Sao Luiz"): conta junto e mostra
    # a grafia mais usada, preferindo a acentuada
    grafias = defaultdict(Counter)
    for it in propostas:
        for b in it["bairros"]:
            grafias[chave_nome(b)][b] += 1
    canon = {k: max(c.items(), key=lambda x: (x[0] != sem_acento(x[0]), x[1]))[0] for k, c in grafias.items()}
    for it in propostas:
        it["bairros"] = list(dict.fromkeys(canon[chave_nome(b)] for b in it["bairros"]))
    for g in repetidos:
        if g["bairro"]:
            g["bairro"] = canon.get(chave_nome(g["bairro"]), g["bairro"])
    bairros = Counter({canon[k]: sum(c.values()) for k, c in grafias.items()})

    # números por vereador
    est = {v["id"]: {"cat": Counter(), "P": 0, "F": 0, "sessoes": 0, "sim": 0, "nao": 0, "abst": 0,
                     "outros_votos": Counter(), "naos": []} for v in vereadores}
    for it in propostas:
        for vid in it["vereadores"]:
            est[vid]["cat"][it["grupo"]] += 1

    n_vot = unanimes = 0
    valores_voto = Counter()
    sem_registro = []
    for s in sessoes:
        if not s.get("votacoes") and not s.get("presenca"):
            sem_registro.append({"data": s["data"], "titulo": s["titulo"]})
            continue
        votou = set()
        for vt in s.get("votacoes", []):
            if not vt["votos"]:
                continue
            n_vot += 1
            vals = [norm(v) for v in vt["votos"].values()]
            if len(set(x for x in vals if x not in ("---", ""))) <= 1:
                unanimes += 1
            for vid, voto in vt["votos"].items():
                vv = norm(voto)
                valores_voto[voto] += 1
                if vid not in est:
                    continue
                if vv == "sim":
                    est[vid]["sim"] += 1
                    votou.add(vid)
                elif vv in ("nao", "contra", "contrario"):
                    est[vid]["nao"] += 1
                    votou.add(vid)
                    est[vid]["naos"].append({"data": s["data"], "titulo": vt["titulo"], "voto": "nao"})
                elif vv.startswith("abst"):
                    est[vid]["abst"] += 1
                    votou.add(vid)
                    est[vid]["naos"].append({"data": s["data"], "titulo": vt["titulo"], "voto": "abstencao"})
                else:
                    est[vid]["outros_votos"][voto] += 1
        presentes = votou | {vid for vid, st in s.get("presenca", {}).items() if norm(st).startswith("presente")}
        # só conta vereadores que estavam no exercício (aparecem na lista de presença ou votaram)
        listados = set(s.get("presenca", {})) | votou
        for vid in listados:
            if vid in est:
                est[vid]["sessoes"] += 1
                if vid in presentes:
                    est[vid]["P"] += 1
                else:
                    est[vid]["F"] += 1

    # em exercício = aparece na lista de presença ou votou na sessão mais recente com registro
    ultima = next((s for s in sorted(sessoes, key=lambda x: x["data"], reverse=True)
                   if s.get("presenca") or s.get("votacoes")), None)
    em_exercicio = set()
    if ultima:
        em_exercicio = set(ultima.get("presenca", {})) | {vid for vt in ultima.get("votacoes", []) for vid in vt["votos"]}

    for v in vereadores:
        v["em_exercicio"] = v["id"] in em_exercicio if ultima else None
        e = est[v["id"]]
        v.update({"cat": dict(e["cat"]), "P": e["P"], "F": e["F"], "sessoes": e["sessoes"],
                  "sim": e["sim"], "nao": e["nao"], "abst": e["abst"],
                  "outros_votos": dict(e["outros_votos"]), "naos": e["naos"]})

    return {
        "catot": dict(Counter(it["grupo"] for it in propostas)),
        "tipos": dict(Counter(it["tipo"] for it in propostas)),
        "temas": dict(Counter(it["tema"] for it in propostas if it["tema"])),
        "bairros": bairros.most_common(80),
        "repetidos": repetidos,
        "n_votacoes": n_vot,
        "unanimes": unanimes,
        "valores_voto": dict(valores_voto),
        "sessoes_sem_registro": sem_registro,
        "autores_sem_vereador": dict(autores_sem_vereador.most_common(30)),
    }
