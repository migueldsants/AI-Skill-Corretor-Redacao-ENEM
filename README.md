<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-22c55e?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/agente%20de%20IA-skill-7C3AED?style=flat-square" alt="Skill para agentes de IA">
  <img src="https://img.shields.io/badge/python-3.11+-0891b2?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/fonte-Inep%20oficial-0ea5e9?style=flat-square" alt="Fonte oficial">
</p>

# Corretor de redação do Enem

**Corrige uma redação do Enem pela Matriz de Referência oficial do Inep — direto no chat, com o descritor citado em cada nota.**

É uma skill para agentes de IA. Toda a rubrica em `references/` é **transcrição
literal** da *Cartilha do(a) Participante*, com procedência registrada em
`oficial/fontes.md` (URL e sha256 de cada PDF). Junto vem o harness que reproduz
a rubrica a partir das fontes e roda a avaliação.

- **Nota por competência, com o descritor na frente** — as cinco competências em
  0, 40, 80, 120, 160 ou 200, cada uma justificada por cópia literal do descritor
  oficial e por comparação com os níveis vizinhos
- **Uma competência por vez, em contextos separados** — o harness invoca o CLI
  cinco vezes por redação, porque processo separado é contexto separado: é isso
  que impede uma nota alta em C2 puxar a C3
- **Calibrada contra o próprio Inep** — 22 comentários de avaliador(a) sobre
  redações nota 1.000 fixam quantos desvios a Competência I de fato tolera
- **Reprodutível de ponta a ponta** — a rubrica se regera dos PDFs oficiais
  byte a byte, e cinco autotestes travam o resultado

```bash
git clone https://github.com/migueldsants/AI-Skill-Corretor-Redacao-ENEM.git

# opção 1 — diretório comum a todos os agentes
ln -s "$PWD/AI-Skill-Corretor-Redacao-ENEM/skills/corretor-redacao-enem" ~/.agents/skills/corretor-redacao-enem

# opção 2 — direto no Claude
ln -s "$PWD/AI-Skill-Corretor-Redacao-ENEM/skills/corretor-redacao-enem" ~/.claude/skills/corretor-redacao-enem
```

