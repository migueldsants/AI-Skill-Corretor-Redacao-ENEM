# -*- coding: utf-8 -*-
"""Executa a skill pelo harness do agente e grava as notas por competência.

A skill NÃO bate na API. Quem a executa é o CLI do agente, que carrega o
SKILL.md, resolve `references/` e aplica a rubrica. Reimplementar os prompts
como chamadas de SDK mediria o reimplementador, não a skill.

Desenho, e o porquê de cada escolha:

- **Uma invocação por competência** (`--competencia N`). Processos separados são
  contextos separados: é o isolamento que impede efeito halo (nota alta em C2
  puxando C3). Dentro de uma única sessão as cinco competências se veriam.
- **`--output-format json`**, que devolve envelope com `result`, `total_cost_usd`
  e `usage`. O custo real sai daí, não de estimativa.
- **`--allowed-tools Read`**, para a skill só poder ler as próprias referências.
- **Cache em `raw/`**, uma invocação por arquivo, para poder retomar uma rodada
  interrompida sem repagar o que já rodou.

Uso:
    python skills/corretor-redacao-enem/scripts/eval/run.py \n        --dataset oficial/redacoes --saida results/v1/oficial.jsonl --dry-run
    python skills/corretor-redacao-enem/scripts/eval/run.py \n        --dataset oficial/redacoes --saida results/v1/oficial.jsonl --paralelo 4
"""
import argparse, concurrent.futures as cf, json, pathlib, random, re, subprocess, sys, time

SKILL = "corretor-redacao-enem"
COMPETENCIAS = ["c1", "c2", "c3", "c4", "c5"]
NIVEIS = [0, 40, 80, 120, 160, 200]

# Medido numa invocação real (Opus, uma competência, redação de ~3,4 mil chars):
# US$ 0,24 e ~41 s. O grosso é o prompt de sistema do próprio agente, que
# entra em cache entre chamadas — a estimativa é teto, não piso.
USD_POR_INVOCACAO = 0.24


def carregar(caminho):
    p = pathlib.Path(caminho)
    if p.is_dir():
        return [{"id": r["id"], "tema": r["tema"], "texto": r["texto"]}
                for r in (json.loads(a.read_text(encoding="utf-8"))
                          for a in sorted(p.glob("*.json")))]
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def montar_prompt(reg, comp):
    """`comp` é "c1".."c5", ou "gate" para a Etapa 0 (portões de anulação)."""
    modo = "--gate" if comp == "gate" else f"--competencia {comp[1]}"
    return (f"/{SKILL} {modo}\n\n"
            f"Tema da proposta: {reg['tema']}\n\n"
            f"Redação:\n\n{reg['texto']}\n")


def extrair_json(texto):
    """Último bloco ```json da resposta. A skill manda fechar com ele e não
    escrever nada depois; pegar o último é a leitura tolerante disso."""
    blocos = re.findall(r"```json\s*(.*?)```", texto, re.S)
    for b in reversed(blocos):
        try:
            return json.loads(b)
        except json.JSONDecodeError:
            continue
    return None


