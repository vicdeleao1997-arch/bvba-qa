#!/usr/bin/env bash
# Banco de testes: simula dois PCs sincronizando o mesmo vault.
set -euo pipefail

# Descobre a raiz do repositorio a partir da localizacao deste script e usa um
# diretorio temporario proprio, para o teste rodar em qualquer maquina e no CI.
AQUI="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd -- "${AQUI}/../.." && pwd)"
BASE="$(mktemp -d)"
trap 'rm -rf "${BASE}"' EXIT
SRC_SYNC="${REPO}/scripts/sync.sh"

FAILS=0
ok()   { printf '  \033[32mPASSOU\033[0m  %s\n' "$*"; }
bad()  { printf '  \033[31mFALHOU\033[0m  %s\n' "$*"; FAILS=$((FAILS+1)); }
head_() { printf '\n=== %s ===\n' "$*"; }

setup_pc() { # $1 = nome
  git clone -q "$BASE/origin.git" "$BASE/$1"
  mkdir -p "$BASE/$1/scripts"
  cp "$SRC_SYNC" "$BASE/$1/scripts/sync.sh"
  chmod +x "$BASE/$1/scripts/sync.sh"
  git -C "$BASE/$1" config user.name "$1"
  git -C "$BASE/$1" config user.email "$1@teste.local"
}

# hostname distinto por PC, para as cópias de conflito ficarem identificáveis
sync_as() { # $1 = pc, resto = args
  local pc="$1"; shift
  local bin="$BASE/fakebin-$pc"
  mkdir -p "$bin"
  cat >"$bin/uname" <<EOF
#!/bin/sh
if [ "\$1" = "-n" ]; then echo "$pc"; else /usr/bin/uname "\$@"; fi
EOF
  chmod +x "$bin/uname"
  PATH="$bin:$PATH" "$BASE/$pc/scripts/sync.sh" --quiet "$@"
}

# --------------------------------------------------------------------------
git init -q --bare -b main "$BASE/origin.git"
tmp="$BASE/seed"; mkdir -p "$tmp/scripts"
cp "$SRC_SYNC" "$tmp/scripts/sync.sh"; chmod +x "$tmp/scripts/sync.sh"
printf 'nota inicial\n' >"$tmp/Bem-vindo.md"
git -C "$tmp" init -q -b main
git -C "$tmp" config user.name seed; git -C "$tmp" config user.email seed@t.local
git -C "$tmp" add -A; git -C "$tmp" commit -qm "inicial"
git -C "$tmp" remote add origin "$BASE/origin.git"; git -C "$tmp" push -qu origin main

setup_pc pcA
setup_pc pcB

# --------------------------------------------------------------------------
head_ "1. Propagação simples: pcA cria nota -> pcB recebe"
printf '# Reuniao QA\nponto um\n' >"$BASE/pcA/Reuniao.md"
sync_as pcA
sync_as pcB
if [ -f "$BASE/pcB/Reuniao.md" ] && grep -q "ponto um" "$BASE/pcB/Reuniao.md"; then
  ok "nota criada no pcA chegou no pcB"
else
  bad "nota nao chegou no pcB"
fi

# --------------------------------------------------------------------------
head_ "2. Edicao simultanea do MESMO arquivo (o caso critico)"
printf '# Reuniao QA\nponto um\nlinha do pcA\n' >"$BASE/pcA/Reuniao.md"
printf '# Reuniao QA\nponto um\nlinha do pcB\n' >"$BASE/pcB/Reuniao.md"
sync_as pcA                      # pcA envia primeiro
sync_as pcB                      # pcB precisa integrar e preservar o seu
sync_as pcA                      # pcA recebe o resultado

conflitoB="$(find "$BASE/pcB" -name 'Reuniao (conflito*' -print -quit)"
if [ -n "$conflitoB" ]; then
  ok "copia de conflito criada no pcB: $(basename "$conflitoB")"
