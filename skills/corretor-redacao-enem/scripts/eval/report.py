# -*- coding: utf-8 -*-
"""Aplica os portões de aprovação sobre os resultados de uma rodada.

    python skills/corretor-redacao-enem/scripts/eval/report.py results/v1/

Portões:

  A  Teto            — o corretor não pune texto excelente.
  B  Discriminação   — a competência degradada cai, cai mais quanto pior a
                       degradação, e as outras ficam paradas.
  C  Concordância    — QWK por competência contra rótulo humano com variância.
  D  Estabilidade    — mesma redação, execuções repetidas, mesma nota.
  E  Calibração      — a média do corretor não infla frente à humana.

O portão A sozinho é insuficiente por construção: num conjunto só de redações
nota 1.000 a estratégia ótima é devolver 1.000 sempre, com 100% de acerto. O
portão B existe exatamente para reprovar esse corretor.

O portão C exige um conjunto com variância no rótulo humano — que o material
oficial do Inep não oferece. Sem `essaybr_test.jsonl` ele é reportado como NÃO
EXECUTADO, nunca como aprovado.
"""
import argparse, json, pathlib, sys, importlib.util

_r = pathlib.Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("mt", _r / "metrics.py")
mt = importlib.util.module_from_spec(_s); _s.loader.exec_module(mt)

COMPS = ["c1", "c2", "c3", "c4", "c5"]

BARRAS = {
    "A_frac_alta": 0.90,      # competências em 200 ou 160
    "A_total_min": 900,
    "B_frac_queda": 0.85,     # ablações em que o alvo cai ao menos um nível
    "B_spearman": -0.80,      # monotonicidade em C1 e C5
    "B_frac_especifica": 0.80,
    "B_folga_colateral": 40,  # pontos que uma não-alvo pode se mexer
    "C_qwk": 0.70,
    "C_mae": 40,
    "D_frac_identica": 0.85,
    "D_desvio_total": 40,
    "E_delta_media": 20,
}


def ler(caminho):
    p = pathlib.Path(caminho)
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if p.exists() else None


def nota(reg, comp):
    v = reg.get("notas", {}).get(comp)
    return v.get("nota") if isinstance(v, dict) else None


