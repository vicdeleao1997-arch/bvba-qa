#!/usr/bin/env bash
#
# Sincroniza o repositorio da BVBA entre as maquinas. Roda no MacBook (e em
# Linux/WSL). A versao do Windows 11 e o sincronizar.ps1 ao lado.
#
# O que faz, em ordem:
#   1. tranca, para duas execucoes nunca se atropelarem
#   2. recusa rodar se ha um merge/rebase pendente na sua frente
#   3. barra dado de cliente e credencial antes de qualquer commit
#   4. comita o que voce mexeu localmente
#   5. traz o que a outra maquina mandou (rebase, nunca merge sujo)
#   6. se o codigo mudou, roda os 156 testes antes de publicar
#   7. envia
#
# Nunca usa --force. Nunca descarta trabalho. Em conflito real ele para,
# desfaz o rebase e avisa — o repositorio fica exatamente como estava.
#
#   ./sinc/sincronizar.sh              # sincroniza
#   ./sinc/sincronizar.sh --simular    # mostra o que faria, sem escrever nada
#   ./sinc/sincronizar.sh --silencioso # sem cor nem enfeite (usado pelo agendador)

set -uo pipefail

SIMULAR=0
SILENCIOSO=0
for arg in "$@"; do
  case "$arg" in
    --simular)    SIMULAR=1 ;;
    --silencioso) SILENCIOSO=1 ;;
    -h|--help)    sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Opcao desconhecida: $arg" >&2; exit 64 ;;
  esac
done

# --- localizacao -------------------------------------------------------------
RAIZ="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Nao estou dentro de um repositorio git." >&2; exit 65
}
cd "$RAIZ" || exit 65

DIR_LOG="$RAIZ/sinc/.log"
ARQ_LOG="$DIR_LOG/sincronizar.log"
MARCA_PROBLEMA="$DIR_LOG/PROBLEMA.txt"
TRAVA="$DIR_LOG/.trava"
mkdir -p "$DIR_LOG"

MAQUINA="$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo desconhecida)"
AGORA="$(date '+%Y-%m-%d %H:%M:%S')"

# --- saida -------------------------------------------------------------------
registrar() {
  printf '%s [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$MAQUINA" "$*" >> "$ARQ_LOG"
  [ "$SILENCIOSO" -eq 1 ] || printf '%s\n' "$*"
}

avisar_humano() {
  # Notificacao de sistema. Se falhar, o log e o arquivo PROBLEMA.txt continuam
  # valendo — notificacao quebrada nunca derruba a sincronia.
  local titulo="$1" texto="$2"
  if command -v osascript >/dev/null 2>&1; then
    osascript -e "display notification \"${texto//\"/}\" with title \"${titulo//\"/}\"" >/dev/null 2>&1 || true
  elif command -v notify-send >/dev/null 2>&1; then
    notify-send "$titulo" "$texto" >/dev/null 2>&1 || true
  fi
}

parar_com_problema() {
  local codigo="$1"; shift
  registrar "PARADO: $*"
  { echo "Sincronia parada em $AGORA na maquina $MAQUINA"; echo; echo "$*"; echo
    echo "O repositorio NAO foi alterado de forma destrutiva. Nada foi perdido."
    echo "Detalhes em: $ARQ_LOG"
  } > "$MARCA_PROBLEMA"
  avisar_humano "BVBA — sincronia parada" "$*"
  exit "$codigo"
}

