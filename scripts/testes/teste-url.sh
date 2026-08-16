#!/usr/bin/env bash
# Testa a funcao url_release REAL, extraida do instalar.sh, contra nomes de
# assets iguais aos das releases oficiais. Cobre o caminho com jq e sem jq.
set -uo pipefail

# Descobre a raiz do repositorio a partir da localizacao deste script e usa um
# diretorio temporario proprio, para o teste rodar em qualquer maquina e no CI.
AQUI="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd -- "${AQUI}/../.." && pwd)"
BASE="$(mktemp -d)"
trap 'rm -rf "${BASE}"' EXIT
SRC="${REPO}/scripts/instalar.sh"
FIX="${BASE}/fix.json"
FAILS=0
ok()  { printf '  \033[32mPASSOU\033[0m  %s\n' "$*"; }
bad() { printf '  \033[31mFALHOU\033[0m  %s\n' "$*"; FAILS=$((FAILS+1)); }

# Extrai a funcao real do instalador (da assinatura ate a chave de fechamento).
eval "$(awk '/^url_release\(\) \{/,/^\}/' "$SRC")"

# Stubs abaixo sao chamados de dentro da funcao sob teste, nao daqui.
# shellcheck disable=SC2317
curl() { cat "$FIX"; }            # stub: devolve a fixture
export -f curl 2>/dev/null || true

mkfix() { printf '{"assets":[' >"$FIX"
  local first=1 n
  for n in "$@"; do
    [ $first -eq 1 ] || printf ',' >>"$FIX"; first=0
    printf '{"name":"%s","browser_download_url":"https://github.com/o/r/releases/download/v1/%s"}' "$n" "$n" >>"$FIX"
  done
  printf ']}' >>"$FIX"; }

esperar() { # $1 = descricao, $2 = padrao, $3 = nome esperado ("" = deve falhar)
  local got; got="$(url_release qualquer/repo "$2")" || got=""
  local base="${got##*/}"
  if [ "$base" = "$3" ]; then ok "$1"; else bad "$1 (esperado '$3', obtido '${base:-<nada>}')"; fi
}

for MODO in com-jq sem-jq; do
  printf '\n=== caminho %s ===\n' "$MODO"
  # shellcheck disable=SC2317  # usados por url_release, nao chamados diretamente
  if [ "$MODO" = "com-jq" ]; then tem() { command -v "$1" >/dev/null 2>&1; }
  else tem() { [ "$1" != "jq" ] && command -v "$1" >/dev/null 2>&1; }; fi

  # --- Assets reais de uma release do Obsidian ---
  mkfix "obsidian_1.8.10_amd64.deb" "obsidian_1.8.10_arm64.deb" \
        "Obsidian-1.8.10.AppImage" "Obsidian-1.8.10-arm64.AppImage" \
        "Obsidian-1.8.10.dmg" "Obsidian-1.8.10.exe" "obsidian-1.8.10.tar.gz" \
        "obsidian-1.8.10.asar.gz"

  esperar "deb amd64"                      '_amd64\.deb$'                  "obsidian_1.8.10_amd64.deb"
  esperar "deb arm64"                      '_arm64\.deb$'                  "obsidian_1.8.10_arm64.deb"
  esperar "AppImage amd64 NAO pega arm64"  '^Obsidian-[0-9][0-9.]*\.AppImage$' "Obsidian-1.8.10.AppImage"
  esperar "AppImage arm64"                 'arm64\.AppImage$'              "Obsidian-1.8.10-arm64.AppImage"
  esperar "dmg do macOS"                   '\.dmg$'                        "Obsidian-1.8.10.dmg"

  # --- Assets reais do plugin obsidian-git ---
  mkfix "main.js" "manifest.json" "styles.css"
  esperar "plugin main.js"      '^main\.js$'      "main.js"
  esperar "plugin manifest.json" '^manifest\.json$' "manifest.json"
  esperar "plugin styles.css"   '^styles\.css$'   "styles.css"

  # --- Release sem o asset procurado: precisa falhar limpo ---
  mkfix "main.js" "manifest.json"
  esperar "asset ausente falha sem estourar" '^styles\.css$' ""

  # --- Release sem assets nenhum ---
  printf '{"assets":[]}' >"$FIX"
  esperar "release vazia falha sem estourar" '^main\.js$' ""
done

printf '\n============================\n'
if [ "$FAILS" -eq 0 ]; then printf '\033[32mTODOS OS TESTES PASSARAM\033[0m\n'
else printf '\033[31m%s FALHA(S)\033[0m\n' "$FAILS"; fi
exit "$FAILS"
