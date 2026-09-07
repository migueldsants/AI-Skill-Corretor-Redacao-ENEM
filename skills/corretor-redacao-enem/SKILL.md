---
name: corretor-redacao-enem
description: Corrige uma redação do Enem pela Matriz de Referência oficial do Inep, atribuindo nota de 0 a 200 em cada uma das cinco competências, com o descritor oficial citado como justificativa. Use quando o pedido for corrigir, avaliar ou dar nota a uma redação do Enem, ou estimar nota por competência.
---

# Corretor de redação do Enem

Avalia uma redação dissertativa-argumentativa pelos critérios da *Cartilha do(a)
Participante* do Inep. Toda a rubrica em `references/` é transcrição literal do
documento oficial — nenhuma paráfrase, nenhum critério inventado.

## O que esta skill afirma e o que não afirma

**Afirma:** aplicar a Matriz de Referência oficial de forma consistente e
auditável, citando o descritor que sustenta cada nota.

**Não afirma:** reproduzir a nota que o Inep daria. O Inep usa dois
avaliadores(as) independentes e aciona um(a) terceiro(a) quando eles divergem —
nem dois humanos treinados concordam sempre. Não existe base pública com texto
de redação e notas por competência atribuídas pelo Inep, então nenhuma
concordância com o Inep pode ser medida nem prometida.

## Entrada

- **Obrigatório:** o texto da redação e o **tema** da proposta.
- **Opcional:** os textos motivadores. Sem eles, o critério de cópia
  (`copia_dos_textos_motivadores`) fica não avaliado e isso deve ser dito.

Se o tema não for informado, **pergunte**. Sem tema não há como julgar fuga ao
tema nem a Competência II, e supor o tema a partir do próprio texto torna a
avaliação circular.

## Modos

Leia os argumentos da invocação:

- **Sem argumentos** (uso normal): faça a correção completa — Etapa 0 e depois
  as cinco competências, uma de cada vez.
- **`--competencia N`** (N de 1 a 5): avalie **somente** aquela competência e
  emita apenas o bloco JSON dela. Não leia as rubricas das outras, não comente
  as outras, não some nota total. Este modo existe para o harness de avaliação
  medir cada competência sem efeito halo.
- **`--gate`**: execute somente a Etapa 0 e emita apenas o JSON dos portões.
- **`--json`**: acrescente o bloco JSON ao final, além da resposta em prosa.

## Procedimento

Execute nesta ordem. Não pule etapas nem junte competências numa única análise.

### Etapa 0 — Portões de anulação

Leia `references/zeradores.md`. Avalie **apenas** os critérios do Grupo A
(verificáveis no texto). Para cada um, decida se disparou e escreva uma frase de
justificativa.

- Se algum disparar: a redação recebe **0** e **nenhuma competência é
  pontuada**. Nomeie o critério e encerre.
- Os critérios do Grupo B exigem a folha física. Reporte-os como **não
  avaliados** — nunca presuma que estão em ordem.
- Aplique a ressalva sobre contagem de linhas: não anule texto limítrofe apenas
  por extensão estimada.

### Etapas 1 a 5 — Uma competência por vez, isoladamente

Para cada N pedido, **em análises separadas**:

1. Leia `references/competencia-N.md` — e **somente** esse arquivo.
   Para N = 1, leia **também** `references/ancoras-c1.md`.
2. Releia a redação inteira com essa competência em mente.
3. Escolha o nível cujo descritor melhor descreve o texto, comparando os seis
   descritores entre si.
4. Emita a saída no formato abaixo.

### Competência I — contagem de desvios

O descritor de 200 aceita desvio "como excepcionalidade e quando não
caracterizarem reincidência", mas não diz quantos. Quem diz é
`references/ancoras-c1.md`: 22 redações que o Inep pontuou 200, com o
comentário do(a) avaliador(a) nomeando os desvios contados. Leia essas âncoras
**antes** de fechar a nota.

Dois erros a evitar, ambos observados em medição:

- **Contar demais.** Preferência de estilo não é desvio. Ponto fino de
  prescrição sobre o qual gramáticos divergem não é desvio. Antes de listar um
  item, pergunte se um(a) avaliador(a) do Inep o nomearia — as âncoras mostram
  exatamente o que ele nomeia.
- **Confundir quantidade com reincidência.** Reincidência é o **mesmo tipo** de
  desvio se repetindo. Dois desvios de tipos distintos não são reincidência, e
  as âncoras mostram redações com um e com dois desvios recebendo 200.

