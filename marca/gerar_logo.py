"""Gera a marca do Radar Embu (PNG) com Pillow.

Marca: um radar de tela (anéis + varredura) à esquerda; à direita "RADAR" em tinta e
"EMBU" em terracota (cor das cerâmicas e do barro de Embu das Artes), com "DAS ARTES"
empilhado ao lado. Fonte: Archivo Black (SIL Open Font License).

Saída em site/: logo.png, logo-branco.png, favicon.png, apple-touch-icon.png, og.png
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
FONTE = str(RAIZ / "marca" / "fontes" / "ArchivoBlack-Regular.ttf")
SAIDA = RAIZ / "site"
TINTA = (17, 20, 24, 255)
TERRA = (224, 83, 47, 255)       # terracota
TERRA_CLARA = (224, 83, 47, 70)
BRANCO = (255, 255, 255, 255)
S = 4  # superamostragem para bordas suaves


def radar(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, tinta, destaque, fundo_varredura):
    """Tela de radar: varredura em leque, dois anéis, cruz discreta, centro e um ponto detectado."""
    # varredura (leque) de -100° a -40°
    d.pieslice([cx - r, cy - r, cx + r, cy + r], start=-100, end=-40, fill=fundo_varredura)
    d.pieslice([cx - r, cy - r, cx + r, cy + r], start=-46, end=-40, fill=destaque)
    w = max(2, r // 7)
    for rr in (r, int(r * 0.62)):
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=tinta, width=w)
    c = int(r * 0.17)
    d.ellipse([cx - c, cy - c, cx + c, cy + c], fill=tinta)
    # ponto detectado
    bx, by, br = cx + int(r * 0.42), cy - int(r * 0.58), int(r * 0.13)
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=destaque)


def texto_largura(fonte, t):
    x0, _, x1, _ = fonte.getbbox(t)
    return x1 - x0


def logo(tinta, destaque, nome: str, varredura=None):
    H = 380 * S
    f_grande = ImageFont.truetype(FONTE, 150 * S)
    f_peq = ImageFont.truetype(FONTE, 54 * S)
    wr = texto_largura(f_grande, "RADAR")
    r = 150 * S
    pad = 10 * S
    x_txt = pad + 2 * r + 34 * S
    w2 = texto_largura(f_grande, "EMBU") + 22 * S + texto_largura(f_peq, "ARTES")
    W = x_txt + max(wr, w2) + pad
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radar(d, pad + r, H // 2, r, tinta, destaque, varredura or (destaque[0], destaque[1], destaque[2], 60))
    # linha 1: RADAR
    asc = f_grande.getbbox("RADAR")[1]
    y1 = 18 * S
    d.text((x_txt, y1 - asc), "RADAR", font=f_grande, fill=tinta)
    # linha 2: EMBU + DAS/ARTES empilhado
    y2 = y1 + 172 * S
    d.text((x_txt, y2 - asc), "EMBU", font=f_grande, fill=destaque)
    we = texto_largura(f_grande, "EMBU")
    xs = x_txt + we + 22 * S
    asc_p = f_peq.getbbox("DAS")[1]
    altura_maiusc = f_grande.getbbox("E")[3] - f_grande.getbbox("E")[1]
    d.text((xs, y2 + 6 * S - asc_p), "DAS", font=f_peq, fill=tinta)
    d.text((xs, y2 + altura_maiusc - 54 * S * 0.72 - asc_p + 2 * S), "ARTES", font=f_peq, fill=tinta)
    img = img.resize((W // S, H // S), Image.LANCZOS)
    img = img.crop(img.getbbox())
    img.save(SAIDA / nome)
    return img


def icone(tamanho: int, nome: str, fundo=None):
    T = tamanho * S
    img = Image.new("RGBA", (T, T), fundo or (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if fundo:
        d.rounded_rectangle([0, 0, T - 1, T - 1], radius=T // 5, fill=fundo)
    r = int(T * (0.36 if fundo else 0.46))
    cor = BRANCO if fundo else TINTA
    radar(d, T // 2, T // 2, r, cor, TERRA, (TERRA[0], TERRA[1], TERRA[2], 90))
    img.resize((tamanho, tamanho), Image.LANCZOS).save(SAIDA / nome)


def og():
    W, H = 1200, 630
    img = Image.new("RGBA", (W, H), (250, 247, 243, 255))
    lg = Image.open(SAIDA / "logo.png")
    esc = 860 / lg.width
    lg = lg.resize((860, int(lg.height * esc)), Image.LANCZOS)
    img.alpha_composite(lg, ((W - lg.width) // 2, 120))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONTE, 40)
    t = "O que cada vereador fez, contado todo dia"
    d.text(((W - texto_largura(f, t)) // 2, 120 + lg.height + 60), t, font=f, fill=TINTA)
    img.convert("RGB").save(SAIDA / "og.png", quality=92)


if __name__ == "__main__":
    SAIDA.mkdir(exist_ok=True)
    logo(TINTA, TERRA, "logo.png")
    logo(BRANCO, TERRA, "logo-branco.png", varredura=(255, 255, 255, 50))
    icone(64, "favicon.png", fundo=TINTA)
    icone(180, "apple-touch-icon.png", fundo=TINTA)
    icone(512, "icone-512.png", fundo=TINTA)
    og()
    print("ok")
