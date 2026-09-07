# -*- coding: utf-8 -*-
"""Extrai as redações comentadas das Cartilhas do Participante para JSON.

Cada arquivo em oficial/redacoes/ traz o texto da redação, o comentário oficial
do(a) avaliador(a) e a procedência. As notas por competência só são preenchidas
quando a Cartilha as declara — o que vale para as edições cuja seção se chama
"Amostra de redações NOTA 1.000" (2022, 2023, 2024). A Cartilha 2025 diz apenas
que as redações "receberam boas notas" e NÃO publica nota alguma; essas entram
com `notas: null` e `rotulo_oficial: false`.

Uso:  python skills/corretor-redacao-enem/scripts/tools/extrair_redacoes.py \n          oficial/pdfs/cartilha_2024.pdf 2024
"""
import sys, re, json, unicodedata, pathlib, importlib.util

_r = pathlib.Path(__file__).resolve().parent
RAIZ = _r.parents[3]           # raiz do projeto
_s = importlib.util.spec_from_file_location("ex", _r / "extrair_cartilha.py")
ex = importlib.util.module_from_spec(_s); _s.loader.exec_module(ex)

ENEM_DA_CARTILHA = {2022: 2021, 2023: 2022, 2024: 2023, 2025: 2024}
RUIDO = ("AMOSTRA", "REDA", "COMPET", "ENEM", "CARTILHA", "MATRIZ", "SUM",
         "PARTICIPANTE", "ATEN", "RECOMENDA", "INSTRU", "TEMA", "PROPOSTA")

CAB_NUMERADO = re.compile(r"^\s*\d{1,2}\.\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ'’]+"
                          r"(?:\s+[A-Za-zÀ-ÿ'’]+){1,6})\s*$")
CAB_CAIXA_ALTA = re.compile(r"^\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿ'’\- ]{10,60})\s*$")

def _ruidoso(nome):
    return (any(r in nome.upper() for r in RUIDO)
            or any(c.isdigit() for c in nome)
            or not 2 <= len(nome.split()) <= 6)


def eh_nome(linha):
    m = CAB_NUMERADO.match(linha)
    if m:
        nome = m.group(1).strip()
        return None if _ruidoso(nome) else nome
    m = CAB_CAIXA_ALTA.match(linha)
    if m:
        nome = m.group(1).strip()
        if _ruidoso(nome):
            return None
        return " ".join(p.capitalize() for p in nome.split())
    return None

def slug(txt):
    t = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")

def secao_amostra(paginas):
    """Devolve (texto_da_secao, pagina_inicial, rotulada_nota_1000)."""
    ini = None
    for n in sorted(paginas):
        if "Para esta Cartilha, foram selecionadas" in paginas[n]:
            ini = n; break
    if ini is None:
        raise SystemExit("não achei a abertura da amostra de redações")
    corpo = "\n".join(paginas[n] for n in sorted(paginas) if n >= ini)
    plano = re.sub(r"\s+", " ", corpo)
    rotulada = bool(re.search(r"pontua\w+ m\w+xima\s*[-–—]\s*1\.000 pontos", plano)
                    or re.search(r"AMOSTRA DE REDA\w*ES NOTA 1\.000", plano))
    return corpo, ini, rotulada

# Tema de cada edição. Cada string foi conferida por busca no texto extraído da
# própria Cartilha correspondente (tools/extrair_cartilha.py). Não é digitação
# de memória. A Cartilha 2022 traz também uma camada de 4pt com o enunciado
# corrompido ("resgistro cilvil") — defeito do PDF do Inep; a forma correta
# aparece nos spans de corpo maior do mesmo documento.
TEMAS = {
    2021: "Invisibilidade e registro civil: garantia de acesso à cidadania no Brasil",
    2022: "Desafios para a valorização de comunidades e povos tradicionais no Brasil",
    2023: "Desafios para o enfrentamento da invisibilidade do trabalho de cuidado "
          "realizado pela mulher no Brasil",
    2024: "Desafios para a valorização da herança africana no Brasil",
}

def tema(enem_ano):
    return TEMAS[enem_ano]

def partir(corpo):
    """Sequência alternada: cabeçalho de nome, redação, COMENTÁRIO."""
    linhas = corpo.splitlines()
    marcas = []
    for i, l in enumerate(linhas):
        nome = eh_nome(l)
        if nome:                              marcas.append((i, "nome", nome))
        elif l.strip().upper().startswith("COMENT"): marcas.append((i, "com", None))
    saida, atual = [], None
    for k, (i, tipo, nome) in enumerate(marcas):
        fim = marcas[k + 1][0] if k + 1 < len(marcas) else len(linhas)
        bloco = "\n".join(linhas[i + 1:fim]).strip()
        if tipo == "nome":
            if atual: saida.append(atual)
            atual = dict(autor=nome, texto=bloco, comentario="")
        elif atual is not None and not atual["comentario"]:
            atual["comentario"] = bloco
        elif atual is not None:
            atual["comentario"] += "\n\n" + bloco
    if atual: saida.append(atual)
    return saida

def main():
    pdf, ano = sys.argv[1], int(sys.argv[2])
    paginas = dict(ex.extrair(pdf))
    corpo, p0, rotulada = secao_amostra(paginas)
    t = tema(ENEM_DA_CARTILHA[ano])
    dest = RAIZ / "oficial" / "redacoes"; dest.mkdir(parents=True, exist_ok=True)
    n_ok = 0
    for idx, red in enumerate(partir(corpo), 1):
        if len(red["texto"]) < 700:            # ruído, não é redação
            continue
        n_ok += 1
        reg = {
            "id": f"{ano}-{n_ok:02d}-{slug(red['autor'])}",
            "cartilha_ano": ano,
            "enem_ano": ENEM_DA_CARTILHA[ano],
            "autor": red["autor"],
            "tema": t,
            "texto": re.sub(r"\n{2,}", "\n\n", red["texto"]).strip(),
            "comentario_inep": re.sub(r"\n{2,}", "\n\n", red["comentario"]).strip(),
            "rotulo_oficial": rotulada,
            "notas": ({"c1": 200, "c2": 200, "c3": 200, "c4": 200, "c5": 200,
                       "total": 1000} if rotulada else None),
            "observacao": (None if rotulada else
                           "A Cartilha deste ano não publica as notas: declara apenas "
                           "que as redações receberam 'boas notas'. Sem rótulo, não "
                           "serve como gabarito."),
            "fonte": {"pdf": str(pathlib.Path(pdf).name), "secao_pagina_inicial": p0},
            "revisado_por": None,
            "data_revisao": None,
        }
        (dest / f"{reg['id']}.json").write_text(
            json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  cartilha {ano}: {n_ok} redações (rotulada nota 1.000: {rotulada}) | tema: {t}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
