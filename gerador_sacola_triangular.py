#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de faca - SACOLA TRIANGULAR
Versão 2.0  –  Primacor

Gera SVG e PDF em escala 1:1 (unidades em mm).
O projeto fechado é definido por:
  A  = largura da frente/trás da sacola  (mm)
  B  = largura do lado                   (mm)
  H  = altura da sacola                  (mm)

Todas as outras medidas derivam automaticamente ou podem ser ajustadas.

PEÇAS
  1) CORPO  – tira única com 5 painéis: aba | frente(A) | lado(B) | trás(A) | aba
              as duas abas (B/2 cada) formam o 2º lado e levam as aberturas da alça.
  2) FUNDO  – duas peças identicas espelhadas (separadas por linha de corte central),
              cada uma com aba de cola, vincos diagonais e aba superior.

CORES
  corte   = CMYK 0/100/100/0  (vermelho)
  vinco   = CMYK 100/0/100/0  (verde)
  moldura = CMYK 0/50/50/50   (cinza-bege, limite da chapa)

USO
  python gerador_sacola_triangular.py                             # medidas padrão
  python gerador_sacola_triangular.py --A 350 --B 180 --H 420
  python gerador_sacola_triangular.py --A 350 --B 180 --H 420 --saida minha_sacola
  python gerador_sacola_triangular.py --help

