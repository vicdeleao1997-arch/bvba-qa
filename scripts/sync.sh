#!/usr/bin/env bash
#
# sync.sh — sincronia bidirecional do vault Obsidian (bvba-qa)
#
# Faz um ciclo completo: commita o que mudou aqui, traz o que mudou lá,
# resolve conflitos SEM PERDER NADA e envia de volta.
#
# Roda com o Obsidian aberto ou fechado. É o mesmo motor que o plugin
# obsidian-git usa por dentro, só que também funciona quando o Obsidian
# está fechado (via agendador do sistema) — é isso que fecha a "sincronia
# total".
#
# Uso:
#   scripts/sync.sh            # um ciclo de sincronia
#   scripts/sync.sh --quiet    # sem saída no terminal (para agendador)
#   scripts/sync.sh --status   # só mostra o estado, não altera nada
#
# Política de conflito: nunca sobrescreve. Se a mesma nota foi editada em
# dois PCs, a versão remota fica com o nome original e a sua vira uma cópia
# "Nota (conflito <pc> <data>).md" ao lado. Você decide depois o que fica.

set -euo pipefail

# --------------------------------------------------------------------------
# Localização e constantes
# --------------------------------------------------------------------------

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VAULT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

STATE_DIR="${VAULT_DIR}/.sync"
LOG_FILE="${STATE_DIR}/sync.log"
LOCK_DIR="${STATE_DIR}/lock"
LOG_MAX_BYTES=1048576   # 1 MB antes de rotacionar
PUSH_ATTEMPTS=4         # tentativas de push por ciclo (backoff 2s/4s/8s/16s)
SYNC_ROUNDS=5           # rodadas de merge+push antes de desistir

QUIET=0
STATUS_ONLY=0
GIT_DIR_ABS=""      # preenchido em main(), depois de validar que é um repo git

HOSTNAME_SHORT="$(uname -n | cut -d. -f1)"

# --------------------------------------------------------------------------
# Saída
# --------------------------------------------------------------------------

log() {
  local level="$1"; shift
  local line
  line="$(date '+%Y-%m-%d %H:%M:%S') [${level}] $*"
  mkdir -p "${STATE_DIR}"
  printf '%s\n' "${line}" >>"${LOG_FILE}"
  if [ "${QUIET}" -eq 0 ]; then
    if [ "${level}" = "ERRO" ]; then
      printf '%s\n' "${line}" >&2
    else
      printf '%s\n' "${line}"
    fi
  fi
}

die() {
  log ERRO "$*"
  exit 1
}

rotate_log() {
  [ -f "${LOG_FILE}" ] || return 0
  local size
  size="$(wc -c <"${LOG_FILE}" 2>/dev/null || echo 0)"
  if [ "${size}" -gt "${LOG_MAX_BYTES}" ]; then
    mv -f "${LOG_FILE}" "${LOG_FILE}.1"
  fi
}

# --------------------------------------------------------------------------
# Trava — impede dois ciclos simultâneos (agendador + plugin ao mesmo tempo)
# --------------------------------------------------------------------------

acquire_lock() {
  mkdir -p "${STATE_DIR}"
  if mkdir "${LOCK_DIR}" 2>/dev/null; then
    printf '%s\n' "$$" >"${LOCK_DIR}/pid"
    return 0
  fi

  # Trava existe. Ainda tem dono vivo?
  local old_pid=""
  [ -f "${LOCK_DIR}/pid" ] && old_pid="$(cat "${LOCK_DIR}/pid" 2>/dev/null || true)"
  if [ -n "${old_pid}" ] && kill -0 "${old_pid}" 2>/dev/null; then
    log INFO "outro ciclo de sincronia já está rodando (pid ${old_pid}); saindo"
    exit 0
  fi

  log AVISO "trava órfã encontrada (pid '${old_pid:-?}'); recuperando"
  rm -rf "${LOCK_DIR}"
  mkdir "${LOCK_DIR}" || die "não consegui criar a trava em ${LOCK_DIR}"
  printf '%s\n' "$$" >"${LOCK_DIR}/pid"
}

release_lock() {
  # shellcheck disable=SC2317  # chamada via trap
  rm -rf "${LOCK_DIR}" 2>/dev/null || true
}