# --- trava -------------------------------------------------------------------
# mkdir e atomico: ou cria, ou falha. Serve de mutex sem depender de flock,
# que nao existe no macOS de fabrica.
if ! mkdir "$TRAVA" 2>/dev/null; then
  if [ -d "$TRAVA" ]; then
    # `find -mmin` em vez de `stat`: o stat tem sintaxe incompativel entre o
    # macOS (BSD, -f %m) e o Linux/WSL (GNU, -c %Y), e o GNU ainda por cima
    # aceita `-f %m` sem erro e devolve outra coisa. O find se comporta igual
    # nos dois.
    if [ -n "$(find "$TRAVA" -maxdepth 0 -mmin +30 2>/dev/null)" ]; then
      registrar "trava parada ha mais de 30 min, presumo execucao morta — removendo"
      rm -rf "$TRAVA"
      mkdir "$TRAVA" 2>/dev/null || exit 75
    else
      registrar "outra sincronia em andamento — saindo sem fazer nada"
      exit 0
    fi
  fi
fi
trap 'rm -rf "$TRAVA"' EXIT

# --- estado do repositorio ---------------------------------------------------
RAMO="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
[ "$RAMO" = "HEAD" ] && parar_com_problema 66 \
  "O repositorio esta em HEAD destacado (detached HEAD). Rode: git checkout main"

if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ] || [ -f .git/MERGE_HEAD ]; then
  parar_com_problema 67 \
    "Ha um merge ou rebase pela metade neste repositorio. Termine ou cancele antes: git rebase --abort  (ou  git merge --abort)"
fi

# --- barreira de dado sensivel ----------------------------------------------
# O .gitignore ja bloqueia os padroes. Isto e o segundo cadeado, para o caso de
# alguem ter feito `git add -f` ou de um padrao novo escapar. Regra da marca:
# base de telefones e credencial NUNCA entram no Git — o repo e publico.
PADROES_PROIBIDOS='(telefone|contatos|clientes|publico-personalizado|E164)[^/]*\.csv$|\.(pfx|p12|pem|key)$|(^|/)\.env$'

verificar_sensivel() {
  local lista
  lista="$(git diff --cached --name-only 2>/dev/null | grep -Ei "$PADROES_PROIBIDOS" || true)"
  if [ -n "$lista" ]; then
    git reset -q HEAD -- $lista 2>/dev/null || true
    parar_com_problema 68 \
      "Bloqueei o envio: arquivo com cara de dado de cliente ou credencial foi para o commit. Tirei do stage. Arquivos: $(echo "$lista" | tr '\n' ' ')"
  fi
}

# --- 1. comitar o que mudou aqui --------------------------------------------
MUDANCAS="$(git status --porcelain)"
if [ -n "$MUDANCAS" ]; then
  N="$(printf '%s\n' "$MUDANCAS" | wc -l | tr -d ' ')"
  if [ "$SIMULAR" -eq 1 ]; then
    registrar "[simulacao] comitaria $N arquivo(s):"
    printf '%s\n' "$MUDANCAS" | sed 's/^/    /'
  else
    git add -A
    verificar_sensivel
    if git diff --cached --quiet; then
      registrar "nada para comitar depois do filtro"
    else
      git commit -q -m "sync($MAQUINA): $N arquivo(s) — $AGORA" || \
        parar_com_problema 69 "git commit falhou. Veja $ARQ_LOG"
      registrar "comitado: $N arquivo(s)"
    fi
  fi
else
  registrar "nada mudou aqui"
fi

# --- 2. buscar o que veio da outra maquina ----------------------------------
tentativa=0
until git fetch -q origin "$RAMO" 2>>"$ARQ_LOG"; do
  tentativa=$((tentativa+1))
  [ "$tentativa" -ge 4 ] && parar_com_problema 70 \
    "Nao consegui falar com o GitHub depois de 4 tentativas. Sem internet, ou a credencial expirou. Teste: git ls-remote origin"
  sleep $((2**tentativa))
done

ATRAS="$(git rev-list --count "HEAD..origin/$RAMO" 2>/dev/null || echo 0)"
FRENTE="$(git rev-list --count "origin/$RAMO..HEAD" 2>/dev/null || echo 0)"
registrar "estado: $FRENTE commit(s) a enviar, $ATRAS a receber"

