# -*- coding: utf-8 -*-
"""Extrai o texto de uma Cartilha do Participante já decodificado.

Uso:  python skills/corretor-redacao-enem/scripts/tools/extrair_cartilha.py \n          oficial/pdfs/cartilha_2025.pdf saida.txt
"""
import sys, pathlib, importlib.util, re, pymupdf

_r = pathlib.Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("dc", _r / "decode_cartilha.py")
dc = importlib.util.module_from_spec(_s); _s.loader.exec_module(dc)

# Só cabeçalhos/marcas de navegação. O número da página NÃO entra aqui: ele é
# removido por geometria em decode_cartilha.page_text, porque um filtro por
# "\d{1,3}" apagaria também as pontuações 200/160/120/80/40 das tabelas.
RODAPE = re.compile(
    r"^(A? ?REDA\S*O DO ENEM \d{4}"
    r"|A REDA\S*O NO ENEM \d{4}"
    r"|CARTILHA DO PARTICIPANTE.*"
    r"|VOLTAR PARA"
    r"|O SUM\u00c1RIO)$")


def extrair(pdf_path):
    doc = pymupdf.open(pdf_path)
    paginas = []
    for i, pg in enumerate(doc):
        linhas = [l for l in dc.page_text(pg).splitlines()
                  if not RODAPE.match(l.strip())]
        paginas.append((i + 1, "\n".join(linhas).strip()))
    return paginas


def main():
    pdf, out = sys.argv[1], sys.argv[2]
    paginas = extrair(pdf)
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        for n, t in paginas:
            fh.write(f"\n\n<<<PAGINA {n}>>>\n{t}")
    texto = "\n".join(t for _, t in paginas)
    print(f"{pdf} -> {out}: {len(paginas)} pag, {len(texto)} chars, "
          f"{texto.count(dc.UNKNOWN)} nao resolvidos, "
          f"{len(re.findall(chr(1)+'-'+chr(31), texto))} ainda codificados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