# --------------------------------------------------------------------------
# Git — helpers
# --------------------------------------------------------------------------

git_v() { git -C "${VAULT_DIR}" "$@"; }

# Commit silencioso: "nada a commitar" é um resultado normal aqui, não erro.
commit_quiet() {
  git_v commit -q --no-verify "$@" >>"${LOG_FILE}" 2>&1 || return 1
  return 0
}

# O diretório .sync/ guarda log e trava — ele muda DURANTE o ciclo, então não
# pode nunca ser versionado (senão cada ciclo gera um commit novo, para sempre).
# Garantimos isso localmente, independente do .gitignore do repositório.
ensure_local_excludes() {
  local excl="${GIT_DIR_ABS}/info/exclude"
  mkdir -p "$(dirname -- "${excl}")"
  local pat
  for pat in '.sync/' '.obsidian/workspace.json' '.obsidian/workspace-mobile.json' '.trash/'; do
    grep -qxF "${pat}" "${excl}" 2>/dev/null || printf '%s\n' "${pat}" >>"${excl}"
  done

  # Auto-reparo: se .sync/ já foi versionado por engano, desversiona.
  if [ -n "$(git_v ls-files -- .sync 2>/dev/null || true)" ]; then
    git_v rm -r -q --cached -- .sync >>"${LOG_FILE}" 2>&1 || true
    log AVISO ".sync/ estava versionado por engano; removido do controle de versão"
  fi
}

ensure_identity() {
  if ! git_v config user.name >/dev/null 2>&1; then
    git_v config user.name "${USER:-obsidian}@${HOSTNAME_SHORT}"
    log INFO "git user.name não estava configurado; usei '${USER:-obsidian}@${HOSTNAME_SHORT}'"
  fi
  if ! git_v config user.email >/dev/null 2>&1; then
    git_v config user.email "${USER:-obsidian}@${HOSTNAME_SHORT}.local"
    log INFO "git user.email não estava configurado; usei um endereço local"
  fi
}

# Nome da cópia de conflito: "Nota.md" -> "Nota (conflito pc 2026-08-16 1042).md"
conflict_copy_name() {
  local path="$1"
  local dir base ext stamp
  dir="$(dirname -- "${path}")"
  base="$(basename -- "${path}")"
  stamp="$(date '+%Y-%m-%d %H%M')"

  if [[ "${base}" == *.* && "${base}" != .* ]]; then
    ext=".${base##*.}"
    base="${base%.*}"
  else
    ext=""
  fi

  local name="${base} (conflito ${HOSTNAME_SHORT} ${stamp})${ext}"
  if [ "${dir}" = "." ]; then
    printf '%s' "${name}"
  else
    printf '%s/%s' "${dir}" "${name}"
  fi
}

# Resolve TODOS os caminhos em conflito preservando as duas versões.
#
# Estágios do índice durante um merge:
#   :1 = ancestral comum   :2 = nossa versão (local)   :3 = versão remota
#
# Regra: a versão remota assume o nome original (assim os dois PCs convergem
# para o mesmo arquivo) e a nossa vira uma cópia de conflito ao lado.
resolve_conflicts() {
  local conflicted
  conflicted="$(git_v diff --name-only --diff-filter=U --relative 2>/dev/null || true)"
  [ -n "${conflicted}" ] || return 0

  local count=0
  while IFS= read -r path; do
    [ -n "${path}" ] || continue
    count=$((count + 1))

    local stages has_ours=0 has_theirs=0
    stages="$(git_v ls-files -u -- "${path}" | awk '{print $3}' | sort -u)"
    grep -qx '2' <<<"${stages}" && has_ours=1
    grep -qx '3' <<<"${stages}" && has_theirs=1

    if [ "${has_ours}" -eq 1 ] && [ "${has_theirs}" -eq 1 ]; then
      # Editado dos dois lados: preserva ambos.
      local copy
      copy="$(conflict_copy_name "${path}")"
      mkdir -p "$(dirname -- "${VAULT_DIR}/${copy}")"
      git_v show ":2:${path}" >"${VAULT_DIR}/${copy}"
      git_v show ":3:${path}" >"${VAULT_DIR}/${path}"
      git_v add -- "${path}" "${copy}"
      log AVISO "conflito em '${path}' — sua versão preservada em '${copy}'"

    elif [ "${has_ours}" -eq 1 ]; then
      # Apagado no remoto, editado aqui: mantém o nosso (não perde trabalho).
      git_v show ":2:${path}" >"${VAULT_DIR}/${path}"
      git_v add -- "${path}"
      log AVISO "'${path}' foi apagado em outro PC mas editado aqui — mantido"

    elif [ "${has_theirs}" -eq 1 ]; then
      # Apagado aqui, editado no remoto: aceita o remoto (a edição vence a exclusão).
      mkdir -p "$(dirname -- "${VAULT_DIR}/${path}")"
      git_v show ":3:${path}" >"${VAULT_DIR}/${path}"
      git_v add -- "${path}"
      log AVISO "'${path}' foi apagado aqui mas editado em outro PC — restaurado"

    else
      # Apagado dos dois lados: só confirma a exclusão.
      git_v rm -q --cached -- "${path}" 2>/dev/null || true
      rm -f -- "${VAULT_DIR}/${path}" 2>/dev/null || true
      log INFO "'${path}' apagado nos dois lados"
    fi
  done <<<"${conflicted}"

  log INFO "${count} conflito(s) resolvido(s) sem perda de conteúdo"
}

