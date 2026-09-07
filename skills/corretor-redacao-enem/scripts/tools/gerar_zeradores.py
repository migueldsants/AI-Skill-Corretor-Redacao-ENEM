# -*- coding: utf-8 -*-
"""Gera references/zeradores.md a partir da Cartilha do Participante.

A lista de anulação é transcrita literalmente da seção canônica ("Quais as
razões para se atribuir nota 0 (zero) a uma redação?"). A classificação em três
grupos é nossa e existe porque um corretor que recebe apenas o TEXTO não tem
como julgar parte dos critérios (identificação, legibilidade, folha em branco).

Uso:  python skills/corretor-redacao-enem/scripts/tools/gerar_zeradores.py \n          oficial/pdfs/cartilha_2025.pdf 2025
"""
import sys, re, pathlib, importlib.util

_r = pathlib.Path(__file__).resolve().parent
SKILL = _r.parents[1]          # skills/corretor-redacao-enem
_s = importlib.util.spec_from_file_location("ex", _r / "extrair_cartilha.py")
ex = importlib.util.module_from_spec(_s); _s.loader.exec_module(ex)

# chave -> (grupo, rótulo curto). Grupo A: verificável no texto. B: exige a
# folha física. C: penaliza uma competência, não anula a redação.
CLASSIFICACAO = [
    ("fuga total ao tema",            "A", "fuga_total_ao_tema"),
    ("não obediência ao tipo",        "A", "tipo_textual_incorreto"),
    ("ausência de texto",             "B", "em_branco"),
    ("extensão de até 7",             "A", "texto_insuficiente"),
    ("impropérios",                   "A", "improperios_ou_anulacao_proposital"),
    ("parte deliberadamente",         "A", "parte_desconectada"),
    ("nome, assinatura",              "B", "identificacao_indevida"),
    ("língua estrangeira",            "A", "lingua_estrangeira"),
    ("texto ilegível",                "B", "ilegivel"),
    ("cópia de texto(s) da Prova",    "A", "copia_dos_textos_motivadores"),
]

def bullets(paginas):
    txt = "\n".join(paginas[p] for p in (9, 10))
    ini = txt.index("A redação receberá nota 0 (zero)")
    fim = txt.index("ATENÇÃO!", ini)
    brutos = re.split(r"\n\s*•\s*", txt[ini:fim])[1:]
    return [re.sub(r"\s+", " ", b).strip().rstrip(";.") for b in brutos if b.strip()]

def main():
    pdf, ano = sys.argv[1], sys.argv[2]
    paginas = dict(ex.extrair(pdf))
    itens = bullets(paginas)
    achados = []
    for texto in itens:
        grupo, slug = "A", None
        for chave, g, s in CLASSIFICACAO:
            if chave.lower() in texto.lower():
                grupo, slug = g, s; break
        if slug is None:
            print(f"  AVISO: item não classificado -> {texto[:60]}", file=sys.stderr)
            slug = "nao_classificado"
        achados.append((grupo, slug, texto))

    L = [
        "# Critérios de anulação (nota 0)", "",
        f"Fonte: *A Redação do Enem {ano} — Cartilha do(a) Participante* (Inep), seção",
        '"Quais as razões para se atribuir nota 0 (zero) a uma redação?" (p. 9-10 do PDF).',
        "Os itens são transcrições literais; o agrupamento é operacional.", "",
        "Estes critérios são **portões binários**: são verificados ANTES de qualquer nota",
        "por competência. Se um deles dispara, a redação recebe 0 e nenhuma competência",
        "é pontuada.", "",
        "## Grupo A — verificáveis a partir do texto", "",
        "| id | critério (transcrição literal) |", "|---|---|",
    ]
    L += [f"| `{s}` | {t} |" for g, s, t in achados if g == "A"]
    L += ["", "## Grupo B — exigem a folha de redação física", "",
          "O corretor recebe apenas o texto e **não pode** julgar estes itens. Deve",
          "declará-los como não avaliados, nunca presumir que estão em ordem.", "",
          "| id | critério (transcrição literal) |", "|---|---|"]
    L += [f"| `{s}` | {t} |" for g, s, t in achados if g == "B"]
    L += ["", "## Grupo C — penalizam uma competência, sem anular a redação", "",
          "- **Desrespeito aos direitos humanos** — nota 0 na Competência V, apenas.",
          f'  Cartilha {ano}: "Propostas que desrespeitem os direitos humanos receberão',
          '  nota 0 (zero) na Competência V." A redação **não** é anulada por isso.',
          "- **Traços de outro tipo textual** em texto predominantemente dissertativo-",
          "  argumentativo — não anula; penaliza a Competência II.", "",
          "## Ressalva sobre a contagem de linhas", "",
          '"Texto insuficiente" é definido em **linhas manuscritas** (até 7) na folha',
          "oficial de 30 linhas. Com entrada digitada não há equivalência exata: a",
          "contagem depende da letra do(a) participante. O corretor deve usar uma",
          "estimativa declarada como aproximada e nunca anular um texto limítrofe",
          "apenas por esse critério.", ""]
    dest = SKILL / "references" / "zeradores.md"
    dest.write_text("\n".join(L), encoding="utf-8")
    print(f"  zeradores.md: {len(achados)} critérios "
          f"(A={sum(1 for g,_,_ in achados if g=='A')}, B={sum(1 for g,_,_ in achados if g=='B')})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
