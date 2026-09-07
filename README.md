<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-22c55e?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/agente%20de%20IA-skill-7C3AED?style=flat-square" alt="Skill para agentes de IA">
  <img src="https://img.shields.io/badge/python-3.11+-0891b2?style=flat-square" alt="Python">
</p>

# Corretor de redação do Enem

**Corrige uma redação do Enem pela Matriz de Referência oficial do Inep — direto no chat, com o descritor citado em cada nota.**

É uma skill para agentes de IA, não um cliente de API. Toda a rubrica em
`references/` é **transcrição literal** da *Cartilha do(a) Participante*, com
procedência registrada em `oficial/fontes.md` (URL e sha256 de cada PDF). Junto
vem o harness que submete a skill a portões de aprovação.

- **Nota por competência, com o descritor na frente** — as cinco competências em
  0, 40, 80, 120, 160 ou 200, cada uma justificada por cópia literal do descritor
  oficial e por comparação com os níveis vizinhos
- **Uma competência por vez, em contextos separados** — o harness invoca o CLI
  cinco vezes por redação, porque processo separado é contexto separado: é isso
  que impede uma nota alta em C2 puxar a C3
- **Calibrada contra o próprio Inep** — 22 comentários de avaliador(a) sobre
  redações nota 1.000 fixam quantos desvios a Competência I de fato tolera
- **Medida, não presumida** — cinco portões de aprovação, corretores sintéticos
  nos autotestes, e portão sem dados reportado como `NAO EXECUTADO`

```bash
git clone https://github.com/migueldsants/AI-Skills-ENEM.git

# opção 1 — diretório comum a todos os agentes
ln -s "$PWD/AI-Skills-ENEM/skills/corretor-redacao-enem" ~/.agents/skills/corretor-redacao-enem

# opção 2 — direto no Claude
ln -s "$PWD/AI-Skills-ENEM/skills/corretor-redacao-enem" ~/.claude/skills/corretor-redacao-enem
```