commit_local_changes() {
  git_v add -A
  if git_v diff --cached --quiet; then
    return 1   # nada para commitar
  fi
  local n
  n="$(git_v diff --cached --name-only | wc -l | tr -d ' ')"
  commit_quiet -m "vault: ${HOSTNAME_SHORT} $(date '+%Y-%m-%d %H:%M:%S') (${n} arquivo(s))" \
    || { log AVISO "não consegui commitar as alterações locais"; return 1; }
  log INFO "commit local: ${n} arquivo(s)"
  return 0
}

# Conclui um merge em andamento preservando as duas versões de cada conflito.
finish_merge() {
  local label="$1"
  if [ -z "$(git_v diff --name-only --diff-filter=U 2>/dev/null || true)" ] \
     && [ ! -f "${GIT_DIR_ABS}/MERGE_HEAD" ]; then
    return 0
  fi
  resolve_conflicts
  commit_quiet -m "sync: ${label} (${HOSTNAME_SHORT})" || true
  if [ -f "${GIT_DIR_ABS}/MERGE_HEAD" ]; then
    return 1
  fi
  return 0
}

push_with_retry() {
  local branch="$1"
  local delay=2 attempt=1
  while [ "${attempt}" -le "${PUSH_ATTEMPTS}" ]; do
    if git_v push -u origin "${branch}" >>"${LOG_FILE}" 2>&1; then
      log INFO "push enviado para origin/${branch}"
      return 0
    fi
    # Remoto andou enquanto a gente trabalhava: sinaliza para nova rodada.
    git_v fetch -q origin "${branch}" 2>/dev/null || true
    if [ -n "$(git_v log "HEAD..origin/${branch}" --oneline 2>/dev/null || true)" ]; then
      log INFO "o remoto recebeu commits novos durante o push; refazendo o merge"
      return 2
    fi
    log AVISO "push falhou (tentativa ${attempt}/${PUSH_ATTEMPTS}); nova tentativa em ${delay}s"
    sleep "${delay}"
    delay=$((delay * 2))
    attempt=$((attempt + 1))
  done
  return 1
}

# --------------------------------------------------------------------------
# Ciclo principal
# --------------------------------------------------------------------------

show_status() {
  local branch
  branch="$(git_v rev-parse --abbrev-ref HEAD)"
  printf 'Vault:  %s\n' "${VAULT_DIR}"
  printf 'Branch: %s\n' "${branch}"
  printf 'PC:     %s\n\n' "${HOSTNAME_SHORT}"

  local pending
  pending="$(git_v status --porcelain | wc -l | tr -d ' ')"
  printf 'Alterações locais ainda não enviadas: %s arquivo(s)\n' "${pending}"

  if git_v fetch -q origin "${branch}" 2>/dev/null; then
    local ahead behind
    ahead="$(git_v rev-list --count "origin/${branch}..HEAD" 2>/dev/null || echo '?')"
    behind="$(git_v rev-list --count "HEAD..origin/${branch}" 2>/dev/null || echo '?')"
    printf 'Commits à frente do remoto:  %s\n' "${ahead}"
    printf 'Commits atrás do remoto:     %s\n' "${behind}"
  else
    printf 'Não consegui falar com o remoto (offline?).\n'
  fi

  if [ -f "${LOG_FILE}" ]; then
    printf '\nÚltimas linhas do log:\n'
    tail -n 5 "${LOG_FILE}"
  fi
}

