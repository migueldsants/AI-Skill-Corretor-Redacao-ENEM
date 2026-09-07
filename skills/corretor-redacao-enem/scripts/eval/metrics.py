# -*- coding: utf-8 -*-
"""Métricas de concordância para correção de redação por competência.

Sem dependências externas: o kappa quadrático é curto e explícito o bastante
para não valer uma dependência, e a fórmula fica auditável aqui.

A escala do Enem tem seis níveis por competência: 0, 40, 80, 120, 160, 200.
Internamente tudo vira índice 0..5, que é o que a ponderação quadrática espera.
"""
import math
from collections import Counter

NIVEIS = [0, 40, 80, 120, 160, 200]
INDICE = {n: i for i, n in enumerate(NIVEIS)}
K = len(NIVEIS)


def para_indice(notas):
    fora = sorted({n for n in notas if n not in INDICE})
    if fora:
        raise ValueError(f"notas fora da escala do Enem: {fora}")
    return [INDICE[n] for n in notas]


def qwk(a, b):
    """Kappa de Cohen com ponderação quadrática.

    Devolve None quando é indefinido — o caso em que um dos avaliadores dá
    sempre a mesma nota. Aí a matriz esperada coincide com a observada e o
    kappa é 0 para QUALQUER corretor, do perfeito ao aleatório: o número não
    carrega informação e reportá-lo como 0 seria enganoso. É exatamente a
    situação de um conjunto só com redações nota 1.000.
    """
    if len(a) != len(b):
        raise ValueError("séries de tamanhos diferentes")
    ia, ib = para_indice(a), para_indice(b)
    n = len(ia)
    if n == 0:
        return None
    if len(set(ia)) == 1 or len(set(ib)) == 1:
        return None

    obs = [[0] * K for _ in range(K)]
    for x, y in zip(ia, ib):
        obs[x][y] += 1
    ma, mb = Counter(ia), Counter(ib)

    num = den = 0.0
    for i in range(K):
        for j in range(K):
            w = (i - j) ** 2 / (K - 1) ** 2
            num += w * obs[i][j]
            den += w * ma[i] * mb[j] / n
    return 1.0 - num / den if den else None


def mae(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a) if a else None


def acerto_exato(a, b):
    return sum(1 for x, y in zip(a, b) if x == y) / len(a) if a else None


def dentro_de_um_nivel(a, b):
    ia, ib = para_indice(a), para_indice(b)
    return sum(1 for x, y in zip(ia, ib) if abs(x - y) <= 1) / len(ia) if ia else None


def estabilidade(execucoes):
    """Test-retest. `execucoes` é uma lista de listas de notas, uma por rodada,
    todas na mesma ordem de redações. Devolve a fração de redações em que todas
    as rodadas deram a mesma nota e o desvio-padrão médio."""
    if len(execucoes) < 2:
        raise ValueError("test-retest exige ao menos duas execuções")
    n = len(execucoes[0])
    if any(len(e) != n for e in execucoes):
        raise ValueError("execuções de tamanhos diferentes")
    iguais = desvios = 0
    for i in range(n):
        vals = [e[i] for e in execucoes]
        if len(set(vals)) == 1:
            iguais += 1
        media = sum(vals) / len(vals)
        desvios += math.sqrt(sum((v - media) ** 2 for v in vals) / len(vals))
    return {"identicas": iguais / n, "desvio_medio": desvios / n}


def resumo(pares_por_competencia):
    """`pares_por_competencia`: {"c1": (humanas, modelo), ...}"""
    out = {}
    for comp, (h, m) in pares_por_competencia.items():
        out[comp] = {
            "n": len(h),
            "qwk": qwk(h, m),
            "mae": mae(h, m),
            "exato": acerto_exato(h, m),
            "ate_um_nivel": dentro_de_um_nivel(h, m),
            "media_humana": sum(h) / len(h) if h else None,
            "media_modelo": sum(m) / len(m) if m else None,
        }
    return out