Escolha uma das duas. Para Windows, para instalação só num projeto e para o
porquê de ligar em vez de copiar, veja [Instalação](#instalação).

**Nenhum repositório é necessário para usar:** com a skill instalada, cole a
redação e o tema em qualquer chat de IA. O repositório é para reproduzir a
rubrica e rodar a avaliação.

---

## O que a skill afirma e o que não afirma

**Afirma:** aplicar a Matriz de Referência oficial de forma consistente e
auditável, citando o descritor que sustenta cada nota.

**Não afirma:** reproduzir a nota que o Inep daria. O Inep usa dois
avaliadores(as) independentes e aciona um(a) terceiro(a) quando eles divergem —
nem dois humanos treinados concordam sempre. Não existe base pública com texto de
redação e notas por competência atribuídas pelo Inep, então nenhuma concordância
com o Inep pode ser medida nem prometida.

## Como funciona

| Etapa | O que acontece |
|---|---|
| **Portões de anulação** | Só os critérios verificáveis no texto são julgados; os que exigem a folha física saem como `não avaliados`, nunca como "em ordem". |
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
circular. Os textos motivadores são opcionais; sem eles o critério de cópia fica
não avaliado, e isso é dito.

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

`~/.agents/skills/` é convenção dos gerenciadores de skill, não um diretório que
todo agente varre sozinho. Se o seu não encontrar a skill depois disso, ligue o
diretório dele ao comum:

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
para o caminho do repo: mover ou apagar o repositório quebra a skill instalada.

Sem essa instalação o `run.py` falha em toda invocação — a skill não é
encontrada.

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
      report.py      aplica os cinco portões
    tests/           autotestes de tudo acima
```

Todo o código vive dentro da skill. O que fica fora dela são as **fontes** (os
PDFs do Inep e sua procedência) e o que o código **deriva** delas.

### O que não é versionado

Nada que contenha texto de redação real entra no repositório, e nada disso
precisa entrar: tudo é derivado dos PDFs oficiais e regenerável pelos scripts.

| Caminho | O que é | Como recriar |
|---|---|---|
| `oficial/redacoes/` | as 37 redações comentadas, uma por JSON | `scripts/tools/extrair_redacoes.py` |
| `datasets/` | as 416 ablações | `scripts/eval/ablate.py` |
| `results/` | notas cruas e relatórios de cada rodada | `scripts/eval/run.py` |
| `para-corrigir/` | redações pessoais — as folhas do Enem trazem CPF e número de inscrição | não se recria; nunca deve ser versionado |

O corpus regenerado é byte a byte o mesmo: `scripts/tests/test_corpus.py` verifica
a integridade e `scripts/tests/test_referencias.py` trava a rubrica contra o
render em imagem das páginas.

## Corpus

| Cartilha | Edição do Enem | Redações | Notas publicadas |
|---|---|---|---|
| 2022 | 2021 | 7 | ✅ 1.000 |
| 2023 | 2022 | 10 | ✅ 1.000 |
| 2024 | 2023 | 10 | ✅ 1.000 |
| 2025 | 2024 | 10 | ❌ |

28 redações rotuladas, 37 no total, todas com o comentário do(a) avaliador(a) do
Inep. 416 ablações derivadas.

### Achados sobre as fontes oficiais

- **A Cartilha 2025 deixou de publicar as notas.** Até 2024 a seção se chamava
  "Amostra de redações NOTA 1.000"; em 2025 virou "Amostra de redações do Enem
  2024" e o texto diz apenas que as redações "receberam boas notas". As 10
  redações de 2025 entram com `rotulo_oficial: false` e `notas: null`, e não
  contam para o portão A.
- **As redações vêm como texto, não como imagem.** O Inep publica as redações
  transcritas na Cartilha. Não foi preciso OCR nem transcrição manual.
- **Os PDFs usam subsets de fonte sem ToUnicode válido.** Cerca de 11% dos
  caracteres saem embaralhados na extração ingênua, incluindo dois dos seis
  descritores da Competência I. `scripts/tools/decode_cartilha.py` resolve os dois
  mapeamentos; `scripts/tests/test_decode.py` trava o resultado contra o render em
  imagem das páginas.
- **A Cartilha 2022 tem uma camada de 4pt com o enunciado corrompido**
  ("resgistro cilvil" em vez de "registro civil") — defeito do PDF do Inep, não da
  extração. `scripts/tools/extrair_redacoes.py` ignora spans abaixo de 6pt.

## Portões de aprovação

| Portão | Conjunto | Barra |
|---|---|---|
| **A — teto** | oficiais rotuladas | ≥ 90% das competências em 160 ou 200; total ≥ 900 |
| **B — discriminação** | ablações | alvo cai em ≥ 85%; Spearman ≤ −0,8 em C1 e C5; não-alvo estável em ≥ 80% |
| **C — concordância** | [Essay-BR](https://github.com/lplnufpi/essay-br) (teste) | QWK ≥ 0,70 e MAE ≤ 40 por competência |
| **D — estabilidade** | 3 execuções | nota idêntica em ≥ 85%; desvio do total ≤ 40 |
| **E — calibração** | Essay-BR (teste) | média do modelo a ≤ 20 pontos da humana |

O portão A sozinho é insuficiente por construção. `scripts/tests/test_portoes.py`
verifica isso empiricamente: um corretor que devolve 1.000 sempre **passa no A e é
reprovado no B**. Portão sem dados é reportado como `NAO EXECUTADO`, nunca como
aprovado.

## Como rodar

Tudo a partir da raiz do projeto. `$S` encurta o caminho da skill.

```bash
python -m pip install pymupdf     # única dependência; o resto é stdlib
S=skills/corretor-redacao-enem/scripts

# reproduzir a rubrica e o corpus a partir dos PDFs oficiais
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
python $S/eval/run.py --dataset datasets/amostra.jsonl --saida results/v1/ablacoes.jsonl
python $S/eval/report.py results/v1/
```

Os scripts de extração precisam rodar antes dos autotestes: `oficial/redacoes/`
não é versionado, e `test_corpus.py` falha com essa mensagem se ele faltar.

`--dry-run` conta as invocações e projeta o custo sem executar nada. Cada
invocação é retomável: o resultado cru fica em `results/<rodada>/raw/`, então uma
rodada interrompida continua de onde parou sem repagar.

Quem executa a skill é o próprio CLI do agente, que carrega o `SKILL.md`,
resolve `references/` e aplica a rubrica. Reimplementar os prompts como chamadas de SDK
mediria o reimplementador, não a skill.

### Custo

Medido numa invocação real (Opus, uma competência, redação de 3,4 mil chars):
**US$ 0,24** e **41 s**. O grosso é o prompt de sistema do próprio agente
(~40 mil tokens), que viaja em toda invocação — daí o custo por chamada ser ordens
de grandeza maior que o de uma chamada de API equivalente.

| Rodada | Invocações | Custo equivalente |
|---|---|---|
| Corpus oficial (portão A) | 185 | ~US$ 44 |
| Ablações, 10 bases (portão B) | 615 | ~US$ 148 |
| Ablações, 37 bases | 2.265 | ~US$ 544 |

Em plano por assinatura isso não vira fatura: consome limite de uso. O número sai
de `total_cost_usd` no envelope do `--output-format json`.

## Resultados medidos

Piloto de 5 redações nota 1.000 (Cartilha 2022), 25 invocações por rodada, Opus.
**US$ 5,70** na primeira rodada, **US$ 1,57** na segunda (só a C1 reexecutada; o
resto veio do cache).

**Portão A: PASSOU** nas duas rodadas — todas as competências em 160 ou 200, todos
os totais acima de 900.

O piloto expôs um viés sistemático na Competência I: **160 em 5 de 5**. O
cruzamento com o comentário do Inep mostrou o mecanismo — a skill **achava os
desvios que o Inep contou** e acrescentava minúcias prescritivas por cima, lendo
quatro itens distintos como "reincidência".

Correção: `references/ancoras-c1.md`, gerado da Parte 2 das Cartilhas — 22
redações nota 1.000 com o comentário do(a) avaliador(a) nomeando os desvios que
ele de fato contou. É a Parte 2 calibrando a Parte 1, que é para isso que ela
existe, e não ajuste ao gabarito.

| Redação (Inep deu 200) | C1 sem âncoras | C1 com âncoras |
|---|---|---|
| 2022-01 | 160 | 160 |
| 2022-02 | 160 | **200** |
| 2022-03 | 160 | **200** |
| 2022-04 | 160 | **200** |
| 2022-05 | 160 | **200** |

As redações são identificadas por edição da Cartilha e índice. Nem aqui nem em
`references/` aparece nome de participante.

De 0/5 para 4/5. O caso remanescente é desacordo defensável, não defeito: a skill
aplica a regra de reincidência ao encontrar três desvios do mesmo tipo (regência)
e aponta um erro ortográfico real — "construírem **ser** verdadeiro 'eu'" — que o
comentário do Inep, ao dizer que "o texto não apresenta desvios de escrita", não
menciona.

**Ressalva:** isto foi medido em 5 redações de uma única edição. Não é o portão A
fechado, e não diz nada sobre discriminação — para isso é o portão B, que ainda
não rodou.

## Estado

| Etapa | Situação |
|---|---|
| Fontes oficiais com procedência | ✅ |
| Rubrica das 5 competências + anulação | ✅ conferida contra o render, com teste de regressão |
| Corpus oficial (37 redações) | ✅ com teste de integridade |
| Skill | ✅ |
| Ablações (416) | ✅ |
| Métricas e portões | ✅ testados com corretores sintéticos |
| Piloto (5 redações, portão A) | ✅ passou; viés da C1 achado e corrigido |
| Portão A completo (37 redações) | ⬜ ~185 invocações, ~US$ 44 |
| Portão B (ablações) | ⬜ ~615 invocações com 10 bases, ~US$ 148 |
| Essay-BR (portões C e E) | ⬜ conjunto ainda não baixado nem particionado |

Enquanto os portões C e E não rodarem, **não há número de concordância** — e o
projeto não deve afirmar nenhum.

## Ressalvas

1. **Contaminação.** As redações nota 1.000 são públicas desde 2012 e
   provavelmente estão na memória do modelo. O portão A é vulnerável a isso; o
   portão B é parcialmente imune, porque as ablações são geradas aqui.
2. **Digitado ≠ manuscrito.** A prova real é manuscrita. Enquanto a entrada for
   texto digitado, a Competência I é medida numa distribuição diferente da real.
3. **A skill apodrece anualmente.** `oficial/fontes.md` fixa a edição usada;
   migrar exige rodar os portões de novo contra a cartilha nova.
4. **C1 e C3 são as mais difíceis.** Os descritores da C1 separam níveis por
   quantidade vaga de desvios ("poucos", "alguns", "muitos") sem limiar numérico.
   Se o QWK ficar abaixo da barra nessas competências, a saída honesta é publicar
   o número por competência e marcá-las como baixa confiança — não relaxar a barra
   depois de ver o resultado.

## Licença

[MIT](LICENSE) — livre para usar, modificar e distribuir.

A licença cobre o **código e a documentação deste repositório**. Ela não cobre o
material do Inep: as Cartilhas em `oficial/pdfs/`, os descritores transcritos em
`references/` e os comentários de avaliador(a) são obra do Inep, reproduzidos aqui
como referência, com URL e sha256 em `oficial/fontes.md`.

## Contribuindo

Issue e pull request são bem-vindos. Duas regras valem para qualquer mudança:

- **Nada de texto de redação real no repositório.** Redação de participante e
  folha de prova ficam de fora — veja [o que não é versionado](#o-que-não-é-versionado).
- **Barra não se relaxa depois de ver o resultado.** Portão que reprovou é
  reportado como reprovado; portão sem dados é `NAO EXECUTADO`.

Mudança na rubrica exige rodar `scripts/tests/test_referencias.py`, que compara
cada descritor com o render em imagem da página oficial.
