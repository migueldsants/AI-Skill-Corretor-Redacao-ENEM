# -*- coding: utf-8 -*-
"""Gera degradações controladas das redações oficiais, uma competência por vez.

Por que isto existe: sobre um conjunto em que o gabarito humano é constante
(as redações nota 1.000 da Cartilha), o kappa é indefinido e a estratégia ótima
é devolver 1.000 sempre — um teste feito só com elas aprovaria um corretor que
não lê o texto. As ablações criam a variância que falta sem sair do material
oficial: pega-se uma redação nota 1.000, degrada-se UMA competência de forma
determinística e verifica-se que a nota daquela competência cai, que cai mais
quanto pior a degradação, e que as demais ficam paradas.

Isso mede sensibilidade, monotonicidade e especificidade. NÃO mede calibração
absoluta contra o Inep — nada mede, porque essa base não existe.

Uso:  python skills/corretor-redacao-enem/scripts/eval/ablate.py \n          --entrada oficial/redacoes --saida datasets/ablacoes.jsonl
"""
import argparse, json, pathlib, re, sys

SEM_ACENTO = str.maketrans("áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ", "aaaaeeiooouucAAAAEEIOOOUUC")


def paragrafos(texto):
    return [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]


def frases(paragrafo):
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+", paragrafo) if f.strip()]


def juntar(paras):
    return "\n\n".join(p for p in paras if p.strip())


# --------------------------------------------------------------------------
# Competência I — desvios de norma-padrão
# --------------------------------------------------------------------------
TROCAS_C1 = [
    (r"\bmas\b", "mais"), (r"\bhá\b", "a"), (r"\bonde\b", "aonde"),
    (r"\bmau\b", "mal"), (r"\bporque\b", "por que"), (r"\btêm\b", "tem"),
    (r"\bàs\b", "as"), (r"\bà\b", "a"),
]


def ablacao_c1(texto, n_desvios):
    """Injeta n desvios: primeiro trocas lexicais clássicas, depois remoção de
    acento palavra a palavra. Determinístico — varre sempre na mesma ordem."""
    restantes = n_desvios
    for padrao, troca in TROCAS_C1:
        if restantes <= 0:
            break
        texto, feitas = re.subn(padrao, troca, texto, count=restantes)
        restantes -= feitas
    if restantes > 0:
        palavras = texto.split(" ")
        for i, p in enumerate(palavras):
            if restantes <= 0:
                break
            sem = p.translate(SEM_ACENTO)
            if sem != p:
                palavras[i] = sem
                restantes -= 1
        texto = " ".join(palavras)
    return texto, n_desvios - restantes


# --------------------------------------------------------------------------
# Competência II — repertório e tangenciamento do tema
# --------------------------------------------------------------------------
# Para tangenciar sem sair do assunto, troca-se o núcleo do tema por um termo
# genérico: o texto passa a tratar do assunto, não do tema. É exatamente a
# diferença entre os níveis 40 e 120 do descritor oficial da Competência II.
NUCLEO_DO_TEMA = {
    2021: (r"registro civil|certid(?:ão|ões) de nascimento|documenta(?:ção|ções) civil",
           "a burocracia"),
    2022: (r"comunidades e povos tradicionais|povos tradicionais|comunidades tradicionais",
           "a população"),
    2023: (r"trabalho de cuidado|invisibilidade do trabalho", "o trabalho"),
    2024: (r"herança africana|cultura afro-?brasileira", "a cultura"),
}


def ablacao_c2(texto, severidade, enem_ano):
    paras = paragrafos(texto)
    if severidade >= 1 and paras:                 # tira o repertório da introdução
        fs = frases(paras[0])
        if len(fs) > 2:
            paras[0] = " ".join(fs[1:])
    texto = juntar(paras)
    if severidade >= 2:                           # tangencia o tema
        padrao, generico = NUCLEO_DO_TEMA[enem_ano]
        texto = re.sub(padrao, generico, texto, flags=re.I)
    return texto


# --------------------------------------------------------------------------
# Competência III — tese e organização dos argumentos
# --------------------------------------------------------------------------
def ablacao_c3(texto, severidade):
    paras = paragrafos(texto)
    if severidade >= 1 and paras:                 # remove a tese (fecho da introdução)
        fs = frases(paras[0])
        if len(fs) > 1:
            paras[0] = " ".join(fs[:-1])
    if severidade >= 2 and len(paras) > 3:        # desorganiza o desenvolvimento
        miolo = paras[1:-1]
        paras = [paras[0]] + miolo[::-1] + [paras[-1]]
    return juntar(paras)


# --------------------------------------------------------------------------
# Competência IV — coesão
# --------------------------------------------------------------------------
CONECTIVOS_INTER = (r"Portanto|Ademais|Outrossim|Entretanto|Todavia|Contudo|"
                    r"Dessa forma|Desse modo|Nesse sentido|Nesse viés|Sob esse prisma|"
                    r"Além disso|De início|Por fim|Em suma|Assim")
CONECTIVOS_INTRA = (r"\b(?:porém|contudo|todavia|entretanto|porquanto|uma vez que|"
                    r"visto que|já que|ademais|outrossim|logo|portanto|"
                    r"bem como|ou seja|isto é)\b")


