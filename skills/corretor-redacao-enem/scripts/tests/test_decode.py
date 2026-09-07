# -*- coding: utf-8 -*-
"""Autoteste do decodificador de subset font das Cartilhas do Participante.

Os textos esperados foram conferidos contra o render em imagem das páginas 16,
28, 32, 35 e 39 da Cartilha 2025. As entradas são os bytes crus que o pymupdf
devolve para aqueles spans (capturados de oficial/pdfs/cartilha_2025.pdf).
"""
import importlib.util, pathlib, sys
sys.stdout.reconfigure(encoding="utf-8")
_r = pathlib.Path(__file__).resolve().parents[1]      # .../scripts
_s = importlib.util.spec_from_file_location("dc", _r / "tools" / "decode_cartilha.py")
dc = importlib.util.module_from_spec(_s); _s.loader.exec_module(dc)

# Fonte #2 (deslocamento uniforme +29) — descritores de 80 e 40 pontos da Competência I
CASOS_F2 = [
    ("'HPRQVWUD\x03GRPtQLR\x03LQVX\u00bfFLHQWH\x03GD\x03PRGDOLGDGH\x03HVFULWD\x03IRUPDO\x03GD\x03OtQJXD\x03",
     "Demonstra dom\u00ednio insuficiente da modalidade escrita formal da l\u00edngua "),
    ("SRUWXJXHVD\x0f\x03GH\x03IRUPD\x03VLVWHPiWLFD\x0f\x03FRP\x03GLYHUVL\u00bfFDGRV\x03H\x03IUHTXHQWHV\x03GHVYLRV\x03",
     "portuguesa, de forma sistem\u00e1tica, com diversificados e frequentes desvios "),
    ("FRPHQWDP\x03DYDQoRV\x03H\x03GL\u00bfFXOGDGHV", "comentam avan\u00e7os e dificuldades"),
]

# Fonte #1 (0x01 espaço, 0x02..0x1B maiúsculas, 0x1C..0x35 minúsculas)
CASOS_F1 = [
    ("\x2b\x2a\x2d\u012f\x28", "por\u00e9m"),
    ("\x1e\x2a\x29\x2e\x20\x2c\x30\u0130\x29\x1e\x24\x1c", "consequ\u00eancia"),
    ("\u0477\u0479\u047c", "025"),
]

def main():
    falhas = []
    for raw, esperado in CASOS_F2:
        got = dc.decode_f2(raw)
        if got != esperado: falhas.append(("f2", esperado, got))
    for raw, esperado in CASOS_F1:
        got = dc.decode(raw)
        if got != esperado: falhas.append(("f1", esperado, got))
    for tag, esperado, got in falhas:
        print(f"FALHOU {tag}\n  esperado: {esperado!r}\n  obtido:   {got!r}")
    total = len(CASOS_F1) + len(CASOS_F2)
    print(f"{total - len(falhas)}/{total} casos OK")
    return 1 if falhas else 0

if __name__ == "__main__":
    sys.exit(main())