Escolha uma das duas. Para Windows, para instalação só num projeto e para o
porquê de ligar em vez de copiar, veja [Instalação](#instalação).

**Nenhum repositório é necessário para usar:** com a skill instalada, cole a
redação e o tema em qualquer chat de IA. O repositório é para reproduzir a
rubrica e rodar a avaliação.

> Ferramenta de estudo: aplica a Matriz de Referência oficial de forma
> consistente e auditável. A nota oficial do exame é atribuída por
> avaliadores(as) do Inep.

---

## Como funciona

| Etapa | O que acontece |
|---|---|
| **Portões de anulação** | Só os critérios verificáveis no texto são julgados; os que exigem a folha física saem como `não avaliados`. |
| **Uma competência por vez** | Cada competência lê **um único** arquivo de rubrica e relê a redação inteira sob aquele critério. |
| **Escolha do nível** | Os seis descritores são comparados entre si; vence o que melhor descreve o texto. |
| **Justificativa contra o vizinho** | "Dei 160 e não 200 porque…" — a comparação com o nível acima e o de baixo é obrigatória. |
| **Confiança declarada** | C1 e C3 saem marcadas `baixa` quando o descritor não dá limiar, em vez de fingir precisão. |

A nota é restrita aos seis níveis oficiais, e o descritor é **citado
literalmente**: se a skill não consegue copiar o descritor do arquivo de
referência, não tem base para a nota.

## Modos

| Invocação | O que faz |
|---|---|
| `/corretor-redacao-enem` | Correção completa: portões + as cinco competências + total |
| `/corretor-redacao-enem --competencia N` | Só a competência N, sem ler nem comentar as outras. É o modo que o harness usa |
| `/corretor-redacao-enem --gate` | Só os portões de anulação |
| `/corretor-redacao-enem --json` | Acrescenta o bloco JSON ao final da prosa |

**Entrada obrigatória:** o texto da redação **e o tema** da proposta. Sem tema a
skill pergunta — supor o tema a partir do próprio texto tornaria a avaliação
circular. Os textos motivadores são opcionais.

## Instalação

O repositório é a fonte de verdade da skill, mas o agente só descobre skills em
diretórios conhecidos. Ligue um ao outro em vez de copiar — cópia sai de
sincronia com o git.

| Destino | Onde | Quando usar |
|---|---|---|
| **Comum a todos os agentes** | `~/.agents/skills/` | Você usa mais de um agente, ou já instala skills por aí. É o diretório neutro que os gerenciadores de skill adotam |
| **Claude** | `~/.claude/skills/` | Instalação global para o Claude, sem depender do diretório comum |
| **Do projeto** | `.claude/skills/` dentro do repositório onde você trabalha | A skill fica disponível só naquele projeto |

As duas primeiras são alternativas: escolha uma.

### Opção A — diretório comum (`~/.agents/skills/`)

Um único lugar, que serve qualquer agente.

```bash
# Linux/macOS
ln -s "$PWD/skills/corretor-redacao-enem" ~/.agents/skills/corretor-redacao-enem
```

```powershell
# Windows: junção de diretório, não precisa de admin
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\corretor-redacao-enem" ^
                 "<caminho-do-repo>\skills\corretor-redacao-enem"
```

`~/.agents/skills/` é convenção dos gerenciadores de skill. Se o seu agente não
encontrar a skill depois disso, ligue o diretório dele ao comum:

```bash
ln -s ~/.agents/skills/corretor-redacao-enem ~/.claude/skills/corretor-redacao-enem
```

### Opção B — direto no Claude (`~/.claude/skills/`)

```bash
# Linux/macOS
ln -s "$PWD/skills/corretor-redacao-enem" ~/.claude/skills/corretor-redacao-enem
```

```powershell
# Windows: junção de diretório, não precisa de admin
cmd /c mklink /J "$env:USERPROFILE\.claude\skills\corretor-redacao-enem" ^
                 "<caminho-do-repo>\skills\corretor-redacao-enem"
```

Para deixar a skill disponível só num projeto, use `.claude/skills/` dentro dele
em vez de `~/.claude/skills/`.

Em qualquer opção, `/corretor-redacao-enem` passa a funcionar em qualquer
diretório, e editar a rubrica no repo muda o que roda na hora. O vínculo aponta
para o caminho do repo: mover o repositório pede refazer o vínculo.

## Estrutura

```
oficial/
  fontes.md          URL + sha256 + data de cada PDF baixado
  pdfs/              Cartilhas 2022, 2023, 2024, 2025
skills/corretor-redacao-enem/
  SKILL.md           o corretor
  references/        os 6 níveis de cada competência, critérios de anulação
                     e as âncoras de calibração da Competência I
  scripts/
    tools/           decodificação, extração dos PDFs e geração das referências
    eval/
      ablate.py      gera as degradações controladas
      run.py         executa a skill via `claude -p`, uma invocação por competência
      metrics.py     QWK, MAE, acerto de nível, test-retest
      report.py      aplica os portões de aprovação
    tests/           autotestes de tudo acima
```

Todo o código vive dentro da skill. O que fica fora dela são as **fontes** (os
PDFs do Inep e sua procedência) e o que o código **deriva** delas.

### O que não é versionado

Nada que contenha texto de redação real entra no repositório, e nada disso
precisa entrar: tudo é derivado dos PDFs oficiais e regenerável pelos scripts.

| Caminho | O que é | Como recriar |
|---|---|---|
| `oficial/redacoes/` | as redações comentadas das Cartilhas, uma por JSON | `scripts/tools/extrair_redacoes.py` |
| `datasets/` | as ablações derivadas | `scripts/eval/ablate.py` |
| `results/` | notas cruas e relatórios de cada rodada | `scripts/eval/run.py` |
| `para-corrigir/` | redações pessoais — as folhas do Enem trazem CPF e número de inscrição | não se recria; nunca deve ser versionado |

O material regenerado é byte a byte o mesmo: `scripts/tests/test_corpus.py`
verifica a integridade e `scripts/tests/test_referencias.py` trava a rubrica
contra o render em imagem das páginas.

As redações extraídas são identificadas por edição da Cartilha e índice — nem
nelas nem em `references/` aparece nome de participante.

## Como rodar

Tudo a partir da raiz do projeto. `$S` encurta o caminho da skill.

```bash
python -m pip install pymupdf     # única dependência; o resto é stdlib
S=skills/corretor-redacao-enem/scripts

# reproduzir a rubrica e o material derivado dos PDFs oficiais
for Y in 2022 2023 2024 2025; do
  python $S/tools/extrair_redacoes.py oficial/pdfs/cartilha_$Y.pdf $Y
done
python $S/tools/gerar_referencias.py oficial/pdfs/cartilha_2025.pdf 2025
python $S/tools/gerar_zeradores.py  oficial/pdfs/cartilha_2025.pdf 2025
python $S/tools/gerar_ancoras.py    # âncoras de calibração da Competência I

# autotestes
for t in $S/tests/test_*.py; do python "$t"; done

# avaliação
python $S/eval/ablate.py --amostra-bases 10 --somente-rotuladas --saida datasets/amostra.jsonl
python $S/eval/run.py --dataset oficial/redacoes --saida results/v1/oficial.jsonl --dry-run
python $S/eval/run.py --dataset oficial/redacoes --saida results/v1/oficial.jsonl
python $S/eval/report.py results/v1/
```

Os scripts de extração rodam antes dos autotestes: `oficial/redacoes/` não é
versionado, e o teste avisa com a receita se ele faltar.

`--dry-run` conta as invocações e projeta o custo sem executar nada. Cada
invocação é retomável: o resultado cru fica em `results/<rodada>/raw/`, então uma
rodada interrompida continua de onde parou.

Quem executa a skill é o próprio CLI do agente, que carrega o `SKILL.md`,
resolve `references/` e aplica a rubrica.

## Contribuindo

Issue e pull request são bem-vindos. Duas regras valem para qualquer mudança:

- **Nada de texto de redação real no repositório.** Redação de participante e
  folha de prova ficam de fora — veja [o que não é versionado](#o-que-não-é-versionado).
- **A barra é definida antes da medição.** O `report.py` aplica portões de
  aprovação com critério fixo, e um portão sem dados sai como `NAO EXECUTADO` —
  nunca como aprovado.

Mudança na rubrica exige rodar `scripts/tests/test_referencias.py`, que compara
cada descritor com o render em imagem da página oficial.

## Licença

[MIT](LICENSE) — livre para usar, modificar e distribuir.

A licença cobre o **código e a documentação deste repositório**. Ela não cobre o
material do Inep: as Cartilhas em `oficial/pdfs/`, os descritores transcritos em
`references/` e os comentários de avaliador(a) são obra do Inep, reproduzidos
aqui como referência, com URL e sha256 em `oficial/fontes.md`.
