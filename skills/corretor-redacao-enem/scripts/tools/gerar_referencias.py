# -*- coding: utf-8 -*-
"""Gera skill/.../references/competencia-N.md a partir da Cartilha do Participante.

Reproduzível: lê o PDF oficial, decodifica os subsets de fonte e recorta as
tabelas de níveis de desempenho. Os seis descritores de cada competência foram
conferidos contra o render em imagem das páginas 16, 28, 32, 35 e 39.

Uso:  python skills/corretor-redacao-enem/scripts/tools/gerar_referencias.py \n          oficial/pdfs/cartilha_2025.pdf 2025
"""
import sys, re, pathlib, importlib.util

_r = pathlib.Path(__file__).resolve().parent
SKILL = _r.parents[1]          # skills/corretor-redacao-enem
_s = importlib.util.spec_from_file_location("ex", _r / "extrair_cartilha.py")
ex = importlib.util.module_from_spec(_s); _s.loader.exec_module(ex)

NIVEIS = [200, 160, 120, 80, 40, 0]
ROMANOS = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}

COMPETENCIAS = {
    1: dict(pagina=16, titulo="Demonstrar domínio da modalidade escrita formal "
                              "da língua portuguesa"),
    2: dict(pagina=28, titulo="Compreender a proposta de redação e aplicar conceitos "
                              "das várias áreas de conhecimento para desenvolver o tema "
                              "dentro dos limites estruturais do texto dissertativo-"
                              "argumentativo em prosa"),
    3: dict(pagina=32, titulo="Selecionar, relacionar, organizar e interpretar "
                              "informações, fatos, opiniões e argumentos em defesa de "
                              "um ponto de vista"),
    4: dict(pagina=35, titulo="Demonstrar conhecimento dos mecanismos linguísticos "
                              "necessários para a construção da argumentação"),
    5: dict(pagina=39, titulo="Elaborar proposta de intervenção para o problema "
                              "abordado, respeitando os direitos humanos"),
}

# Rótulo de pontuação. Pode vir em uma linha ("80 pontos") ou em duas ("200"
# seguido de "pontos"), e — na tabela da Competência IV — DEPOIS do descritor
# a que se refere. Por isso o pareamento não usa adjacência: usa a ordem dos
# parágrafos, que é sempre 200 -> 0 de cima para baixo.
ROTULO = re.compile(r"^\s*(200|160|120|80|40|0)(\s+pontos?)?\s*$")
ORFAO = re.compile(r"^\s*pontos?\s*$")
ABERTURA = re.compile(r"O quadro a seguir apresenta os seis n\u00edveis")
FIM = re.compile(r"^\s*\d\.\d\s+(COMPET\u00caNCIA|RECOMENDA)", re.I)


def recortar_tabela(texto_pagina):
    linhas = texto_pagina.splitlines()
    # A frase de abertura ocupa duas linhas ("...que serão utilizados / para
    # avaliar a Competência N nas redações do Enem AAAA."). Avança até a linha
    # em branco seguinte, senão o rabo da frase vira o descritor de 200.
    ini = 0
    for i, l in enumerate(linhas):
        if ABERTURA.search(l):
            ini = i + 1
            while ini < len(linhas) and linhas[ini].strip():
                ini += 1
            break
    fim = len(linhas)
    for i in range(ini, len(linhas)):
        if FIM.match(linhas[i]):
            fim = i; break

    rotulos, paragrafos, atual = [], [], []
    for l in linhas[ini:fim]:
        m = ROTULO.match(l)
        if m:
            rotulos.append(int(m.group(1)))
            if atual: paragrafos.append(" ".join(atual)); atual = []
            continue
        if ORFAO.match(l):
            if atual: paragrafos.append(" ".join(atual)); atual = []
            continue
        if l.strip():
            atual.append(l.strip())
        elif atual:
            paragrafos.append(" ".join(atual)); atual = []
    if atual: paragrafos.append(" ".join(atual))

    paragrafos = [re.sub(r"\s+", " ", p).strip() for p in paragrafos if len(p.strip()) > 25]
    if sorted(set(rotulos), reverse=True) != NIVEIS:
        print(f"  AVISO: rótulos encontrados {sorted(set(rotulos), reverse=True)}",
              file=sys.stderr)
    if len(paragrafos) != 6:
        print(f"  AVISO: {len(paragrafos)} parágrafos de descritor (esperado 6)",
              file=sys.stderr)
    return list(zip(NIVEIS, paragrafos))


def main():
    pdf, ano = sys.argv[1], sys.argv[2]
    paginas = dict(ex.extrair(pdf))
    dest = SKILL / "references"
    dest.mkdir(parents=True, exist_ok=True)
    for n, meta in COMPETENCIAS.items():
        tabela = recortar_tabela(paginas[meta["pagina"]])
        L = [f"# Competência {ROMANOS[n]}", "",
             f"> {meta['titulo']}", "",
             f"Fonte: *A Redação do Enem {ano} — Cartilha do(a) Participante* (Inep), "
             f"p. {meta['pagina']} do PDF. Descritores transcritos literalmente.", "",
             "## Níveis de desempenho", ""]
        for nota, desc in tabela:
            L += [f"### {nota} {'ponto' if nota == 0 else 'pontos'}", "", desc, ""]
        (dest / f"competencia-{n}.md").write_text("\n".join(L), encoding="utf-8")
        print(f"  competencia-{n}.md: {len(tabela)}/6 níveis")
    return 0


if __name__ == "__main__":
    sys.exit(main())
