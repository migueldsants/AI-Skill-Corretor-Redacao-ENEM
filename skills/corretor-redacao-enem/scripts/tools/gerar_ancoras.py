# -*- coding: utf-8 -*-
"""Gera references/ancoras-c1.md: como o Inep aplica o descritor da Competência I.

Por que só a Competência I: o piloto mostrou que a skill acerta os desvios que
o Inep conta e depois acrescenta minúcias prescritivas que ele não conta,
derrubando 200 para 160 em 5 de 5 redações nota 1.000. O descritor de 200
tolera desvio "como excepcionalidade e quando não caracterizarem reincidência",
mas não diz quantos — quem diz é a Parte 2 da Cartilha, que existe justamente
para mostrar a Parte 1 aplicada.

Isto NÃO é ajuste ao gabarito: o texto das âncoras é o comentário literal do(a)
avaliador(a) do Inep, e o corpus usado aqui é o de calibração, não o conjunto
de teste (que é o Essay-BR, particionado e tocado uma vez só).

Uso:  python skills/corretor-redacao-enem/scripts/tools/gerar_ancoras.py
"""
import json, pathlib, re, sys

SKILL = pathlib.Path(__file__).resolve().parents[2]   # skills/corretor-redacao-enem
RAIZ = SKILL.parents[1]                               # raiz do projeto
RED = RAIZ / "oficial" / "redacoes"
DEST = SKILL / "references"

INICIO_C1 = re.compile(r"modalidade escrita formal", re.I)

# Vocabulário que denuncia que o comentário passou para outra competência.
FIM_C1 = re.compile(
    r"dissertativo|argumentativ|\btema\b|repert[óo]rio|proposta de interven"
    r"|coes[ãa]o|projeto de texto|tese|par[áa]grafo de conclus", re.I)


ID_ANONIMO = re.compile(r"^(\d{4})-(\d+)-")


def rotulo(id_):
    """Identifica a âncora pela edição da Cartilha e pelo índice, nunca pelo
    nome do(a) participante: o repositório não versiona dado de terceiros.
    O corpus local mantém o id completo — a anonimização é só na saída."""
    m = ID_ANONIMO.match(id_)
    if not m:
        raise ValueError(f"id fora do padrão <ano>-<indice>-<nome>: {id_}")
    return f"{m.group(1)}-{m.group(2)}"


def frases(texto):
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+", texto) if f.strip()]


def trecho_c1(comentario):
    """Do início da frase que fala da modalidade escrita até a primeira frase
    que trate de outra competência. Devolve None se não achar — sem chute."""
    fs = frases(re.sub(r"\s+", " ", comentario))
    ini = next((i for i, f in enumerate(fs) if INICIO_C1.search(f)), None)
    if ini is None:
        return None
    saida = []
    for f in fs[ini:]:
        if saida and FIM_C1.search(f):
            break
        saida.append(f)
        if len(saida) >= 3:
            break
    return " ".join(saida)


def main():
    linhas = [
        "# Âncoras de calibração — Competência I", "",
        "Como o Inep aplica na prática o descritor da Competência I. Cada item",
        "traz o comentário literal do(a) avaliador(a) sobre uma redação e a nota",
        "que ela recebeu. Fonte: Parte 2 das Cartilhas do(a) Participante.", "",
        "Cada âncora é identificada pela edição da Cartilha e pelo índice da",
        "redação dentro dela — nunca pelo nome do(a) participante.", "",
        "**Leia isto antes de fechar a nota da Competência I.** O padrão que estes",
        "casos revelam:", "",
        "- O Inep **conta desvios**, e nomeia cada um. Um ou dois desvios de tipos",
        "  distintos **não impedem 200** — o descritor tolera desvio \"como",
        "  excepcionalidade e quando não caracterizarem reincidência\".",
        "- \"Reincidência\" é o **mesmo tipo** de desvio se repetindo, não a mera",
        "  presença de vários desvios diferentes.",
        "- O que o Inep conta como desvio é concreto e verificável: ortografia,",
        "  acentuação, pontuação ausente, crase, regência, concordância, escolha",
        "  lexical inadequada. Ele **não** conta preferências de estilo, nem pontos",
        "  finos de prescrição sobre os quais gramáticos divergem.",
        "- Antes de rebaixar de 200 para 160, verifique se cada item que você",
        "  listou seria nomeado por um(a) avaliador(a) do Inep como desvio. Se",
        "  você listou quatro e só um sobreviveria a esse teste, a nota é 200.", "",
        "---", "",
    ]
    n = 0
    for arq in sorted(RED.glob("*.json")):
        reg = json.loads(arq.read_text(encoding="utf-8"))
        if not reg.get("rotulo_oficial"):
            continue                      # sem nota publicada, não é âncora
        t = trecho_c1(reg["comentario_inep"])
        if not t:
            continue
        n += 1
        linhas += [f"### {rotulo(reg['id'])} — Competência I: 200 pontos", "",
                   f"> {t}", ""]
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "ancoras-c1.md").write_text("\n".join(linhas), encoding="utf-8")
    print(f"  ancoras-c1.md: {n} âncoras")
    return 0


if __name__ == "__main__":
    sys.exit(main())