Dependência: pip install reportlab   (SVG gerado mesmo sem ela)
"""

from __future__ import annotations
import argparse
import sys
import math
from dataclasses import dataclass, field, fields

# ---------------------------------------------------------------------------
# Constantes globais
# ---------------------------------------------------------------------------
K = 0.5523            # constante de Bézier para quarto de círculo
LINE_MM = 1 / 72 * 25.4   # 1 pt ≈ 0.3528 mm

CORES: dict = {
    "corte":   {"cmyk": (0, 1, 1, 0),              "rgb": "#ED1C24"},
    "vinco":   {"cmyk": (1, 0, 1, 0),              "rgb": "#00A651"},
    "moldura": {"cmyk": (0, 0.502, 0.502, 0.498),  "rgb": "#804040"},
    "texto":   {"cmyk": (0, 0, 0, 1),              "rgb": "#000000"},
}

TXT_W   = 22.5   # largura "COLA" (mm)
TXT_CAP = 10.0   # altura cap (mm)
TXT_FS  = 13.93  # corpo da fonte (mm)


# ---------------------------------------------------------------------------
# Parâmetros
# ---------------------------------------------------------------------------
@dataclass
class Params:
    # ── PROJETO FECHADO ────────────────────────────────────────────────────
    A: float = 300.0        # largura frente/trás  (mm)
    B: float = 150.0        # largura do lado       (mm)
    H: float = 400.0        # altura da sacola      (mm)

    # ── ALÇA ───────────────────────────────────────────────────────────────
    aba: float | None = None      # largura de cada aba das alças  (padrão B/2)
    raio: float = 25.0            # raio dos cantos externos das abas
    alca_larg: float = 25.0       # largura da abertura da alça
    alca_alt: float = 90.0        # altura da abertura da alça

    # ── FUNDO ──────────────────────────────────────────────────────────────
    # Se fundo_auto=True, todas as medidas do fundo são calculadas a partir
    # de A, B, H usando proporções do original. Caso queira controle total,
    # passe fundo_auto=False e informe cada medida.
    fundo_auto: bool = True

    fundo_larg: float | None = None       # largura total de cada peça do fundo
    fundo_dobra_larg: float | None = None # comprimento do vinco horizontal superior
    fundo_cintura: float | None = None    # largura entre vincos diagonais na linha central
    fundo_dobra_y: float | None = None    # altura do vinco horizontal
    fundo_aba_alt: float | None = None    # altura da aba superior (acima do vinco)
    fundo_aba_recuo: float | None = None  # recuo lateral da aba superior
    ombro_y: float | None = None          # altura do "ombro"
    lado_x: float | None = None           # x do vinco lateral no ombro
    lado_y0: float | None = None          # y onde o vinco lateral encosta na borda
    cola_y: float | None = None           # altura do corte da borda lateral
    cola_x: float | None = None           # x do recorte da aba de cola

    # ── PÁGINA / MOLDURA ───────────────────────────────────────────────────
    margem: float = 30.0
    raio_moldura: float = 5.0
    espaco: float = 22.8        # espaço horizontal entre as duas molduras
    margem_pagina: float = 20.0
    moldura: bool = True

    def __post_init__(self) -> None:
        if self.aba is None:
            self.aba = self.B / 2

        if self.fundo_auto:
            # ── Proporções derivadas do original (A=300, B=150, H=400) ──
            # Referência: fundo_larg=320, dobra=150, cintura=60 → escala por B
            escB = self.B / 150.0
            escA = self.A / 300.0
            escH = self.H / 400.0

            if self.fundo_larg is None:
                self.fundo_larg = round(self.A + self.B / 3 * 2 + 20 * escB, 2)
            if self.fundo_dobra_larg is None:
                self.fundo_dobra_larg = round(self.B * escB, 2)
            if self.fundo_cintura is None:
                self.fundo_cintura = round(60.0 * escB, 2)
            if self.fundo_dobra_y is None:
                self.fundo_dobra_y = round(180.0 * escH, 2)
            if self.fundo_aba_alt is None:
                self.fundo_aba_alt = round(15.0 * escH, 2)
            if self.fundo_aba_recuo is None:
                self.fundo_aba_recuo = round(11.72 * escB, 2)
            if self.ombro_y is None:
                self.ombro_y = round(165.0 * escH, 2)
            if self.lado_x is None:
                self.lado_x = round(73.29 * escA, 2)
            if self.lado_y0 is None:
                self.lado_y0 = round(71.13 * escH, 2)
            if self.cola_y is None:
                self.cola_y = round(155.66 * escH, 2)
            if self.cola_x is None:
                self.cola_x = round(37.37 * escA, 2)
        else:
            # Preenche defaults originais para campos não fornecidos
            defaults = dict(
                fundo_larg=320.0, fundo_dobra_larg=150.0, fundo_cintura=60.0,
                fundo_dobra_y=180.0, fundo_aba_alt=15.0, fundo_aba_recuo=11.72,
                ombro_y=165.0, lado_x=73.29, lado_y0=71.13,
                cola_y=155.66, cola_x=37.37,
            )
            for attr, val in defaults.items():
                if getattr(self, attr) is None:
                    setattr(self, attr, val)


# ---------------------------------------------------------------------------
# Primitivas geométricas
# ---------------------------------------------------------------------------
def rounded_rect(x, y, w, h, r):
    return [
        ("M",  x + r,         y),
        ("L",  x + w - r,     y),
        ("C",  x + w - r + K*r, y,       x + w, y + r - K*r,       x + w, y + r),
        ("L",  x + w,         y + h - r),
        ("C",  x + w, y + h - r + K*r,   x + w - r + K*r, y + h,   x + w - r, y + h),
        ("L",  x + r,         y + h),
        ("C",  x + r - K*r,   y + h,     x, y + h - r + K*r,       x,     y + h - r),
        ("L",  x,             y + r),
        ("C",  x, y + r - K*r, x + r - K*r, y,                     x + r, y),
        ("Z",),
    ]


def obround(cx, cy, w, h):
    """Retângulo com extremos semicirculares (alça)."""
    r = w / 2
    s = (h - w) / 2
    return [
        ("M",  cx - r, cy - s),
        ("L",  cx - r, cy + s),
        ("C",  cx - r,   cy + s + K*r, cx - K*r, cy + s + r, cx,   cy + s + r),
        ("C",  cx + K*r, cy + s + r,   cx + r,   cy + s + K*r, cx + r, cy + s),
        ("L",  cx + r, cy - s),
        ("C",  cx + r,   cy - s - K*r, cx + K*r, cy - s - r, cx,   cy - s - r),
        ("C",  cx - K*r, cy - s - r,   cx - r,   cy - s - K*r, cx - r, cy - s),
        ("Z",),
    ]


def polyline(pts):
    return [("M",) + tuple(pts[0])] + [("L",) + tuple(p) for p in pts[1:]]


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------
def validar(p: Params) -> None:
    erros = []
    for nome in ("A", "B", "H", "aba", "raio", "alca_larg", "alca_alt"):
        if getattr(p, nome) <= 0:
            erros.append(f"{nome} deve ser > 0")
    if p.raio > min(p.aba, p.H / 2):
        erros.append("raio maior que a aba ou metade da altura")
    if p.alca_larg >= p.aba:
        erros.append("abertura da alça mais larga que a aba")
    if p.alca_alt > p.H - 2 * p.raio:
        erros.append("abertura da alça alta demais para a altura da sacola")
    if p.alca_alt < p.alca_larg:
        erros.append("alca_alt deve ser >= alca_larg")
    if p.fundo_dobra_larg >= p.fundo_larg:
        erros.append("vinco horizontal do fundo maior que a largura do fundo")
    if p.fundo_cintura >= p.fundo_larg:
        erros.append("cintura do fundo maior que a largura do fundo")
    if erros:
        sys.exit("Erro nos parâmetros:\n  - " + "\n  - ".join(erros))


# ---------------------------------------------------------------------------
# Construção das peças
# ---------------------------------------------------------------------------
def construir(p: Params):
    validar(p)
    itens: list[dict] = []

    # ── Layout de página ────────────────────────────────────────────────────
    Wb = p.aba + p.A + p.B + p.A + p.aba          # largura total do corpo
    base_meia = p.fundo_dobra_y + p.fundo_aba_alt  # meia-altura do fundo
    m  = p.margem
    mp = p.margem_pagina

    bx  = mp + m                                   # corpo: canto inf-esq
    by  = mp + m
    xf_base = mp + Wb + 2*m + p.espaco             # fundo: canto esq moldura
    x0  = xf_base + m                              # fundo: x0 das peças
    cy  = mp + m + base_meia                        # fundo: linha de corte central (y)

    PW = xf_base + p.fundo_larg + 2*m + mp
    PH = 2*mp + max(p.H + 2*m, 2*base_meia + 2*m)

    def add(layer, cmds):
        itens.append({"layer": layer, "cmds": cmds})

    # ── Molduras ────────────────────────────────────────────────────────────
    if p.moldura:
        add("moldura", rounded_rect(mp, mp, Wb + 2*m, p.H + 2*m, p.raio_moldura))
        add("moldura", rounded_rect(xf_base, mp,
                                    p.fundo_larg + 2*m, 2*base_meia + 2*m,
                                    p.raio_moldura))

    # ── PEÇA 1: CORPO ───────────────────────────────────────────────────────
    r = p.raio
    # Contorno externo com cantos arredondados
    add("corte", [
        ("M",  bx + r,       by),
        ("L",  bx + Wb - r,  by),
        ("C",  bx + Wb - r + K*r, by,       bx + Wb, by + r - K*r,       bx + Wb, by + r),
        ("L",  bx + Wb,      by + p.H - r),
        ("C",  bx + Wb, by + p.H - r + K*r, bx + Wb - r + K*r, by + p.H, bx + Wb - r, by + p.H),
        ("L",  bx + r,       by + p.H),
        ("C",  bx + r - K*r, by + p.H,      bx, by + p.H - r + K*r,     bx, by + p.H - r),
        ("L",  bx,           by + r),
        ("C",  bx, by + r - K*r,             bx + r - K*r, by,           bx + r, by),
        ("Z",),
    ])

    # Vincos verticais (separação dos painéis)
    for xv in (p.aba, p.aba + p.A, p.aba + p.A + p.B, p.aba + 2*p.A + p.B):
        add("vinco", polyline([(bx + xv, by), (bx + xv, by + p.H)]))

    # Aberturas das alças (obround centrado verticalmente)
    cyb = by + p.H / 2
    add("corte", obround(bx + p.aba / 2,       cyb, p.alca_larg, p.alca_alt))
    add("corte", obround(bx + Wb - p.aba / 2,  cyb, p.alca_larg, p.alca_alt))

    # ── PEÇA 2: FUNDO (2 espelhados) ────────────────────────────────────────
    W   = p.fundo_larg
    fx0 = (W - p.fundo_dobra_larg) / 2    # x início do vinco horizontal
    wx0 = (W - p.fundo_cintura) / 2       # x do vinco diagonal na linha central
    fy  = p.fundo_dobra_y
    ty  = fy + p.fundo_aba_alt

    for s in (1, -1):   # s=1 → metade de cima, s=-1 → metade de baixo
        def P(u, v, _s=s):
            return (x0 + u, cy + _s * v)

        contorno = [
            P(0,                              0),
            P(0,                              p.cola_y),
            P(p.cola_x,                       p.ombro_y),
            # P(p.lado_x, p.ombro_y) removido: pertence só ao vinco, não ao corte
            P(fx0,                            fy),
            P(fx0 + p.fundo_aba_recuo,        ty),
            P(W - fx0 - p.fundo_aba_recuo,    ty),
            P(W - fx0,                        fy),
            # P(W - p.lado_x, p.ombro_y) removido: pertence só ao vinco, não ao corte
            P(W - p.cola_x,                   p.ombro_y),
            P(W,                              p.cola_y),
            P(W,                              0),
        ]
        add("corte", polyline(contorno))

        # Vincos diagonais e horizontal
        add("vinco", polyline([P(wx0, 0), P(fx0, fy)]))
        add("vinco", polyline([P(W - wx0, 0), P(W - fx0, fy)]))
        add("vinco", polyline([P(fx0, fy), P(W - fx0, fy)]))

        # Vincos laterais da aba de cola
        add("vinco", polyline([P(0,     p.lado_y0), P(p.lado_x,     p.ombro_y)]))
        add("vinco", polyline([P(W,     p.lado_y0), P(W - p.lado_x, p.ombro_y)]))

        # Texto "COLA"
        tx_u = p.cola_x * 0.6
        ty_v = p.cola_y - 16
        for u in (tx_u, W - tx_u):
            gx, gy = P(u, ty_v)
            itens.append({
                "layer": "texto", "texto": "COLA",
                "cx": gx, "cy": gy,
                "rot": 0 if s == 1 else 180,
            })

    # Linha de corte central (divide as 2 peças do fundo)
    add("corte", polyline([(x0, cy), (x0 + W, cy)]))

    return itens, PW, PH


# ---------------------------------------------------------------------------
# Saída SVG
# ---------------------------------------------------------------------------
def escrever_svg(itens, PW, PH, caminho):
    ordem = ["moldura", "corte", "vinco", "texto"]
    nomes = {"moldura": "MOLDURA", "corte": "CORTE", "vinco": "VINCO", "texto": "TEXTO"}

    linhas = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{PW:.3f}mm" height="{PH:.3f}mm" '
        f'viewBox="0 0 {PW:.3f} {PH:.3f}">',
        f'<rect width="{PW:.3f}" height="{PH:.3f}" fill="#ffffff"/>',
    ]

    for layer in ordem:
        grupo = [i for i in itens if i["layer"] == layer]
        if not grupo:
            continue
        rgb = CORES[layer]["rgb"]

        if layer == "texto":
            linhas.append(
                f'<g id="{nomes[layer]}" fill="{rgb}" '
                f'font-family="Helvetica, Arial, sans-serif">'
            )
            for it in grupo:
                cx, cy = it["cx"], PH - it["cy"]
                base   = cy + TXT_CAP / 2
                rot_attr = (f' transform="rotate({it["rot"]} {cx:.3f} {cy:.3f})"'
                            if it["rot"] else "")
                linhas.append(
                    f'<text x="{cx:.3f}" y="{base:.3f}" '
                    f'font-size="{TXT_FS}" text-anchor="middle" '
                    f'textLength="{TXT_W}" lengthAdjust="spacingAndGlyphs"'
                    f'{rot_attr}>{it["texto"]}</text>'
                )
            linhas.append("</g>")
            continue

        linhas.append(
            f'<g id="{nomes[layer]}" fill="none" stroke="{rgb}" '
            f'stroke-width="{LINE_MM:.4f}" stroke-linejoin="miter" stroke-linecap="butt">'
        )
        for it in grupo:
            d = []
            for c in it["cmds"]:
                if c[0] in ("M", "L"):
                    d.append(f'{c[0]}{c[1]:.3f} {PH - c[2]:.3f}')
                elif c[0] == "C":
                    d.append(
                        f'C{c[1]:.3f} {PH - c[2]:.3f} '
                        f'{c[3]:.3f} {PH - c[4]:.3f} '
                        f'{c[5]:.3f} {PH - c[6]:.3f}'
                    )
                else:
                    d.append("Z")
            linhas.append(f'<path d="{" ".join(d)}"/>')
        linhas.append("</g>")

    linhas.append("</svg>")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")


# ---------------------------------------------------------------------------
# Saída PDF
# ---------------------------------------------------------------------------
def escrever_pdf(itens, PW, PH, caminho):
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.colors import CMYKColor
        from reportlab.lib.units import mm
        from reportlab.pdfbase.pdfmetrics import stringWidth
    except ImportError:
        print("⚠  PDF não gerado – instale com:  pip install reportlab")
        return False

    c = rl_canvas.Canvas(caminho, pagesize=(PW * mm, PH * mm))
    c.setTitle("Faca - Sacola Triangular | Primacor")
    c.setCreator("gerador_sacola_triangular.py v2")
    c.setAuthor("Primacor")
    c.scale(mm, mm)
    c.setLineWidth(LINE_MM)
    c.setLineJoin(0)
    c.setLineCap(0)

    for layer in ("moldura", "corte", "vinco", "texto"):
        cor = CMYKColor(*CORES[layer]["cmyk"])
        for it in (i for i in itens if i["layer"] == layer):
            if layer == "texto":
                c.saveState()
                c.setFillColor(cor)
                c.translate(it["cx"], it["cy"])
                c.rotate(it["rot"])
                t = c.beginText()
                t.setFont("Helvetica", TXT_FS)
                nat = stringWidth(it["texto"], "Helvetica", TXT_FS)
                t.setHorizScale(100 * TXT_W / nat)
                t.setTextOrigin(-TXT_W / 2, -TXT_CAP / 2)
                t.textOut(it["texto"])
                c.drawText(t)
                c.restoreState()
                continue

            c.setStrokeColor(cor)
            path = c.beginPath()
            for cmd in it["cmds"]:
                if cmd[0] == "M":
                    path.moveTo(cmd[1], cmd[2])
                elif cmd[0] == "L":
                    path.lineTo(cmd[1], cmd[2])
                elif cmd[0] == "C":
                    path.curveTo(*cmd[1:])
                else:
                    path.close()
            c.drawPath(path, stroke=1, fill=0)

    c.showPage()
    c.save()
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
HELP_MAP = {
    "A":                 "largura das faces frente/trás (mm)  ─ PROJETO FECHADO",
    "B":                 "largura do lado (mm)  ─ PROJETO FECHADO",
    "H":                 "altura da sacola (mm)  ─ PROJETO FECHADO",
    "aba":               "largura de cada aba da alça (padrão: B/2)",
    "raio":              "raio dos cantos arredondados das abas",
    "alca_larg":         "largura da abertura da alça",
    "alca_alt":          "altura da abertura da alça",
    "fundo_larg":        "largura total de cada peça do fundo",
    "fundo_dobra_larg":  "comprimento do vinco horizontal do fundo",
    "fundo_cintura":     "largura entre vincos diagonais na linha central",
    "fundo_dobra_y":     "altura do vinco horizontal do fundo",
    "fundo_aba_alt":     "altura da aba superior do fundo",
    "fundo_aba_recuo":   "recuo lateral da aba superior",
    "ombro_y":           "altura do ombro da aba de cola",
    "lado_x":            "x do vinco lateral no ombro",
    "lado_y0":           "y inicial do vinco lateral na borda",
    "cola_y":            "altura do corte na borda lateral",
    "cola_x":            "x do recorte da aba de cola",
    "margem":            "margem entre peça e moldura",
    "raio_moldura":      "raio dos cantos da moldura",
    "espaco":            "espaço horizontal entre as duas molduras",
    "margem_pagina":     "margem da página",
}

SKIP = {"fundo_auto", "moldura"}


def main():
    ap = argparse.ArgumentParser(
        description="Gerador de faca – Sacola Triangular (medidas em mm)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python gerador_sacola_triangular.py --A 350 --B 180 --H 420
  python gerador_sacola_triangular.py --A 300 --B 150 --H 400 --saida faca_padrao
  python gerador_sacola_triangular.py --A 250 --B 120 --H 350 --sem-moldura --so-svg
        """,
    )
    for f in fields(Params):
        if f.name in SKIP:
            continue
        ap.add_argument(f"--{f.name.replace('_', '-')}", dest=f.name,
                        type=float, default=None,
                        help=HELP_MAP.get(f.name, ""))
    ap.add_argument("--sem-moldura",   action="store_true", help="omitir moldura da chapa")
    ap.add_argument("--fundo-manual",  action="store_true",
                    help="desativar cálculo automático do fundo (usar valores padrão do original)")
    ap.add_argument("--so-svg",        action="store_true", help="gerar apenas o SVG")
    ap.add_argument("--saida", default="sacola_triangular",
                    help="prefixo dos arquivos de saída (sem extensão)")

    a = ap.parse_args()

    kw: dict = {}
    for f in fields(Params):
        if f.name in SKIP:
            continue
        v = getattr(a, f.name, None)
        if v is not None:
            kw[f.name] = v

    if a.fundo_manual:
        kw["fundo_auto"] = False

    p = Params(**kw)
    if a.sem_moldura:
        p.moldura = False

    # Resumo
    print("=" * 55)
    print("  GERADOR DE FACA – SACOLA TRIANGULAR  |  Primacor")
    print("=" * 55)
    print(f"  Projeto: A={p.A} mm  B={p.B} mm  H={p.H} mm")
    print(f"  Aba alça: {p.aba:.1f} mm   Alça: {p.alca_larg}×{p.alca_alt} mm")
    print(f"  Fundo: {p.fundo_larg:.1f} × {2*(p.fundo_dobra_y+p.fundo_aba_alt):.1f} mm")
    print("-" * 55)

    itens, PW, PH = construir(p)

    svg_path = a.saida + ".svg"
    escrever_svg(itens, PW, PH, svg_path)
    print(f"  SVG → {svg_path}")
    print(f"  Página: {PW:.1f} × {PH:.1f} mm")

    if not a.so_svg:
        pdf_path = a.saida + ".pdf"
        ok = escrever_pdf(itens, PW, PH, pdf_path)
        if ok:
            print(f"  PDF → {pdf_path}")

    print("=" * 55)


if __name__ == "__main__":
    main()
