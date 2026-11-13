"""Padroniza as fotos dos vereadores: fundo branco, rosto centralizado, 480x480.

Roda no ambiente .venv-fotos (Python 3.12), porque rembg/onnxruntime ainda não têm versão
para o Python do coletor:

    .venv-fotos\\Scripts\\python.exe marca\\padronizar_fotos.py

Origem de cada foto, nesta ordem:
  1. fotos_manuais/<nome do vereador>.<jpg|png|avif|webp>  (enviadas à mão; o nome do arquivo
     começa com o nome do vereador, como aparece no site ou na ficha)
  2. a foto da ficha no NoPaper (baixada para dados/cache/fotos_originais/)
Saída: site/fotos/<id>.jpg  e uma prancha de conferência em dados/cache/prancha_fotos.jpg
"""
from __future__ import annotations

import io
import json
import re
import sys
import unicodedata
from pathlib import Path

import cv2
import numpy as np
import pillow_avif  # noqa: F401  (registra AVIF em versões antigas do Pillow)
import requests
from PIL import Image, ImageDraw, ImageOps
from rembg import new_session, remove

RAIZ = Path(__file__).resolve().parent.parent
MANUAIS = RAIZ / "fotos_manuais"
ORIG = RAIZ / "dados" / "cache" / "fotos_originais"
SAIDA = RAIZ / "site" / "fotos"
LADO = 480
FUNDO = (255, 255, 255)


def chave(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", s.lower()).split() and " ".join(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())


def foto_manual(nomes: list[str]) -> Path | None:
    ks = [chave(n) for n in nomes if n]
    for p in sorted(MANUAIS.glob("*")):
        if p.suffix.lower() not in {".jpg", ".jpeg", ".png", ".avif", ".webp"}:
            continue
        kp = chave(p.stem)
        if any(kp == k or kp.startswith(k + " ") for k in ks):
            return p
    return None


def rosto(img: Image.Image, mascara: np.ndarray):
    """Maior rosto frontal (OpenCV Haar). Sem rosto: estima pelo topo da silhueta."""
    cinza = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    cls = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    menor = max(24, int(min(cinza.shape) * 0.12))
    faces = cls.detectMultiScale(cinza, scaleFactor=1.08, minNeighbors=6, minSize=(menor, menor))
    if len(faces):
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        return x + w / 2, y + h / 2, h
    ys, xs = np.nonzero(mascara > 128)
    if not len(ys):
        h, w = cinza.shape
        return w / 2, h * 0.35, h * 0.3
    topo = ys.min()
    altura = ys.max() - topo
    linha = xs[ys < topo + altura * 0.15]
    cx = float(np.median(linha)) if len(linha) else float(np.median(xs))
    fh = altura * 0.28
    return cx, topo + fh * 0.75, fh


def padronizar(origem: Image.Image, sessao) -> Image.Image:
    origem = ImageOps.exif_transpose(origem).convert("RGBA")
    # amplia fotos pequenas antes de recortar o fundo (melhora a borda)
    if max(origem.size) < 600:
        f = 600 / max(origem.size)
        origem = origem.resize((round(origem.width * f), round(origem.height * f)), Image.LANCZOS)
    recortada = remove(origem, session=sessao, post_process_mask=True)
    mascara = np.array(recortada.split()[-1])
    branco = Image.new("RGB", recortada.size, FUNDO)
    branco.paste(recortada, mask=recortada.split()[-1])
    cx, cy, fh = rosto(origem, mascara)
    # rosto ocupa ~38% da altura, olhos um pouco acima do centro, ombros visíveis
    lado = fh / 0.38
    topo = cy - lado * (0.5 - 0.32 * 0.38)  # centro do rosto a ~38% da altura do quadro
    # Se a foto original corta o corpo (silhueta encosta na borda de baixo) antes do fim do
    # quadro, o corte reto apareceria "flutuando". Nesse caso o quadro termina no corte:
    # o rosto fica um pouco maior, mas a base some na borda.
    ys = np.nonzero(mascara.max(axis=1) > 128)[0]
    if len(ys):
        base = ys.max()
        cortada = base >= mascara.shape[0] - 3
        if cortada and base < topo + lado - 2:
            lado = max((base - cy) / (1 - 0.40), fh * 2.2)  # mínimo: folga acima da cabeça
            topo = base - lado
    x0, y0 = cx - lado / 2, topo
    quadro = Image.new("RGB", (round(lado), round(lado)), FUNDO)
    quadro.paste(branco, (round(-x0), round(-y0)))
    return quadro.resize((LADO, LADO), Image.LANCZOS)


def main():
    d = json.loads((RAIZ / "dados" / "embu.json").read_text(encoding="utf-8"))
    ajustes = json.loads((RAIZ / "coletor" / "ajustes.json").read_text(encoding="utf-8")).get("nomes", {})
    sessao = new_session("u2net_human_seg")
    SAIDA.mkdir(parents=True, exist_ok=True)
    ORIG.mkdir(parents=True, exist_ok=True)
    so = set(sys.argv[1:])  # opcional: ids específicos
    feitas, prancha = [], []
    for v in d["vereadores"]:
        if so and v["id"] not in so:
            continue
        nomes = [ajustes.get(v["id"], ""), v["ap"], v.get("nome", "")]
        man = foto_manual(nomes)
        if man:
            img, fonte = Image.open(man), f"manual: {man.name}"
        elif v.get("foto"):
            p = ORIG / f"{v['id']}.img"
            if not p.exists():
                r = requests.get(v["foto"], timeout=60, headers={"User-Agent": "RadarEmbu/0.1"})
                r.raise_for_status()
                p.write_bytes(r.content)
            img, fonte = Image.open(io.BytesIO(p.read_bytes())), "ficha NoPaper"
        else:
            print(f"  sem foto: {v['ap']}")
            continue
        out = padronizar(img, sessao)
        out.save(SAIDA / f"{v['id']}.jpg", quality=88, optimize=True, progressive=True)
        feitas.append(v["id"])
        prancha.append((ajustes.get(v["id"]) or v["ap"], out))
        print(f"  ok: {v['ap']:<28} ({fonte})")
    if prancha:
        col = 6
        t = 200
        lin = (len(prancha) + col - 1) // col
        folha = Image.new("RGB", (col * t, lin * (t + 24)), (235, 235, 235))
        dr = ImageDraw.Draw(folha)
        for i, (nome, im) in enumerate(prancha):
            x, y = (i % col) * t, (i // col) * (t + 24)
            folha.paste(im.resize((t - 8, t - 8)), (x + 4, y + 4))
            dr.text((x + 6, y + t - 2), nome[:28], fill=(0, 0, 0))
        folha.save(RAIZ / "dados" / "cache" / "prancha_fotos.jpg", quality=85)
    print(f"{len(feitas)} fotos padronizadas em site/fotos/")


if __name__ == "__main__":
    main()
