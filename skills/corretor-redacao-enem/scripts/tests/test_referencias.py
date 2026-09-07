# -*- coding: utf-8 -*-
"""Regressão dos descritores oficiais.

Os trechos abaixo foram lidos no render em imagem das páginas 16, 28, 32, 35 e
39 da Cartilha do Participante 2025. Este teste trava aquela conferência visual:
qualquer mudança no extrator que desalinhe as tabelas quebra aqui.
"""
import pathlib, sys, re
sys.stdout.reconfigure(encoding="utf-8")
REF = pathlib.Path(__file__).resolve().parents[1].parent / "references"

ESPERADO = {
    1: {200: "Demonstra excelente domínio da modalidade escrita formal",
        80:  "Demonstra domínio insuficiente da modalidade escrita formal",
        40:  "Demonstra domínio precário da modalidade escrita formal",
        0:   "Demonstra desconhecimento da modalidade escrita formal"},
    2: {200: "Desenvolve o tema por meio de argumentação consistente, a partir de um",
        80:  "Desenvolve o tema recorrendo à cópia de trechos dos textos motivadores",
        0:   "Fuga ao tema/não atendimento à estrutura dissertativo-argumentativa"},
    3: {200: "Apresenta informações, fatos e opiniões relacionados ao tema proposto",
        80:  "Apresenta informações, fatos e opiniões relacionados ao tema, mas",
        0:   "Apresenta informações, fatos e opiniões não relacionados ao tema"},
    4: {200: "Articula bem as partes do texto e apresenta repertório diversificado",
        40:  "Articula as partes do texto de forma precária",
        0:   "Não articula as informações"},
    5: {200: "Elabora muito bem proposta de intervenção, detalhada",
        40:  "Apresenta proposta de intervenção vaga, precária ou relacionada apenas",
        0:   "Não apresenta proposta de intervenção"},
}

def descritor(md, nota):
    rot = f"### {nota} ponto" + ("" if nota == 0 else "s")
    return md.split(rot)[1].split("###")[0].strip()

def main():
    falhas = 0
    for comp, casos in ESPERADO.items():
        md = (REF / f"competencia-{comp}.md").read_text(encoding="utf-8")
        if len(re.findall(r"^### ", md, re.M)) != 6:
            print(f"FALHOU C{comp}: não são 6 níveis"); falhas += 1
        for nota, inicio in casos.items():
            obtido = descritor(md, nota)
            if not obtido.startswith(inicio):
                falhas += 1
                print(f"FALHOU C{comp} nível {nota}\n  esperado começar com: {inicio!r}"
                      f"\n  obtido:               {obtido[:len(inicio) + 20]!r}")
    n = sum(len(v) for v in ESPERADO.values())
    print(f"{n - falhas}/{n} descritores conferem com o render oficial")
    return 1 if falhas else 0

if __name__ == "__main__":
    sys.exit(main())
