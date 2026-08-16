#!/usr/bin/env bash
# Integracao com o CONTEUDO REAL do repositorio: prova que o .gitignore e o
# sync.sh se comportam bem juntos num vault de verdade.
set -uo pipefail

# Descobre a raiz do repositorio a partir da localizacao deste script e usa um
# diretorio temporario proprio, para o teste rodar em qualquer maquina e no CI.
AQUI="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd -- "${AQUI}/../.." && pwd)"
BASE="$(mktemp -d)"
trap 'rm -rf "${BASE}"' EXIT
FAILS=0
ok()  { printf '  \033[32mPASSOU\033[0m  %s\n' "$*"; }
bad() { printf '  \033[31mFALHOU\033[0m  %s\n' "$*"; FAILS=$((FAILS+1)); }
sec() { printf '\n=== %s ===\n' "$*"; }

sync_as() { local pc="$1"; shift
  local bin="$BASE/fb-$pc"; mkdir -p "$bin"
  # shellcheck disable=SC2016  # aspas simples de proposito: $1/$@ sao do script gerado
  printf '#!/bin/sh\nif [ "$1" = "-n" ]; then echo "%s"; else /usr/bin/uname "$@"; fi\n' "$pc" >"$bin/uname"
  chmod +x "$bin/uname"
  PATH="$bin:$PATH" "$BASE/$pc/scripts/sync.sh" --quiet "$@"; }

git init -q --bare -b main "$BASE/origin.git"
# git archive em vez de git clone: funciona mesmo com HEAD destacado, que e
# exatamente o estado deixado pelo actions/checkout no CI.
mkdir -p "$BASE/seed"
git -C "$REPO" archive HEAD | tar -x -C "$BASE/seed"
git -C "$BASE/seed" init -q -b main
git -C "$BASE/seed" config user.name seed; git -C "$BASE/seed" config user.email seed@t.local
git -C "$BASE/seed" add -A; git -C "$BASE/seed" commit -qm "vault"
git -C "$BASE/seed" remote add origin "$BASE/origin.git"
git -C "$BASE/seed" push -q origin main
git clone -q -b main "$BASE/origin.git" "$BASE/pcA"
git clone -q -b main "$BASE/origin.git" "$BASE/pcB"
for pc in pcA pcB; do
  git -C "$BASE/$pc" config user.name "$pc"; git -C "$BASE/$pc" config user.email "$pc@t.local"
done

sec "Configuracoes do Obsidian sincronizam"
for f in .obsidian/app.json .obsidian/core-plugins.json .obsidian/hotkeys.json \
         .obsidian/plugins/obsidian-git/data.json "80 - Modelos/Nota diária.md"; do
  if [ -f "$BASE/pcB/$f" ]; then ok "chegou no pcB: $f"; else bad "faltou no pcB: $f"; fi
done

sec "Estado local de maquina NAO e versionado"
mkdir -p "$BASE/pcA/.obsidian/plugins/obsidian-git"
echo '{"main":{"x":1}}'   >"$BASE/pcA/.obsidian/workspace.json"
echo 'console.log(1)'     >"$BASE/pcA/.obsidian/plugins/obsidian-git/main.js"
echo '{"id":"obsidian-git"}' >"$BASE/pcA/.obsidian/plugins/obsidian-git/manifest.json"
mkdir -p "$BASE/pcA/.trash"; echo 'apagado' >"$BASE/pcA/.trash/velho.md"
printf '# nota real\n' >"$BASE/pcA/00 - Inbox/Nota real.md"
sync_as pcA; sync_as pcB

for f in .obsidian/workspace.json .obsidian/plugins/obsidian-git/main.js \
         .obsidian/plugins/obsidian-git/manifest.json .trash/velho.md; do
  if git -C "$BASE/pcA" ls-files --error-unmatch "$f" >/dev/null 2>&1; then
    bad "$f foi versionado (nao deveria)"
  else ok "$f ignorado corretamente"; fi
done
if [ -f "$BASE/pcB/00 - Inbox/Nota real.md" ]; then ok "a nota de verdade sincronizou"
else bad "a nota de verdade nao sincronizou"; fi

sec "O log da propria sincronia nunca entra no git"
if git -C "$BASE/pcA" ls-files | grep -q '^\.sync/'; then bad ".sync/ foi versionado — causaria commits infinitos"
else ok ".sync/ fora do controle de versao"; fi
if [ -f "$BASE/pcA/.sync/sync.log" ]; then ok "o log existe em disco (so nao e versionado)"
else bad "o log nao foi criado"; fi