def ablacao_c4(texto, severidade):
    if severidade >= 1:                           # conectivos de abertura de parágrafo
        texto = re.sub(r"(^|\n\n)(?:" + CONECTIVOS_INTER + r")[,]?\s*",
                       lambda m: m.group(1), texto)
    if severidade >= 2:                           # conectivos interfrásicos
        texto = re.sub(CONECTIVOS_INTRA, "", texto, flags=re.I)
        texto = re.sub(r"[ \t]{2,}", " ", texto)
        texto = re.sub(r"\s+([,.;])", r"\1", texto)
    return texto


# --------------------------------------------------------------------------
# Competência V — proposta de intervenção
# --------------------------------------------------------------------------
def ablacao_c5(texto, severidade):
    """A conclusão do dissertativo-argumentativo do Enem encadeia agente, ação,
    modo, efeito e detalhamento. Truncar a partir do fim remove primeiro o
    detalhamento, depois o efeito, e assim por diante até sumir a proposta."""
    paras = paragrafos(texto)
    if not paras:
        return texto
    if severidade >= 4:
        return juntar(paras[:-1])                 # sem proposta alguma
    fs = frases(paras[-1])
    corte = min(severidade, max(0, len(fs) - 1))
    if corte:
        paras[-1] = " ".join(fs[:len(fs) - corte])
    return juntar(paras)


# --------------------------------------------------------------------------
# Colaterais declarados: degradar uma competência mexe legitimamente em outras.
# A especificidade é medida só contra as competências FORA desta lista.
# --------------------------------------------------------------------------
COLATERAIS = {
    "c1": [],
    "c2": ["c3"],           # o repertório também sustenta a argumentação
    "c3": ["c2", "c4"],     # tese e ordem afetam estrutura e encadeamento
    "c4": ["c3"],           # coesão e coerência se tocam
    "c5": ["c2", "c3"],     # a conclusão faz parte da estrutura do texto
}

PLANO = {"c1": [3, 8, 20], "c2": [1, 2], "c3": [1, 2], "c4": [1, 2], "c5": [1, 2, 3, 4]}


def gerar(reg):
    saidas = []
    for alvo, severidades in PLANO.items():
        for sev in severidades:
            detalhe = {}
            if alvo == "c1":
                texto, aplicados = ablacao_c1(reg["texto"], sev)
                detalhe = {"desvios_injetados": aplicados}
            elif alvo == "c2":
                texto = ablacao_c2(reg["texto"], sev, reg["enem_ano"])
            elif alvo == "c3":
                texto = ablacao_c3(reg["texto"], sev)
            elif alvo == "c4":
                texto = ablacao_c4(reg["texto"], sev)
            else:
                texto = ablacao_c5(reg["texto"], sev)
            if texto.strip() == reg["texto"].strip():
                continue                          # degradação sem efeito
            saidas.append({
                "id": f"{reg['id']}::{alvo}::s{sev}",
                "base_id": reg["id"],
                "alvo": alvo,
                "severidade": sev,
                "tema": reg["tema"],
                "enem_ano": reg["enem_ano"],
                "texto": texto,
                "colaterais_esperados": COLATERAIS[alvo],
                "detalhe": detalhe,
            })
    return saidas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="oficial/redacoes")
    ap.add_argument("--saida", default="datasets/ablacoes.jsonl")
    ap.add_argument("--amostra-bases", type=int, default=0,
                    help="usa só N redações como base, distribuídas entre as edições. "
                         "Cada base custa ~12 invocações da skill; dimensione a rodada aqui.")
    ap.add_argument("--somente-rotuladas", action="store_true",
                    help="ignora a Cartilha 2025, que não publica notas")
    a = ap.parse_args()

    arquivos = sorted(pathlib.Path(a.entrada).glob("*.json"))
    if a.somente_rotuladas:
        arquivos = [f for f in arquivos if not f.name.startswith("2025-")]
    if a.amostra_bases and a.amostra_bases < len(arquivos):
        # passo uniforme sobre a lista ordenada: pega redações de todas as
        # edições em vez de esvaziar a primeira. Determinístico, sem sorteio.
        passo = len(arquivos) / a.amostra_bases
        arquivos = [arquivos[int(i * passo)] for i in range(a.amostra_bases)]
    pathlib.Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
    n_base = n_abl = 0
    with open(a.saida, "w", encoding="utf-8") as fh:
        for arq in arquivos:
            reg = json.loads(arq.read_text(encoding="utf-8"))
            n_base += 1
            # a redação intacta é a referência contra a qual cada ablação é lida
            fh.write(json.dumps({
                "id": f"{reg['id']}::base", "base_id": reg["id"], "alvo": None,
                "severidade": 0, "tema": reg["tema"], "enem_ano": reg["enem_ano"],
                "texto": reg["texto"], "colaterais_esperados": [], "detalhe": {},
            }, ensure_ascii=False) + "\n")
            for item in gerar(reg):
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
                n_abl += 1
    print(f"{n_base} redacoes base + {n_abl} ablacoes -> {a.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