**Regra de isolamento:** ao avaliar a competência N, não consulte nem leve em
conta a nota das outras. Isso evita efeito halo — uma nota alta em C2 puxando
C3 para cima. Se perceber que está justificando uma nota por causa de outra,
refaça.

### Saída por competência

Em prosa:

```
Competência N — <nota> pontos
Descritor aplicado: "<transcrição literal do descritor escolhido>"
Evidências: <2 a 4 trechos citados da redação, entre aspas>
Justificativa: <por que este descritor e não o vizinho acima e o de baixo>
Confiança: alta | média | baixa
```

`Descritor aplicado` é obrigatório e deve ser **cópia literal** do arquivo de
referência. Se você não consegue citar o descritor, não tem base para a nota.

A justificativa precisa comparar com os **níveis vizinhos**. "Dei 160 porque o
texto é bom" não é justificativa; "dei 160 e não 200 porque há dois desvios
gramaticais reincidentes (X e Y), e o nível 200 só aceita desvio como
excepcionalidade sem reincidência" é.

### Competência V — direitos humanos

Desrespeito aos direitos humanos zera **apenas a Competência V**. A redação
**não** é anulada por isso. Essa regra mudou: material anterior a 2017 dizia que
anulava tudo. Siga `references/zeradores.md`, Grupo C.

Para a proposta de intervenção, verifique explicitamente os cinco elementos:
**ação**, **agente**, **modo/meio**, **efeito** e **detalhamento**. Diga quais
estão presentes e quais faltam.

## Bloco JSON

Nos modos `--competencia`, `--gate` e `--json`, termine a resposta com um bloco
```json fechado, e nada depois dele. A nota tem de ser um dos seis níveis
oficiais: 0, 40, 80, 120, 160, 200.

Para `--competencia N`:

```json
{"competencia": "cN", "nota": 160, "descritor_citado": "...",
 "evidencias": ["...", "..."], "justificativa": "...", "confianca": "alta"}
```

Para `--gate`:

```json
{"anulada": false, "criterio": null, "grupo_a": {"fuga_total_ao_tema": false},
 "nao_avaliados": ["em_branco", "identificacao_indevida", "ilegivel"]}
```

Para a correção completa com `--json`:

```json
{"c1": {"nota": 160, "confianca": "media"}, "c2": {"nota": 200, "confianca": "alta"},
 "c3": {"nota": 160, "confianca": "baixa"}, "c4": {"nota": 200, "confianca": "alta"},
 "c5": {"nota": 200, "confianca": "alta"}, "total": 920, "anulada": false}
```

## Resultado final (modo completo)

Uma tabela com as cinco competências, as notas, o total (soma, máximo 1000) e a
lista de critérios não avaliados por dependerem da folha física.

Declare a confiança por competência. As Competências I e III são as mais
difíceis de julgar com precisão: os descritores da C1 separam níveis por
quantidade vaga de desvios ("poucos", "alguns", "muitos") sem limiar numérico, e
a C3 depende de julgar autoria e organização argumentativa. Marque `baixa`
nesses casos em vez de fingir precisão.

## Padronização

Esta skill roda dentro do Claude Code, que não expõe controle de amostragem —
não há `temperature` para zerar. A consistência vem de quatro escolhas:

1. O descritor é **citado literalmente**, não parafraseado.
2. Cada competência é julgada contra **um único arquivo** de rubrica.
3. A justificativa é obrigada a **comparar com os níveis vizinhos**.
4. A nota é restrita aos **seis níveis oficiais**.

Duas execuções ainda podem divergir. A variação é medida, não presumida:
`scripts/eval/report.py` reporta o test-retest como métrica própria, separada da
acurácia. Se ela for alta, rode três vezes e tome a **mediana** por competência
— nunca a média, que produz notas fora da escala.

## Arquivos de referência

| Arquivo | Conteúdo |
|---|---|
| `references/competencia-1.md` … `-5.md` | Os seis níveis de cada competência, transcritos da Cartilha |
| `references/ancoras-c1.md` | 22 comentários do Inep sobre redações nota 1.000, calibrando a contagem de desvios da Competência I |
| `references/zeradores.md` | Critérios de anulação, agrupados por verificabilidade |

Tudo em `references/` é gerado por `scripts/tools/` a partir dos PDFs oficiais
em `oficial/pdfs/`; a procedência, com URL e sha256, está em `oficial/fontes.md`
na raiz do projeto.

O corpus de calibração (37 redações comentadas pelo Inep) **não é versionado** —
é texto de redação real. Regere-o dos PDFs com
`scripts/tools/extrair_redacoes.py`.