def invocar(reg, comp, modelo, timeout, cache_dir, tentativas=3):
    destino = cache_dir / f"{reg['id'].replace('::', '__')}__{comp}.json"
    if destino.exists():
        d = json.loads(destino.read_text(encoding="utf-8"))
        d["do_cache"] = True
        return d

    cmd = ["claude", "-p", "--output-format", "json",
           "--allowed-tools", "Read", "--no-session-persistence"]
    if modelo:
        cmd += ["--model", modelo]

    # Sessões concorrentes esbarram em limite de uso e o CLI sai com 1. A falha
    # é transitória: a mesma invocação isolada passa. Recuo exponencial com
    # jitter, para as tentativas não voltarem todas ao mesmo tempo.
    proc = None
    for tentativa in range(tentativas):
        inicio = time.time()
        try:
            proc = subprocess.run(cmd, input=montar_prompt(reg, comp), capture_output=True,
                                  text=True, encoding="utf-8", timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"id": reg["id"], "competencia": comp, "erro": "timeout",
                    "segundos": round(time.time() - inicio, 1)}
        if proc.returncode == 0:
            break
        if tentativa < tentativas - 1:
            time.sleep(2 ** tentativa * 15 + random.uniform(0, 10))

    if proc.returncode != 0:
        return {"id": reg["id"], "competencia": comp,
                "erro": f"exit {proc.returncode} apos {tentativas} tentativas",
                "stderr": (proc.stderr or "")[:400]}
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"id": reg["id"], "competencia": comp, "erro": "envelope invalido",
                "stdout": proc.stdout[:400]}
    if envelope.get("is_error"):
        return {"id": reg["id"], "competencia": comp, "erro": "sessao com erro",
                "subtype": envelope.get("subtype")}

    payload = extrair_json(envelope.get("result", ""))
    saida = {
        "id": reg["id"], "competencia": comp,
        "avaliacao": payload,
        "usd": envelope.get("total_cost_usd"),
        "segundos": round(envelope.get("duration_ms", 0) / 1000, 1),
        "sessao": envelope.get("session_id"),
    }
    if payload is None:
        saida["erro"] = "sem bloco json na resposta"
    elif comp == "gate":
        if "anulada" not in payload:
            saida["erro"] = "gate sem campo 'anulada'"
    elif payload.get("nota") not in NIVEIS:
        saida["erro"] = f"nota fora da escala: {payload.get('nota')!r}"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    return saida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True,
                    help="arquivo .jsonl ou diretório com um .json por redação")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--competencias", default="c1,c2,c3,c4,c5")
    ap.add_argument("--com-gate", action="store_true",
                    help="acrescenta uma invocação por redação para a Etapa 0 "
                         "(portões de anulação). Custa +20%% e é o único jeito de "
                         "verificar que a skill não anula redação boa.")
    ap.add_argument("--modelo", default="opus")
    ap.add_argument("--paralelo", type=int, default=2,
                    help="sessoes simultaneas. Acima de 2 o limite de uso comeca "
                         "a derrubar invocacoes; ha retentativa, mas custa tempo.")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    comps = [c.strip() for c in a.competencias.split(",") if c.strip()]
    if a.com_gate:
        comps = ["gate"] + comps
    regs = carregar(a.dataset)
    if a.limite:
        regs = regs[:a.limite]
    saida = pathlib.Path(a.saida)
    cache_dir = saida.parent / "raw"
    tarefas = [(r, c) for r in regs for c in comps]

    ja_feitas = sum(1 for r, c in tarefas
                    if (cache_dir / f"{r['id'].replace('::', '__')}__{c}.json").exists())
    faltam = len(tarefas) - ja_feitas
    print(f"{len(regs)} redacoes x {len(comps)} competencias = {len(tarefas)} invocacoes")
    print(f"  em cache: {ja_feitas} | a rodar: {faltam} "
          f"| ~US$ {faltam * USD_POR_INVOCACAO:.2f} | modelo: {a.modelo}")

    if a.dry_run:
        print("\nexemplo de invocacao:")
        print(f"  claude -p --output-format json --allowed-tools Read "
              f"--no-session-persistence --model {a.modelo}")
        print(f"  prompt: /{SKILL} --competencia 1 + tema + redacao "
              f"({len(montar_prompt(regs[0], 'c1'))} chars)")
        print("\n(dry-run: nada foi executado)")
        return 0

    cache_dir.mkdir(parents=True, exist_ok=True)
    resultados, feitas = [], 0
    with cf.ThreadPoolExecutor(max_workers=a.paralelo) as ex:
        futuros = {ex.submit(invocar, r, c, a.modelo, a.timeout, cache_dir): (r, c)
                   for r, c in tarefas}
        for fut in cf.as_completed(futuros):
            res = fut.result()
            resultados.append(res)
            feitas += 1
            marca = "cache" if res.get("do_cache") else f"{res.get('segundos', '?')}s"
            estado = res.get("erro") or (res.get("avaliacao") or {}).get("nota")
            print(f"  [{feitas}/{len(tarefas)}] {res['id']} {res['competencia']}: "
                  f"{estado} ({marca})")

    # agrega por redação, no formato que o report.py consome
    por_id = {}
    for res in resultados:
        alvo = por_id.setdefault(res["id"], {"id": res["id"], "notas": {}, "erros": {}})
        if res.get("erro"):
            alvo["erros"][res["competencia"]] = res["erro"]
        elif res["competencia"] == "gate":
            alvo["gate"] = res["avaliacao"]
        else:
            alvo["notas"][res["competencia"]] = res["avaliacao"]
    for reg in regs:
        r = por_id.setdefault(reg["id"], {"id": reg["id"], "notas": {}, "erros": {"*": "ausente"}})
        r["tema"] = reg.get("tema")
        for campo in ("alvo", "severidade", "base_id", "colaterais_esperados"):
            if campo in reg:
                r[campo] = reg[campo]

    saida.parent.mkdir(parents=True, exist_ok=True)
    with open(saida, "w", encoding="utf-8") as fh:
        for reg in regs:
            fh.write(json.dumps(por_id[reg["id"]], ensure_ascii=False) + "\n")

    gasto = sum(r.get("usd") or 0 for r in resultados if not r.get("do_cache"))
    erros = sum(1 for r in resultados if r.get("erro"))
    print(f"\n-> {saida} | gasto nesta rodada: US$ {gasto:.2f} | invocacoes com erro: {erros}")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
