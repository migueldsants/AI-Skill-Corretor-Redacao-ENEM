# -*- coding: utf-8 -*-
"""Integridade do corpus oficial extraído das Cartilhas do Participante.

Pega as regressões que já apareceram uma vez: comentário do avaliador vazando
para dentro da redação (ordem de blocos do PDF), títulos de seção virando nome
de participante e rótulo de nota atribuído a edição que não o publica.
"""
import json, pathlib, sys, re
sys.stdout.reconfigure(encoding="utf-8")
RED = pathlib.Path(__file__).resolve().parents[4] / "oficial" / "redacoes"

# A Cartilha 2025 abandonou a seção "Amostra de redações NOTA 1.000": diz apenas
# que as redações "receberam boas notas" e não publica nota nenhuma.
ROTULADAS = {2022, 2023, 2024}
ESPERADO_POR_ANO = {2022: 7, 2023: 10, 2024: 10, 2025: 10}

# Um texto dissertativo-argumentativo de até 30 linhas manuscritas.
MIN_PALAVRAS, MAX_PALAVRAS = 200, 700
INICIO_DE_COMENTARIO = re.compile(
    r"(A|O) (participante|reda\u00e7\u00e3o|texto) (demonstra|apresenta)"
    r"|COMENT\u00c1RIO", re.I)


def main():
    arquivos = sorted(RED.glob("*.json"))
    if not arquivos:
        # O corpus é derivado dos PDFs e não é versionado (é texto de redação
        # real). Regere antes de testar.
        print("FALHOU corpus ausente em", RED)
        print("  gere com: python .../scripts/tools/extrair_redacoes.py "
              "oficial/pdfs/cartilha_<ano>.pdf <ano>")
        return 1
    reds = [json.loads(a.read_text(encoding="utf-8")) for a in arquivos]
    falhas = []

    for ano, esperado in ESPERADO_POR_ANO.items():
        obtido = sum(1 for r in reds if r["cartilha_ano"] == ano)
        if obtido != esperado:
            falhas.append(f"cartilha {ano}: {obtido} redações, esperado {esperado}")

    for r in reds:
        id_ = r["id"]
        pal = len(r["texto"].split())
        if not MIN_PALAVRAS <= pal <= MAX_PALAVRAS:
            falhas.append(f"{id_}: {pal} palavras, fora de [{MIN_PALAVRAS},{MAX_PALAVRAS}]")
        if INICIO_DE_COMENTARIO.search(r["texto"]):
            falhas.append(f"{id_}: comentário do avaliador vazou para dentro da redação")
        if len(r["comentario_inep"]) < 500:
            falhas.append(f"{id_}: comentário do Inep ausente ou truncado")
        rotulada = r["cartilha_ano"] in ROTULADAS
        if r["rotulo_oficial"] != rotulada:
            falhas.append(f"{id_}: rotulo_oficial={r['rotulo_oficial']}, esperado {rotulada}")
        if rotulada and r["notas"] != {"c1": 200, "c2": 200, "c3": 200,
                                       "c4": 200, "c5": 200, "total": 1000}:
            falhas.append(f"{id_}: notas != 1.000 em edição rotulada")
        if not rotulada and r["notas"] is not None:
            falhas.append(f"{id_}: nota atribuída a edição que não publica nota")
        if not r["tema"]:
            falhas.append(f"{id_}: sem tema")

    for f in falhas:
        print("FALHOU", f)
    print(f"{len(reds)} redações verificadas, {len(falhas)} problemas")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