main() {
  while [ $# -gt 0 ]; do
    case "$1" in
      -q|--quiet)  QUIET=1 ;;
      -s|--status) STATUS_ONLY=1 ;;
      -h|--help)
        sed -n '2,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
        exit 0 ;;
      *) die "opção desconhecida: $1 (use --help)" ;;
    esac
    shift
  done

  command -v git >/dev/null 2>&1 || die "git não está instalado neste PC"
  git_v rev-parse --git-dir >/dev/null 2>&1 || die "${VAULT_DIR} não é um repositório git"

  if [ "${STATUS_ONLY}" -eq 1 ]; then
    show_status
    exit 0
  fi

  GIT_DIR_ABS="$(git_v rev-parse --absolute-git-dir)"

  rotate_log
  acquire_lock
  trap release_lock EXIT INT TERM

  ensure_local_excludes
  ensure_identity

  local branch
  branch="$(git_v rev-parse --abbrev-ref HEAD)"
  [ "${branch}" != "HEAD" ] || die "o vault está em HEAD destacado; rode: git checkout main"

  git_v remote get-url origin >/dev/null 2>&1 \
    || die "nenhum remoto 'origin' configurado neste vault"

  # Merge interrompido de um ciclo anterior: termina antes de seguir.
  if [ -f "${GIT_DIR_ABS}/MERGE_HEAD" ]; then
    log AVISO "merge pendente de um ciclo anterior; concluindo"
    finish_merge "conclusão de merge interrompido" \
      || die "não consegui concluir o merge pendente; abra o vault e resolva à mão"
  fi

  local round=1
  while [ "${round}" -le "${SYNC_ROUNDS}" ]; do
    commit_local_changes || true

    if ! git_v fetch -q origin "${branch}" 2>>"${LOG_FILE}"; then
      log AVISO "sem conexão com o remoto; as mudanças ficaram commitadas localmente e sobem no próximo ciclo"
      exit 0
    fi

    # Traz o remoto. Só faz merge se houver algo a trazer.
    if [ -n "$(git_v log "HEAD..origin/${branch}" --oneline 2>/dev/null || true)" ]; then
      # Fast-forward quando não há nada local (evita commits de merge vazios que
      # os dois PCs ficariam se empurrando para sempre); merge real só quando
      # os dois lados de fato divergiram.
      if ! git_v merge --no-edit "origin/${branch}" >>"${LOG_FILE}" 2>&1; then
        # Falhou sem conflitos de conteúdo? É outro problema — não mascarar.
        if [ -z "$(git_v diff --name-only --diff-filter=U 2>/dev/null || true)" ]; then
          git_v merge --abort >/dev/null 2>&1 || true
          die "o merge com origin/${branch} falhou por um motivo inesperado; veja ${LOG_FILE}"
        fi
        finish_merge "merge de origin/${branch} com conflitos preservados" \
          || die "não consegui concluir o merge automaticamente; abra o vault e resolva à mão"
      fi
      log INFO "mudanças do remoto integradas"
    fi

    # Nada a enviar? Ciclo encerrado.
    if [ -z "$(git_v log "origin/${branch}..HEAD" --oneline 2>/dev/null || true)" ]; then
      log INFO "tudo sincronizado"
      exit 0
    fi

    local rc=0
    push_with_retry "${branch}" || rc=$?
    case "${rc}" in
      0) log INFO "sincronia concluída"; exit 0 ;;
      2) round=$((round + 1)); continue ;;
      *) die "não consegui enviar para origin/${branch}; veja ${LOG_FILE}" ;;
    esac
  done

  die "o remoto mudou ${SYNC_ROUNDS} vezes seguidas durante a sincronia; tente de novo"
}

main "$@"