def spearman(xs, ys):
    """Correlação de postos. Amostras pequenas, empates tratados por posto médio."""
    def postos(v):
        ordem = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(ordem):
            j = i
            while j + 1 < len(ordem) and v[ordem[j + 1]] == v[ordem[i]]:
                j += 1
            media = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[ordem[k]] = media
            i = j + 1
        return r
    if len(xs) < 3:
        return None
    rx, ry = postos(xs), postos(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    return num / (dx * dy) if dx and dy else None


# --------------------------------------------------------------------------
def portao_a(oficial):
    """Teto: nas redações que o Inep declarou nota 1.000, o corretor não deve
    punir. Só entram as edições que publicam a nota — a Cartilha 2025 não
    publica nenhuma e por isso fica de fora."""
    if not oficial:
        return {"estado": "NAO EXECUTADO", "motivo": "sem results/oficial.jsonl"}
    rotuladas = [r for r in oficial if str(r["id"])[:4] in ("2022", "2023", "2024")]
    if not rotuladas:
        return {"estado": "NAO EXECUTADO", "motivo": "nenhuma redação rotulada"}
    altas = total = 0
    totais_ok = 0
    for r in rotuladas:
        notas = [nota(r, c) for c in COMPS]
        if any(n is None for n in notas):
            continue
        altas += sum(1 for n in notas if n >= 160)
        total += len(notas)
        totais_ok += 1 if sum(notas) >= BARRAS["A_total_min"] else 0
    frac = altas / total if total else 0
    ok = frac >= BARRAS["A_frac_alta"] and totais_ok == len(rotuladas)
    return {"estado": "PASSOU" if ok else "REPROVOU", "n": len(rotuladas),
            "frac_160_ou_200": round(frac, 3),
            "totais_acima_de_900": f"{totais_ok}/{len(rotuladas)}",
            "nota": "sozinho, este portão aprovaria um corretor que devolve 1.000 sempre"}


def portao_b(ablacoes):
    """Discriminação: sensibilidade, monotonicidade e especificidade."""
    if not ablacoes:
        return {"estado": "NAO EXECUTADO", "motivo": "sem results/ablacoes.jsonl"}
    bases = {r["base_id"]: r for r in ablacoes if r.get("alvo") is None}
    caiu = comparadas = 0
    especificas = checadas = 0
    series = {"c1": {}, "c5": {}}
    for r in ablacoes:
        alvo = r.get("alvo")
        if not alvo:
            continue
        base = bases.get(r["base_id"])
        if not base:
            continue
        n_alvo, n_base = nota(r, alvo), nota(base, alvo)
        if n_alvo is not None and n_base is not None:
            comparadas += 1
            caiu += 1 if n_alvo < n_base else 0
            if alvo in series:
                series[alvo].setdefault(r["base_id"], []).append((r["severidade"], n_alvo))
        for c in COMPS:
            if c == alvo or c in r.get("colaterais_esperados", []):
                continue
            a, b = nota(r, c), nota(base, c)
            if a is None or b is None:
                continue
            checadas += 1
            especificas += 1 if abs(a - b) <= BARRAS["B_folga_colateral"] else 0
    monot = {}
    for comp, porbase in series.items():
        rs = [spearman([s for s, _ in v], [n for _, n in v])
              for v in porbase.values() if len(v) >= 3]
        rs = [x for x in rs if x is not None]
        monot[comp] = round(sum(rs) / len(rs), 3) if rs else None
    f_caiu = caiu / comparadas if comparadas else 0
    f_esp = especificas / checadas if checadas else 0
    ok = (f_caiu >= BARRAS["B_frac_queda"] and f_esp >= BARRAS["B_frac_especifica"]
          and all(m is not None and m <= BARRAS["B_spearman"] for m in monot.values()))
    return {"estado": "PASSOU" if ok else "REPROVOU", "ablacoes": comparadas,
            "frac_alvo_caiu": round(f_caiu, 3),
            "frac_nao_alvo_estavel": round(f_esp, 3),
            "spearman_severidade_nota": monot}


def portao_c(essaybr):
    """Concordância por redação. Exige rótulo humano COM variância."""
    if not essaybr:
        return {"estado": "NAO EXECUTADO",
                "motivo": "sem results/essaybr_test.jsonl — nenhum conjunto oficial "
                          "do Inep tem variância no rótulo, então este portão não "
                          "pode ser executado só com material oficial"}
    pares = {}
    for c in COMPS:
        h = [r["humano"][c] for r in essaybr if r.get("humano") and nota(r, c) is not None]
        m = [nota(r, c) for r in essaybr if r.get("humano") and nota(r, c) is not None]
        pares[c] = (h, m)
    res = mt.resumo(pares)
    ok = all(v["qwk"] is not None and v["qwk"] >= BARRAS["C_qwk"]
             and v["mae"] <= BARRAS["C_mae"] for v in res.values())
    return {"estado": "PASSOU" if ok else "REPROVOU", "por_competencia": res,
            "leitura": "concordância com corretores humanos treinados na matriz do "
                       "Inep — NÃO é concordância com o Inep"}


def portao_d(execucoes):
    if len(execucoes) < 2:
        return {"estado": "NAO EXECUTADO",
                "motivo": "test-retest exige ao menos dois arquivos retest*.jsonl"}
    ids = [r["id"] for r in execucoes[0]]
    por_comp, totais = {}, []
    for c in COMPS:
        series = []
        for ex in execucoes:
            mapa = {r["id"]: nota(r, c) for r in ex}
            series.append([mapa.get(i) for i in ids])
        validos = [i for i in range(len(ids)) if all(s[i] is not None for s in series)]
        if not validos:
            continue
        por_comp[c] = mt.estabilidade([[s[i] for i in validos] for s in series])
    for ex in execucoes:
        mapa = {r["id"]: sum(nota(r, c) or 0 for c in COMPS) for r in ex}
        totais.append([mapa.get(i, 0) for i in ids])
    est_total = mt.estabilidade(totais)
    ok = (all(v["identicas"] >= BARRAS["D_frac_identica"] for v in por_comp.values())
          and est_total["desvio_medio"] <= BARRAS["D_desvio_total"])
    return {"estado": "PASSOU" if ok else "REPROVOU", "execucoes": len(execucoes),
            "por_competencia": {k: round(v["identicas"], 3) for k, v in por_comp.items()},
            "desvio_medio_total": round(est_total["desvio_medio"], 1)}


def portao_e(essaybr):
    if not essaybr:
        return {"estado": "NAO EXECUTADO", "motivo": "sem results/essaybr_test.jsonl"}
    fora = {}
    for c in COMPS:
        h = [r["humano"][c] for r in essaybr if r.get("humano") and nota(r, c) is not None]
        m = [nota(r, c) for r in essaybr if r.get("humano") and nota(r, c) is not None]
        if h:
            fora[c] = round(sum(m) / len(m) - sum(h) / len(h), 1)
    ok = all(abs(v) <= BARRAS["E_delta_media"] for v in fora.values())
    return {"estado": "PASSOU" if ok else "REPROVOU", "delta_media_modelo_menos_humano": fora}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("diretorio")
    a = ap.parse_args()
    d = pathlib.Path(a.diretorio)

    oficial = ler(d / "oficial.jsonl")
    ablacoes = ler(d / "ablacoes.jsonl")
    essaybr = ler(d / "essaybr_test.jsonl")
    execucoes = [x for x in (ler(d / "dev.jsonl"),) if x]
    execucoes += [ler(p) for p in sorted(d.glob("dev_retest*.jsonl"))]

    portoes = {
        "A - teto (redações nota 1.000 do Inep)": portao_a(oficial),
        "B - discriminação (ablações controladas)": portao_b(ablacoes),
        "C - concordância (QWK por competência)": portao_c(essaybr),
        "D - estabilidade (test-retest)": portao_d(execucoes),
        "E - calibração (inflação de média)": portao_e(essaybr),
    }
    largura = 78
    for nome, r in portoes.items():
        print("=" * largura)
        print(f"{r['estado']:<14} {nome}")
        for k, v in r.items():
            if k != "estado":
                print(f"   {k}: {v}")
    print("=" * largura)
    reprovou = [n for n, r in portoes.items() if r["estado"] == "REPROVOU"]
    nao_exec = [n for n, r in portoes.items() if r["estado"] == "NAO EXECUTADO"]
    print(f"reprovados: {len(reprovou)} | não executados: {len(nao_exec)}")
    if nao_exec:
        print("Portão não executado NÃO é portão aprovado.")
    return 1 if reprovou else 0


if __name__ == "__main__":
    sys.exit(main())
