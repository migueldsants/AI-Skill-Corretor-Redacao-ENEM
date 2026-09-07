# -*- coding: utf-8 -*-
"""Verifica que os portões fazem o que prometem.

O caso decisivo: um corretor que devolve 1.000 sempre, sem ler o texto, DEVE
passar no portão A (teto) e DEVE ser reprovado no portão B (discriminação).
Se o portão B não reprovar esse corretor, a suíte inteira não vale nada.
"""
import importlib.util, json, pathlib, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
SCRIPTS = pathlib.Path(__file__).resolve().parents[1]   # .../scripts
RAIZ = SCRIPTS.parents[2]                               # raiz do projeto
_s = importlib.util.spec_from_file_location("rp", SCRIPTS / "eval" / "report.py")
rp = importlib.util.module_from_spec(_s); _s.loader.exec_module(rp)

COMPS = rp.COMPS
# O dataset de ablações é derivado (não versionado): gera na primeira execução.
_DS = RAIZ / "datasets" / "ablacoes.jsonl"
if not _DS.exists():
    subprocess.run([sys.executable, str(SCRIPTS / "eval" / "ablate.py")],
                   cwd=RAIZ, check=True, capture_output=True)
ABL = [json.loads(l) for l in open(_DS, encoding="utf-8")]


def resultado(reg, notas):
    return {"id": reg["id"], "base_id": reg.get("base_id"), "alvo": reg.get("alvo"),
            "severidade": reg.get("severidade"),
            "colaterais_esperados": reg.get("colaterais_esperados", []),
            "notas": {c: {"nota": notas[c]} for c in COMPS}}


def corretor_preguicoso(reg):
    """Devolve 1.000 sempre, sem olhar o texto."""
    return {c: 200 for c in COMPS}


def corretor_sensivel(reg):
    """Enxerga a degradação: derruba a competência-alvo proporcionalmente à
    severidade e deixa as demais em 200."""
    notas = {c: 200 for c in COMPS}
    alvo = reg.get("alvo")
    if alvo:
        # a escala é por competência porque as severidades diferem entre elas
        # (C1 usa 3/8/20 desvios; as demais usam 1..4). Tem de ser monotônica.
        escalas = {
            "c1": {3: 160, 8: 120, 20: 40},
            "c2": {1: 160, 2: 80}, "c3": {1: 160, 2: 80}, "c4": {1: 160, 2: 80},
            "c5": {1: 160, 2: 120, 3: 80, 4: 0},
        }
        notas[alvo] = escalas[alvo][reg["severidade"]]
    return notas


def rodar(corretor):
    oficial = [resultado({"id": r["base_id"]}, corretor(r))
               for r in ABL if r.get("alvo") is None]
    ablacoes = [resultado(r, corretor(r)) for r in ABL]
    return rp.portao_a(oficial), rp.portao_b(ablacoes)


def main():
    falhas = []
    a_preg, b_preg = rodar(corretor_preguicoso)
    if a_preg["estado"] != "PASSOU":
        falhas.append(f"corretor preguiçoso deveria passar no portão A, deu {a_preg['estado']}")
    if b_preg["estado"] != "REPROVOU":
        falhas.append(f"corretor preguiçoso DEVERIA ser reprovado no portão B, "
                      f"deu {b_preg['estado']} — a suíte não discrimina nada")

    a_sen, b_sen = rodar(corretor_sensivel)
    if a_sen["estado"] != "PASSOU":
        falhas.append(f"corretor sensível deveria passar no portão A, deu {a_sen['estado']}")
    if b_sen["estado"] != "PASSOU":
        falhas.append(f"corretor sensível deveria passar no portão B, deu {b_sen['estado']} "
                      f"({b_sen})")

    # Portão sem dados nunca pode sair como aprovado.
    for nome, r in (("C", rp.portao_c(None)), ("D", rp.portao_d([])), ("E", rp.portao_e(None))):
        if r["estado"] != "NAO EXECUTADO":
            falhas.append(f"portão {nome} sem dados deveria ser NAO EXECUTADO")

    for f in falhas:
        print("FALHOU", f)
    print(f"preguiçoso: A={a_preg['estado']} B={b_preg['estado']} "
          f"(alvo caiu em {b_preg['frac_alvo_caiu']:.0%})")
    print(f"sensível:   A={a_sen['estado']} B={b_sen['estado']} "
          f"(alvo caiu em {b_sen['frac_alvo_caiu']:.0%}, "
          f"não-alvo estável em {b_sen['frac_nao_alvo_estavel']:.0%})")
    print(f"{7 - len(falhas)}/7 verificações OK")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
