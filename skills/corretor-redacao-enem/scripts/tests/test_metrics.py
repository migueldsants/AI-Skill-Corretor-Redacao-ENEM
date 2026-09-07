# -*- coding: utf-8 -*-
"""Casos do kappa quadrático calculados à mão, mais o caso degenerado."""
import importlib.util, pathlib, sys
sys.stdout.reconfigure(encoding="utf-8")
_r = pathlib.Path(__file__).resolve().parents[1]      # .../scripts
_s = importlib.util.spec_from_file_location("mt", _r / "eval" / "metrics.py")
mt = importlib.util.module_from_spec(_s); _s.loader.exec_module(mt)

def quase(a, b, tol=1e-9):
    return a is not None and abs(a - b) < tol

CASOS = [
    ("concordância perfeita", [0, 40, 200], [0, 40, 200], 1.0),
    ("inversão total",        [0, 40, 80],  [80, 40, 0], -1.0),
    ("acaso puro",            [0, 0, 40, 40], [0, 40, 0, 40], 0.0),
]

def main():
    falhas = []
    for nome, a, b, esperado in CASOS:
        got = mt.qwk(a, b)
        if not quase(got, esperado):
            falhas.append(f"{nome}: esperado {esperado}, obtido {got}")

    # O caso que motivou todo o desenho: gabarito constante (só nota 1.000).
    # O kappa é indefinido, e devolver 0 esconderia que a métrica não mede nada.
    for modelo in ([200] * 5, [0, 40, 80, 120, 200]):
        if mt.qwk([200] * 5, modelo) is not None:
            falhas.append("gabarito constante deveria devolver None")

    if not quase(mt.mae([200, 160], [160, 160]), 20.0):
        falhas.append("mae errado")
    if not quase(mt.dentro_de_um_nivel([200, 200], [160, 80]), 0.5):
        falhas.append("dentro_de_um_nivel errado")
    est = mt.estabilidade([[200, 160], [200, 120], [200, 160]])
    if not quase(est["identicas"], 0.5):
        falhas.append(f"estabilidade errada: {est}")

    try:
        mt.qwk([200, 150], [200, 200]); falhas.append("aceitou nota fora da escala")
    except ValueError:
        pass

    for f in falhas: print("FALHOU", f)
    print(f"{len(CASOS) + 5 - len(falhas)}/{len(CASOS) + 5} verificações OK")
    return 1 if falhas else 0

if __name__ == "__main__":
    sys.exit(main())