else
  bad "nenhuma copia de conflito criada — risco de perda de dados"
fi

if grep -q "linha do pcA" "$BASE/pcB/Reuniao.md" 2>/dev/null; then
  ok "pcB adotou a versao remota no nome original"
else
  bad "pcB nao adotou a versao remota"
fi
if [ -n "$conflitoB" ] && grep -q "linha do pcB" "$conflitoB"; then
  ok "trabalho do pcB preservado na copia de conflito"
else
  bad "trabalho do pcB foi PERDIDO"
fi

sync_as pcB; sync_as pcA
if find "$BASE/pcA" -name 'Reuniao (conflito*' | grep -q .; then
  ok "a copia de conflito propagou para o pcA (ambos veem as duas versoes)"
else
  bad "copia de conflito nao propagou para o pcA"
fi

# --------------------------------------------------------------------------
head_ "3. Convergencia: os dois PCs terminam identicos"
sync_as pcA; sync_as pcB; sync_as pcA; sync_as pcB
hA="$(git -C "$BASE/pcA" rev-parse HEAD)"
hB="$(git -C "$BASE/pcB" rev-parse HEAD)"
if [ "$hA" = "$hB" ]; then ok "mesmo commit nos dois PCs ($(echo "$hA" | cut -c1-8))"
else bad "PCs divergentes: $hA vs $hB"; fi

# Invariante decisiva: sincronizar sem mudanca nenhuma NAO pode criar commits.
# Se criar, os dois PCs ficam se empurrando commits vazios eternamente.
cBefore="$(git -C "$BASE/pcA" rev-list --count HEAD)"
for _ in 1 2 3 4 5 6; do sync_as pcA; sync_as pcB; done
cAfter="$(git -C "$BASE/pcA" rev-list --count HEAD)"
if [ "$cBefore" = "$cAfter" ]; then
  ok "6 ciclos ociosos nao criaram nenhum commit (contagem estavel em $cAfter)"
else
  bad "ciclos ociosos criaram $((cAfter - cBefore)) commit(s) — churn infinito"
fi
hA="$(git -C "$BASE/pcA" rev-parse HEAD)"; hB="$(git -C "$BASE/pcB" rev-parse HEAD)"
if [ "$hA" = "$hB" ]; then ok "PCs continuam identicos apos os ciclos ociosos"
else bad "PCs divergiram durante ciclos ociosos"; fi

dA="$(cd "$BASE/pcA" && find . -name '*.md' -not -path './.git/*' | sort | md5sum)"
dB="$(cd "$BASE/pcB" && find . -name '*.md' -not -path './.git/*' | sort | md5sum)"
if [ "$dA" = "$dB" ]; then ok "mesma lista de notas nos dois PCs"
else bad "listas de notas diferentes"; fi

# --------------------------------------------------------------------------
head_ "4. Apagado num PC, editado no outro"
printf 'documento importante\n' >"$BASE/pcA/Importante.md"
sync_as pcA; sync_as pcB
rm "$BASE/pcA/Importante.md"                      # pcA apaga
printf 'documento importante\nEDITADO no pcB\n' >"$BASE/pcB/Importante.md"  # pcB edita
sync_as pcA; sync_as pcB; sync_as pcA
if [ -f "$BASE/pcA/Importante.md" ] && grep -q "EDITADO no pcB" "$BASE/pcA/Importante.md"; then
  ok "edicao venceu a exclusao — arquivo restaurado, nada perdido"
else
  bad "arquivo com edicao pendente foi perdido"
fi

# --------------------------------------------------------------------------
head_ "5. Exclusao limpa (apagado sem edicao concorrente) propaga"
printf 'temporario\n' >"$BASE/pcA/Rascunho.md"
sync_as pcA; sync_as pcB
rm "$BASE/pcA/Rascunho.md"
sync_as pcA; sync_as pcB
if [ ! -f "$BASE/pcB/Rascunho.md" ]; then ok "exclusao propagou para o pcB"
else bad "arquivo apagado reapareceu no pcB"; fi

