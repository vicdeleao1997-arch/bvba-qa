#!/usr/bin/env bash
#
# rodar.sh — roda toda a bateria de testes do vault.
#
# Verifica o motor de sincronia (scripts/sync.sh) e os instaladores. Rode isto
# antes de mexer em qualquer coisa dentro de scripts/ — é o que garante que a
# sincronia continua sem perder nota nenhuma.
#
#   ./scripts/testes/rodar.sh

set -uo pipefail

AQUI="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd -- "${AQUI}/../.." && pwd)"

FALHAS=0
executar() { # $1 = nome, resto = comando
  local nome="$1"; shift
  printf '\n\033[1m######  %s  ######\033[0m\n' "${nome}"
  if "$@"; then
    printf '\033[32m>>> %s: OK\033[0m\n' "${nome}"
  else
    printf '\033[31m>>> %s: FALHOU\033[0m\n' "${nome}"
    FALHAS=$((FALHAS + 1))
  fi
}

printf '\n\033[1m######  Análise estática  ######\033[0m\n'
if command -v shellcheck >/dev/null 2>&1; then
  if LC_ALL=C.UTF-8 shellcheck -S style "${REPO}/scripts"/*.sh "${AQUI}"/*.sh; then
    printf '\033[32m>>> shellcheck: OK\033[0m\n'
  else
    printf '\033[31m>>> shellcheck: FALHOU\033[0m\n'; FALHAS=$((FALHAS + 1))
  fi
else
  printf '  (shellcheck não instalado — análise pulada)\n'
fi

# Os arquivos de configuração do Obsidian precisam ser JSON válido, senão o app
# descarta a configuração inteira em silêncio.
printf '\n\033[1m######  JSON do vault  ######\033[0m\n'
if command -v jq >/dev/null 2>&1; then
  ruim=0
  while IFS= read -r f; do
    if jq empty "$f" 2>/dev/null; then printf '  ok   %s\n' "${f#"${REPO}/"}"
    else printf '  ERRO %s\n' "${f#"${REPO}/"}"; ruim=1; fi
  done < <(find "${REPO}/.obsidian" -name '*.json' 2>/dev/null)
  if [ "${ruim}" -eq 0 ]; then printf '\033[32m>>> JSON: OK\033[0m\n'
  else printf '\033[31m>>> JSON: FALHOU\033[0m\n'; FALHAS=$((FALHAS + 1)); fi
else
  printf '  (jq não instalado — verificação pulada)\n'
fi

executar "Sincronia entre dois PCs" bash "${AQUI}/teste-sync.sh"
executar "Seleção de downloads"     bash "${AQUI}/teste-url.sh"
executar "Integração com o vault"   bash "${AQUI}/teste-integracao.sh"
executar "Portão de testes"         bash "${AQUI}/teste-portao.sh"

# O agente de drop é o único código de verdade do repositório, e é ele que o
# portão protege. Se esta suíte quebrar, a sincronia passa a segurar todo envio
# que toque código — então ela faz parte da bateria, não é um extra.
printf '\n\033[1m######  Agente de drop (156 testes)  ######\033[0m\n'
if PY_BIN="$(command -v python3 || command -v python || true)"; [ -n "${PY_BIN}" ]; then
  if ( cd "${REPO}" && PYTHONDONTWRITEBYTECODE=1 "${PY_BIN}" -m unittest discover -s testes -t . 2>&1 | tail -3 ); then
    printf '\033[32m>>> Agente de drop: OK\033[0m\n'
  else
    printf '\033[31m>>> Agente de drop: FALHOU\033[0m\n'; FALHAS=$((FALHAS + 1))
  fi
else
  printf '  (python não encontrado — testes do agente pulados)\n'
fi

if command -v pwsh >/dev/null 2>&1; then
  executar "Instalador do Windows" pwsh -NoProfile -File "${AQUI}/teste-ps.ps1"
else
  printf '\n  (pwsh não instalado — testes do instalador Windows pulados)\n'
fi

printf '\n============================================\n'
if [ "${FALHAS}" -eq 0 ]; then
  printf '\033[32mTUDO PASSOU\033[0m\n'
else
  printf '\033[31m%s SUÍTE(S) FALHARAM\033[0m\n' "${FALHAS}"
fi
printf '============================================\n'
exit "${FALHAS}"
