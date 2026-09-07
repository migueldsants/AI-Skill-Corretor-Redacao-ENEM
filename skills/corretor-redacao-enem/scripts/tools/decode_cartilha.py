# -*- coding: utf-8 -*-
"""Decodifica o texto das Cartilhas do Participante (Inep).

Os PDFs embutem subsets de SourceSansPro sem ToUnicode válido em parte dos
spans. São dois mapeamentos, ambos derivados empiricamente e conferidos contra
o render em imagem das páginas (ver ../tests/test_decode.py):

  Fonte #1   0x01        -> espaço
             0x02..0x1B  -> 'A'..'Z'   (+63)
             0x1C..0x35  -> 'a'..'z'   (+69)
             U+0477..80  -> '0'..'9'   (Cartilha 2025)
             U+044B..54  -> '0'..'9'   (Cartilhas 2023/2024)
             restante    -> SYMBOLS (pontuação, acentuadas, ligaduras)

  Fonte #2   deslocamento uniforme de +29 sobre 0x03..0x5D
             (0x03 é espaço, 0x0F é vírgula); acentuadas em F2_ACENTOS.

Duas armadilhas tratadas aqui:

  1. Extrair sempre com get_text("rawdict", sort=True). Sem rawdict, o pymupdf
     insere espaços de layout indistinguíveis do glifo 'e'. Sem sort, a ordem
     é a do content stream, não a visual.
  2. Na fonte #1 o codepoint 0x20 é ambíguo — é a letra 'e' do subset e também
     o espaço sintetizado entre palavras. Separam-se pela LARGURA do glifo:
     'e' ocupa ~0.50x o corpo da fonte, o espaço ~0.18x (ver E_RATIO).
"""
import re

SYMBOLS = {
    # dígitos: um bloco contíguo por subset
    **{chr(0x0477 + i): str(i) for i in range(10)},
    **{chr(0x044B + i): str(i) for i in range(10)},
    # pontuação
    "\u0481": ".",  "\u0482": ",",  "\u0483": ":",  "\u0484": ";",
    "\u04A2": "(",  "\u04A3": ")",  "\u04A4": "\u201c", "\u04A5": "\u201d",
    "\u0498": "\u2013", "\u0496": "\u2013", "\u0497": "-", "\u06F3": "-",
    "\u048B": "\u2018", "\u048C": "\u2018", "\u048D": "\u2019",
    "\u048E": "\u201c", "\u048F": "\u201d",
    "\u0488": "?",  "\u0489": "!",  "\u04A8": "\u00ba", "\u067F": "\u00a7",
    # acentuadas
    "\u0107": "\u00e1", "\u0106": "\u00c1", "\u0109": "\u00e3", "\u0108": "\u00c3",
    "\u0124": "\u00e7", "\u0125": "\u00c7", "\u012F": "\u00e9", "\u012E": "\u00c9",
    "\u0130": "\u00ea", "\u0131": "\u00ca", "\u0151": "\u00ed", "\u0150": "\u00cd",
    "\u0177": "\u00f3", "\u0176": "\u00d3", "\u0179": "\u00f5", "\u0178": "\u00f4",
    "\u01AA": "\u00fa", "\u01AB": "\u00da",
    "\u00BF": "\u00e0", "\u00B3": "\u00e0", "\u00B4": "\u00e2",
    "\u00A8": "\u00d5", "\u00B1": "\u00e7",
    "\u00A6": "\u00d3", "\u00D9": "\u00da", "\u067D": "\u00aa",
    # ligaduras
    "\u07B2": "fi", "\u07B3": "fl", "\u0225": "ff",
}
UNKNOWN = "\ufffd"
E_RATIO = 0.32    # largura/corpo acima disso: o glifo 0x20 é a letra 'e'
RODAPE_PT = 60    # faixa inferior da página descartada (numeração e marca)


def decode_char(ch):
    o = ord(ch)
    if o == 0x01:          return " "
    if 0x02 <= o <= 0x1B:  return chr(o + 63)
    if 0x1C <= o <= 0x35:  return chr(o + 69)
    if ch in SYMBOLS:      return SYMBOLS[ch]
    if o < 0x80:           return ch
    return UNKNOWN


def is_scrambled(text):
    return bool(re.search(r"[\x01-\x08\x0b-\x1f]", text))


def decode(text):
    return "".join(decode_char(c) for c in text)


# --------------------------------------------------------------------------
# Fonte #2
# --------------------------------------------------------------------------
F2_ACENTOS = {
    "\u00bf": "fi", "\u00be": "fl",
    "t": "\u00ed", "i": "\u00e1", "o": "\u00e7", "n": "\u00e3",
    "m": "\u00e2", "p": "\u00e9", "q": "\u00ea",
    "y": "\u00f5", "x": "\u00f4", "s": "\u00f3", "z": "\u00fa",
}


def decode_f2(text):
    out = []
    for ch in text:
        o = ord(ch)
        if o == 0x20:           out.append(" ")
        elif 0x03 <= o <= 0x5D: out.append(chr(o + 29))
        elif ch in F2_ACENTOS:  out.append(F2_ACENTOS[ch])
        elif o < 0x80:          out.append(ch)
        else:                   out.append(UNKNOWN)
    return "".join(out)


def is_f2(text):
    """A fonte #1 nunca emite letras acima de 0x35; a #2 as usa o tempo todo.
    Três ou mais caracteres em 0x3E..0x5D junto com os controles do subset é
    assinatura suficiente e não colide com a fonte #1.

    LIMITAÇÃO CONHECIDA: a página que reproduz a folha de instruções da prova
    (p24 na Cartilha 2025) usa a fonte #2 com 0x20 como espaço, sem caracteres
    de controle, e não é capturada aqui — sai truncada. O conteúdo dela é
    redundante com a lista canônica de anulação, que extrai limpa.
    """
    if len(text) < 10:
        return False
    return (sum(1 for c in text if 0x3E <= ord(c) <= 0x5D) >= 3
            and any(0x01 <= ord(c) <= 0x1B for c in text))


# --------------------------------------------------------------------------
def _span_text(sp):
    raw = "".join(c["c"] for c in sp["chars"])
    if is_f2(raw):
        return decode_f2(raw)
    if not is_scrambled(raw):
        return raw
    size = sp.get("size") or 1.0
    out = []
    for c in sp["chars"]:
        ch = c["c"]
        if ord(ch) == 0x20:
            b = c["bbox"]
            out.append("e" if (b[2] - b[0]) / size > E_RATIO else " ")
        else:
            out.append(decode_char(ch))
    return "".join(out)


def page_text(page):
    """Texto da página na ordem de leitura, com os spans decodificados.

    Duas correções indispensáveis:

    - sort=True. A ordem do content stream não é a ordem visual: nas tabelas
      de descritores a pontuação da linha sai depois do seu texto, e no layout
      em página dupla das Cartilhas 2022/2023 o comentário do(a) avaliador(a)
      sai antes do cabeçalho da redação.
    - O rodapé é descartado por GEOMETRIA, não por expressão regular. Filtrar
      "\d{1,3}" para remover o número da página apagava junto as pontuações
      200/160/120/80/40 das tabelas de níveis.
    """
    limite = page.rect.height - RODAPE_PT
    out = []
    for bl in page.get_text("rawdict", sort=True)["blocks"]:
        if bl.get("bbox", (0, 0, 0, 0))[1] > limite:
            continue
        for ln in bl.get("lines", []):
            linha = "".join(_span_text(sp) for sp in ln.get("spans", []))
            if linha.strip():
                out.append(re.sub(r"[ \t]{2,}", " ", linha).rstrip())
        out.append("")
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