sec "Ciclos ociosos com o vault real nao geram commits"
antes="$(git -C "$BASE/pcA" rev-list --count HEAD)"
for _ in 1 2 3 4; do sync_as pcA; sync_as pcB; done
depois="$(git -C "$BASE/pcA" rev-list --count HEAD)"
if [ "$antes" = "$depois" ]; then ok "8 ciclos ociosos, 0 commits novos (estavel em $depois)"
else bad "ciclos ociosos criaram $((depois-antes)) commit(s)"; fi

sec "Anexo real (imagem em 90 - Anexos)"
printf '\x89PNG\r\n\x1a\n\x00\x10\x20fake-image-bytes' >"$BASE/pcA/90 - Anexos/captura.png"
sync_as pcA; sync_as pcB
if cmp -s "$BASE/pcA/90 - Anexos/captura.png" "$BASE/pcB/90 - Anexos/captura.png"; then
  ok "anexo binario chegou intacto"
else bad "anexo binario corrompido"; fi

sec "Mudanca de configuracao do Obsidian propaga (tema)"
jq '.accentColor = "#ff0000"' "$BASE/pcA/.obsidian/appearance.json" >"$BASE/tmp.json" \
  && mv "$BASE/tmp.json" "$BASE/pcA/.obsidian/appearance.json"
sync_as pcA; sync_as pcB
if grep -q 'ff0000' "$BASE/pcB/.obsidian/appearance.json"; then
  ok "ajuste de aparencia propagou entre PCs (sincronia de configuracao)"
else bad "configuracao nao propagou"; fi

sec "Conflito numa nota real do vault"
printf '# Reuniao\nversao do pcA\n' >"$BASE/pcA/00 - Inbox/Ata.md"
sync_as pcA; sync_as pcB
printf '# Reuniao\nversao do pcA\nadicao do pcA\n' >"$BASE/pcA/00 - Inbox/Ata.md"
printf '# Reuniao\nversao do pcA\nadicao do pcB\n' >"$BASE/pcB/00 - Inbox/Ata.md"
sync_as pcA; sync_as pcB; sync_as pcA
copia="$(find "$BASE/pcA/00 - Inbox" -name 'Ata (conflito*' -print -quit)"
if [ -n "$copia" ] && grep -q 'adicao do pcB' "$copia" \
   && grep -q 'adicao do pcA' "$BASE/pcA/00 - Inbox/Ata.md"; then
  ok "as duas versoes sobreviveram: $(basename "$copia")"
else bad "perda de conteudo no conflito"; fi

sec "Convergencia final"
sync_as pcA; sync_as pcB; sync_as pcA; sync_as pcB
hA="$(git -C "$BASE/pcA" rev-parse HEAD)"; hB="$(git -C "$BASE/pcB" rev-parse HEAD)"
if [ "$hA" = "$hB" ]; then ok "pcA e pcB no mesmo commit ($(echo "$hA"|cut -c1-8))"
else bad "PCs divergentes"; fi
# O que importa e o conteudo VERSIONADO ser identico. Os arquivos locais de
# maquina (workspace.json, binarios de plugin, lixeira) devem MESMO diferir —
# e para isso que eles estao no .gitignore.
if diff -q <(git -C "$BASE/pcA" ls-files | sort) <(git -C "$BASE/pcB" ls-files | sort) >/dev/null; then
  ok "lista de arquivos versionados identica nos dois PCs"
else bad "os PCs versionam arquivos diferentes"; fi

tA="$(git -C "$BASE/pcA" rev-parse "HEAD^{tree}")"; tB="$(git -C "$BASE/pcB" rev-parse "HEAD^{tree}")"
if [ "$tA" = "$tB" ]; then ok "arvore git identica byte a byte ($(echo "$tA"|cut -c1-8))"
else bad "arvores git diferentes"; fi

# E o inverso: os locais de maquina NAO podem ter vazado para o outro PC.
vazou=0
for f in .obsidian/workspace.json .obsidian/plugins/obsidian-git/main.js .trash/velho.md; do
  [ -e "$BASE/pcB/$f" ] && { bad "estado local de maquina vazou para o pcB: $f"; vazou=1; }
done
[ "$vazou" -eq 0 ] && ok "nenhum estado local de maquina vazou entre os PCs"

printf '\n============================\n'
if [ "$FAILS" -eq 0 ]; then printf '\033[32mTODOS OS TESTES DE INTEGRACAO PASSARAM\033[0m\n'
else printf '\033[31m%s FALHA(S)\033[0m\n' "$FAILS"; fi
exit "$FAILS"