if [ "$ATRAS" -gt 0 ]; then
  if [ "$SIMULAR" -eq 1 ]; then
    registrar "[simulacao] traria $ATRAS commit(s) por rebase"
  elif ! git rebase -q "origin/$RAMO" 2>>"$ARQ_LOG"; then
    git rebase --abort 2>/dev/null || true
    parar_com_problema 71 \
      "Conflito real: voce e a outra maquina editaram as mesmas linhas. Desfiz o rebase, seu trabalho esta intacto no commit local. Resolva a mao: git pull --rebase"
  else
    registrar "recebido: $ATRAS commit(s) da outra maquina"
  fi
fi

# --- 3. portao dos testes ----------------------------------------------------
# So roda quando os commits a enviar tocam codigo. Doc e planilha passam direto.
CAMINHOS_CODIGO="agente_drop testes ferramentas .github"
FRENTE="$(git rev-list --count "origin/$RAMO..HEAD" 2>/dev/null || echo 0)"

if [ "$FRENTE" -gt 0 ] && [ "$SIMULAR" -eq 0 ]; then
  if git diff --name-only "origin/$RAMO...HEAD" -- $CAMINHOS_CODIGO 2>/dev/null | grep -q .; then
    PY="$(command -v python3 || command -v python || true)"
    if [ -z "$PY" ]; then
      registrar "AVISO: codigo mudou mas nao achei python — enviando sem testar"
    else
      registrar "codigo mudou — rodando os testes antes de enviar"
      if ! "$PY" -m unittest discover -s testes -t . >>"$ARQ_LOG" 2>&1; then
        registrar "TESTES FALHARAM — seu trabalho esta comitado aqui, mas NAO foi enviado"
        { echo "Sincronia segurou o envio em $AGORA na maquina $MAQUINA"; echo
          echo "Os testes do agente de drop falharam. Seu trabalho esta salvo no"
          echo "commit local — nada foi perdido — mas nao subiu, para nao quebrar"
          echo "a outra maquina."; echo
          echo "Rode para ver o erro:"
          echo "  python3 -m unittest discover -s testes -t ."; echo
          echo "Corrija e a proxima sincronia envia sozinha."
        } > "$MARCA_PROBLEMA"
        avisar_humano "BVBA — envio segurado" "Testes falharam. Trabalho salvo local, nao enviado."
        exit 72
      fi
      registrar "testes passaram"
    fi
  fi
fi

# --- 4. enviar ---------------------------------------------------------------
if [ "$FRENTE" -gt 0 ]; then
  if [ "$SIMULAR" -eq 1 ]; then
    registrar "[simulacao] enviaria $FRENTE commit(s) para origin/$RAMO"
  else
    tentativa=0
    until git push -q origin "$RAMO" 2>>"$ARQ_LOG"; do
      tentativa=$((tentativa+1))
      if [ "$tentativa" -ge 4 ]; then
        parar_com_problema 73 \
          "Nao consegui enviar depois de 4 tentativas. Se a outra maquina publicou nesse meio tempo, rode de novo — a proxima passada resolve."
      fi
      sleep $((2**tentativa))
      git fetch -q origin "$RAMO" 2>/dev/null || true
      git rebase -q "origin/$RAMO" 2>/dev/null || { git rebase --abort 2>/dev/null || true; }
    done
    registrar "enviado: $FRENTE commit(s)"
  fi
fi

# --- fim ---------------------------------------------------------------------
rm -f "$MARCA_PROBLEMA"
if [ "$SIMULAR" -eq 1 ]; then
  registrar "simulacao terminada — nada foi escrito"
else
  registrar "em dia ($(git rev-parse --short HEAD))"
fi

# Log nao cresce para sempre: corta em 2000 linhas.
if [ "$(wc -l < "$ARQ_LOG" 2>/dev/null || echo 0)" -gt 2000 ]; then
  tail -1000 "$ARQ_LOG" > "$ARQ_LOG.tmp" && mv "$ARQ_LOG.tmp" "$ARQ_LOG"
fi
exit 0
