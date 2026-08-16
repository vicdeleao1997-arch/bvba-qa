#!/usr/bin/env bash
# Banco de testes do portao de testes: prova que codigo quebrado nao viaja
# entre os PCs, e que nota e plano continuam passando direto.
#
# O que esta sendo protegido: este repositorio nao e so um vault de notas.
# `agente_drop/` sobe o drop da marca para a Nuvemshop. Uma sincronia que
# commita sozinha e empurra sem olhar levaria um defeito para a outra maquina
# e para o main.
set -euo pipefail

AQUI="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd -- "${AQUI}/../.." && pwd)"
BASE="$(mktemp -d)"
trap 'rm -rf "${BASE}"' EXIT
SRC_SYNC="${REPO}/scripts/sync.sh"

FAILS=0
ok()    { printf '  \033[32mPASSOU\033[0m  %s\n' "$*"; }
bad()   { printf '  \033[31mFALHOU\033[0m  %s\n' "$*"; FAILS=$((FAILS+1)); }
head_() { printf '\n=== %s ===\n' "$*"; }

# afirmar <condicao-ja-avaliada> <mensagem>  — 0 passou, qualquer outro falhou
afirmar() {
  local resultado="$1"; shift
  if [ "${resultado}" -eq 0 ]; then ok "$*"; else bad "$*"; fi
}
igual() { # igual <a> <b> <mensagem>
  local a="$1" b="$2"; shift 2
  if [ "${a}" = "${b}" ]; then ok "$*"; else bad "$* (obtido '${a}', esperado '${b}')"; fi
}

PY="$(command -v python3 || command -v python || true)"
if [ -z "${PY}" ]; then
  printf '  (python nao encontrado — testes do portao pulados)\n'
  exit 0
fi

# --------------------------------------------------------------------------
# Um repositorio minimo com codigo de verdade e um remoto de verdade.
#
# De proposito SEM .gitignore para __pycache__: assim o teste tambem prova que
# o portao nao suja a arvore que esta prestes a sincronizar. Se ele voltar a
# deixar bytecode para tras, o cenario 4 acusa.
# --------------------------------------------------------------------------
git init -q --bare "${BASE}/origin.git"
git -C "${BASE}/origin.git" symbolic-ref HEAD refs/heads/main

git clone -q "${BASE}/origin.git" "${BASE}/semente" 2>/dev/null
(
  cd "${BASE}/semente"
  git config user.email t@t; git config user.name semente
  mkdir -p scripts testes agente_drop
  cp "${SRC_SYNC}" scripts/; chmod +x scripts/sync.sh
  printf 'def somar(a, b):\n    return a + b\n' > agente_drop/calculo.py
  printf 'import unittest\nfrom agente_drop.calculo import somar\n\n\nclass T(unittest.TestCase):\n    def test_soma(self):\n        self.assertEqual(somar(2, 2), 4)\n' > testes/test_calculo.py
  : > agente_drop/__init__.py
  : > testes/__init__.py
  printf 'nota inicial\n' > PLANO.md
  git add -A; git commit -q -m inicial; git branch -M main; git push -q -u origin main
)
rm -rf "${BASE}/semente"

git clone -q "${BASE}/origin.git" "${BASE}/pc"
git -C "${BASE}/pc" config user.email t@t
git -C "${BASE}/pc" config user.name pc

sincronizar() { ( cd "${BASE}/pc" && ./scripts/sync.sh --quiet ) >"${BASE}/.saida" 2>&1; }
remoto_head() { git -C "${BASE}/origin.git" rev-parse main; }
local_head()  { git -C "${BASE}/pc" rev-parse HEAD; }
log_sync()    { cat "${BASE}/pc/.sync/sync.log" 2>/dev/null || true; }

# --------------------------------------------------------------------------
head_ "1. Mudanca so de NOTA nao dispara os testes e sobe normalmente"
# --------------------------------------------------------------------------
printf 'linha nova na nota\n' >> "${BASE}/pc/PLANO.md"
rc=0; sincronizar || rc=$?
igual "${rc}" 0 "sincronia terminou sem erro"
if log_sync | grep -qi 'rodando os testes'; then
  bad "rodou os testes para uma mudanca que so mexeu em nota"