# --------------------------------------------------------------------------
head_ "6. Modo offline (remoto inacessivel)"
mv "$BASE/origin.git" "$BASE/origin.git.off"
printf 'escrito offline\n' >"$BASE/pcA/Offline.md"
if sync_as pcA; then ok "sincronia offline saiu sem erro"
else bad "sincronia offline retornou erro"; fi
if git -C "$BASE/pcA" log --oneline -1 --name-only | grep -q "Offline.md"; then
  ok "trabalho offline ficou commitado localmente"
else bad "trabalho offline nao foi commitado"; fi
mv "$BASE/origin.git.off" "$BASE/origin.git"
sync_as pcA; sync_as pcB
if [ -f "$BASE/pcB/Offline.md" ]; then ok "trabalho offline subiu ao reconectar"
else bad "trabalho offline nao subiu apos reconectar"; fi

# --------------------------------------------------------------------------
head_ "7. Corrida de push (o remoto muda no meio do ciclo)"
printf 'a\n' >"$BASE/pcA/Corrida.md"
printf 'b\n' >"$BASE/pcB/Outra.md"
sync_as pcA & p1=$!
sync_as pcB & p2=$!
wait $p1 $p2 || true
sync_as pcA; sync_as pcB; sync_as pcA
if [ -f "$BASE/pcA/Corrida.md" ] && [ -f "$BASE/pcA/Outra.md" ] \
   && [ -f "$BASE/pcB/Corrida.md" ] && [ -f "$BASE/pcB/Outra.md" ]; then
  ok "pushes concorrentes: os dois arquivos sobreviveram nos dois PCs"
else
  bad "push concorrente perdeu arquivo"
fi

# --------------------------------------------------------------------------
head_ "8. Trava impede ciclos simultaneos no mesmo PC"
mkdir -p "$BASE/pcA/.sync/lock"; echo 999999 >"$BASE/pcA/.sync/lock/pid"  # pid morto
printf 'x\n' >"$BASE/pcA/Trava.md"
if sync_as pcA; then ok "trava orfa recuperada automaticamente"
else bad "trava orfa travou a sincronia"; fi

# --------------------------------------------------------------------------
head_ "9. Anexo binario sincroniza intacto"
printf '\x89PNG\r\n\x1a\n\x00\x01\x02\x03binario' >"$BASE/pcA/anexo.png"
sync_as pcA; sync_as pcB
if cmp -s "$BASE/pcA/anexo.png" "$BASE/pcB/anexo.png"; then ok "binario identico byte a byte"
else bad "binario corrompido na sincronia"; fi

# --------------------------------------------------------------------------
head_ "10. Nome com acento e espaco"
printf 'conteudo\n' >"$BASE/pcA/Reunião de Diretoria — 2026.md"
sync_as pcA; sync_as pcB
if [ -f "$BASE/pcB/Reunião de Diretoria — 2026.md" ]; then ok "acentos e espacos preservados"
else bad "nome com acento quebrou"; fi

# --------------------------------------------------------------------------
head_ "11. --status nao altera nada"
before="$(git -C "$BASE/pcA" rev-parse HEAD)"
"$BASE/pcA/scripts/sync.sh" --status >/dev/null 2>&1 || true
after="$(git -C "$BASE/pcA" rev-parse HEAD)"
if [ "$before" = "$after" ]; then ok "--status e somente leitura"
else bad "--status alterou o repositorio"; fi

printf '\n============================\n'
if [ "$FAILS" -eq 0 ]; then printf '\033[32mTODOS OS TESTES PASSARAM\033[0m\n'
else printf '\033[31m%s TESTE(S) FALHARAM\033[0m\n' "$FAILS"; fi
printf '============================\n'
exit "$FAILS"