else
  ok "nao rodou os testes (mudanca nao toca codigo)"
fi
igual "$(local_head)" "$(remoto_head)" "a nota chegou ao remoto"

# --------------------------------------------------------------------------
head_ "2. Mudanca de CODIGO com teste passando: roda os testes e envia"
# --------------------------------------------------------------------------
printf '\n\ndef dobrar(x):\n    return x * 2\n' >> "${BASE}/pc/agente_drop/calculo.py"
rc=0; sincronizar || rc=$?
igual "${rc}" 0 "sincronia terminou sem erro"
log_sync | grep -qi 'rodando os testes'; afirmar $? "rodou os testes antes de enviar"
log_sync | grep -qi 'testes passaram';   afirmar $? "registrou que passaram"
igual "$(local_head)" "$(remoto_head)" "o codigo chegou ao remoto"

# --------------------------------------------------------------------------
head_ "3. Mudanca de CODIGO que QUEBRA o teste: nao sobe, mas nao se perde"
# --------------------------------------------------------------------------
antes_remoto="$(remoto_head)"
printf 'def somar(a, b):\n    return a - b   # defeito de proposito\n' > "${BASE}/pc/agente_drop/calculo.py"
rc=0; sincronizar || rc=$?

igual "${rc}" 72 "saiu com 72 (envio segurado)"
igual "$(remoto_head)" "${antes_remoto}" "o remoto NAO recebeu o codigo quebrado"

sujo="$(git -C "${BASE}/pc" status --porcelain)"
adiante="$(git -C "${BASE}/pc" log 'origin/main..HEAD' --oneline)"
if [ -z "${sujo}" ] && [ -n "${adiante}" ]; then
  ok "o trabalho ficou commitado localmente (nada se perdeu)"
else
  bad "o trabalho nao foi preservado (sujo='${sujo}')"
fi

grep -q 'defeito de proposito' "${BASE}/pc/agente_drop/calculo.py"
afirmar $? "o conteudo escrito continua no disco"

[ -f "${BASE}/pc/.sync/TESTES-FALHARAM.txt" ]
afirmar $? "criou o aviso TESTES-FALHARAM.txt"

# --------------------------------------------------------------------------
head_ "4. Repetir o ciclo com o defeito nao cria lixo nem desiste do trabalho"
# --------------------------------------------------------------------------
commits_antes="$(git -C "${BASE}/pc" rev-list --count HEAD)"
rc=0; sincronizar || rc=$?
commits_depois="$(git -C "${BASE}/pc" rev-list --count HEAD)"
igual "${rc}" 72 "continua segurando o envio"
igual "${commits_depois}" "${commits_antes}" "nao criou commit de ruido ao repetir"
igual "$(remoto_head)" "${antes_remoto}" "remoto segue intocado"

# O portao roda os testes; se ele deixar bytecode para tras, aparece aqui.
lixo="$(find "${BASE}/pc" -name '__pycache__' -not -path '*/.git/*' | head -3)"
if [ -z "${lixo}" ]; then
  ok "o portao nao sujou a arvore com __pycache__"
else
  bad "o portao deixou lixo para a sincronia commitar: ${lixo}"
fi

# --------------------------------------------------------------------------
head_ "5. Corrigido o defeito, o proximo ciclo envia sozinho"
# --------------------------------------------------------------------------
printf 'def somar(a, b):\n    return a + b\n' > "${BASE}/pc/agente_drop/calculo.py"
rc=0; sincronizar || rc=$?
igual "${rc}" 0 "sincronia voltou ao normal"
igual "$(local_head)" "$(remoto_head)" "o trabalho represado subiu junto"
if [ -f "${BASE}/pc/.sync/TESTES-FALHARAM.txt" ]; then
  bad "o aviso TESTES-FALHARAM.txt ficou para tras"
else
  ok "o aviso sumiu sozinho"
fi

# --------------------------------------------------------------------------
printf '\n============================\n'
if [ "${FAILS}" -eq 0 ]; then
  printf '\033[32mPORTAO DE TESTES: TUDO PASSOU\033[0m\n'
else
  printf '\033[31mPORTAO DE TESTES: %s FALHA(S)\033[0m\n' "${FAILS}"
fi
exit "${FAILS}"
