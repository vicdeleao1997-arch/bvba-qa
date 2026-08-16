#!/usr/bin/env bash
#
# instalar.sh — instala o Obsidian e coloca o vault bvba-qa em sincronia total.
#
# Faz, de ponta a ponta:
#   1. instala o git (se faltar) e o Obsidian
#   2. baixa o vault do GitHub (ou usa o que já está aqui)
#   3. instala e configura o plugin obsidian-git (sincronia com o app aberto)
#   4. registra o vault no Obsidian, para ele abrir sozinho
#   5. agenda a sincronia de fundo (sincronia com o app fechado)
#
# Uso:
#   ./scripts/instalar.sh
#   ./scripts/instalar.sh --vault ~/Documentos/bvba-qa --intervalo 5
#   ./scripts/instalar.sh --sem-obsidian     # só a sincronia, sem instalar o app
#   ./scripts/instalar.sh --sem-agendador    # sem a sincronia de fundo
#   ./scripts/instalar.sh --remover          # remove só o agendador de fundo

set -euo pipefail

REPO_URL="https://github.com/vicdeleao1997-arch/bvba-qa.git"
VAULT_NAME="bvba-qa"
SERVICE_ID="obsidian-sync-bvba-qa"

VAULT_DIR=""
INTERVALO=5          # minutos entre sincronias de fundo
INSTALAR_OBSIDIAN=1
INSTALAR_AGENDADOR=1
REMOVER=0

# --------------------------------------------------------------------------
# Saída
# --------------------------------------------------------------------------

if [ -t 1 ]; then
  C_OK=$'\033[32m'; C_ERR=$'\033[31m'; C_AV=$'\033[33m'; C_T=$'\033[1m'; C_0=$'\033[0m'
else
  C_OK=""; C_ERR=""; C_AV=""; C_T=""; C_0=""
fi

titulo() { printf '\n%s==> %s%s\n' "${C_T}" "$*" "${C_0}"; }
ok()     { printf '  %s✓%s %s\n' "${C_OK}" "${C_0}" "$*"; }
aviso()  { printf '  %s!%s %s\n' "${C_AV}" "${C_0}" "$*"; }
erro()   { printf '  %s✗%s %s\n' "${C_ERR}" "${C_0}" "$*" >&2; }
morre()  { erro "$*"; exit 1; }

# --------------------------------------------------------------------------
# Detecção de plataforma
# --------------------------------------------------------------------------

case "$(uname -s)" in
  Darwin) SO="macos" ;;
  Linux)  SO="linux" ;;
  *)      morre "sistema não suportado: $(uname -s). No Windows use scripts\\instalar.ps1" ;;
esac

case "$(uname -m)" in
  # O AppImage de 64 bits não traz sufixo de arquitetura no nome, então o padrão
  # precisa excluir explicitamente o "-arm64" — senão baixaríamos o binário errado.
  x86_64|amd64)  ARCH="amd64"; PADRAO_APPIMAGE='^Obsidian-[0-9][0-9.]*\.AppImage$' ;;
  aarch64|arm64) ARCH="arm64"; PADRAO_APPIMAGE='arm64\.AppImage$' ;;
  *) morre "arquitetura não suportada: $(uname -m)" ;;
esac

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  command -v sudo >/dev/null 2>&1 && SUDO="sudo"
fi

# --------------------------------------------------------------------------
# Utilitários
# --------------------------------------------------------------------------

tem() { command -v "$1" >/dev/null 2>&1; }

# Extrai a URL de download de um asset da última release do GitHub.
#   $1 = repositório (ex.: obsidianmd/obsidian-releases)
#   $2 = regex casada contra o NOME do arquivo (não contra a URL inteira)
#
# O padrão é sempre aplicado ao nome do arquivo, com ou sem jq, para os dois
# caminhos se comportarem igual — âncoras como ^ e $ valem em ambos.
url_release() {
  local repo="$1" padrao="$2" json urls u
  json="$(curl -fsSL --retry 3 --retry-delay 2 \
            "https://api.github.com/repos/${repo}/releases/latest" 2>/dev/null)" || return 1
  [ -n "${json}" ] || return 1

  if tem jq; then
    urls="$(printf '%s' "${json}" | jq -r '.assets[]?.browser_download_url // empty' 2>/dev/null)"
  else
    urls="$(printf '%s' "${json}" \
      | grep -o '"browser_download_url": *"[^"]*"' \
      | sed 's/.*"\(https[^"]*\)"/\1/')"
  fi
  [ -n "${urls}" ] || return 1

  while IFS= read -r u; do
    [ -n "${u}" ] || continue
    if printf '%s' "${u##*/}" | grep -qE "${padrao}"; then
      printf '%s' "${u}"
      return 0
    fi
  done <<<"${urls}"
  return 1
}

baixar() { # $1 = url, $2 = destino
  curl -fsSL --retry 3 --retry-delay 2 -o "$2" "$1"
}

# --------------------------------------------------------------------------
# Argumentos
# --------------------------------------------------------------------------

while [ $# -gt 0 ]; do
  case "$1" in
    --vault)          VAULT_DIR="${2:?--vault precisa de um caminho}"; shift ;;
    --intervalo)      INTERVALO="${2:?--intervalo precisa de um número}"; shift ;;
    --sem-obsidian)   INSTALAR_OBSIDIAN=0 ;;
    --sem-agendador)  INSTALAR_AGENDADOR=0 ;;
    --remover)        REMOVER=1 ;;
    -h|--help)        sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) morre "opção desconhecida: $1 (use --help)" ;;
  esac
  shift
done

if ! [[ "${INTERVALO}" =~ ^[0-9]+$ ]] || [ "${INTERVALO}" -lt 1 ]; then
  morre "--intervalo deve ser um número de minutos >= 1"
fi

# --------------------------------------------------------------------------
# Caminhos por plataforma
# --------------------------------------------------------------------------

if [ "${SO}" = "macos" ]; then
  OBSIDIAN_CONFIG_DIR="${HOME}/Library/Application Support/obsidian"
  VAULT_PADRAO="${HOME}/Documents/${VAULT_NAME}"
else
  OBSIDIAN_CONFIG_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}/obsidian"
  VAULT_PADRAO="${HOME}/Documentos/${VAULT_NAME}"
  [ -d "${HOME}/Documentos" ] || VAULT_PADRAO="${HOME}/Documents/${VAULT_NAME}"
  [ -d "$(dirname "${VAULT_PADRAO}")" ] || VAULT_PADRAO="${HOME}/${VAULT_NAME}"
fi

# --------------------------------------------------------------------------
# Remoção do agendador
# --------------------------------------------------------------------------

remover_agendador() {
  titulo "Removendo a sincronia de fundo"
  if [ "${SO}" = "macos" ]; then
    local plist="${HOME}/Library/LaunchAgents/com.${SERVICE_ID}.plist"
    if [ -f "${plist}" ]; then
      launchctl unload "${plist}" 2>/dev/null || true
      rm -f "${plist}"; ok "agente launchd removido"
    else
      aviso "nenhum agente launchd instalado"
    fi
  else
    if tem systemctl && systemctl --user list-unit-files 2>/dev/null | grep -q "${SERVICE_ID}"; then
      systemctl --user disable --now "${SERVICE_ID}.timer" 2>/dev/null || true
      rm -f "${HOME}/.config/systemd/user/${SERVICE_ID}."{service,timer}
      systemctl --user daemon-reload 2>/dev/null || true
      ok "timer systemd removido"
    elif crontab -l 2>/dev/null | grep -q "${SERVICE_ID}"; then
      crontab -l 2>/dev/null | grep -v "${SERVICE_ID}" | crontab -
      ok "entrada de cron removida"
    else
      aviso "nenhum agendador instalado"
    fi
  fi
  printf '\nO vault e o Obsidian continuam instalados. Só a sincronia automática\n'
  printf 'de fundo foi desligada — dentro do Obsidian o plugin continua ativo.\n'
}

if [ "${REMOVER}" -eq 1 ]; then
  remover_agendador
  exit 0
fi

# --------------------------------------------------------------------------
# 1. git
# --------------------------------------------------------------------------

titulo "Verificando o git"
if tem git; then
  ok "git presente ($(git --version | awk '{print $3}'))"
else
  aviso "git não encontrado; instalando"
  if [ "${SO}" = "macos" ]; then
    xcode-select --install 2>/dev/null || true
    morre "conclua a instalação das Ferramentas de Linha de Comando e rode de novo"
  elif tem apt-get; then
    ${SUDO} apt-get update -qq && ${SUDO} apt-get install -y git
  elif tem dnf; then ${SUDO} dnf install -y git
  elif tem pacman; then ${SUDO} pacman -Sy --noconfirm git
  elif tem zypper; then ${SUDO} zypper install -y git
  else morre "não sei instalar o git nesta distribuição; instale manualmente"
  fi
  tem git || morre "a instalação do git falhou"
  ok "git instalado"
fi

# --------------------------------------------------------------------------
# 2. Obsidian
# --------------------------------------------------------------------------

obsidian_instalado() {
  [ "${SO}" = "macos" ] && [ -d "/Applications/Obsidian.app" ] && return 0
  tem obsidian && return 0
  [ -x "${HOME}/.local/bin/obsidian" ] && return 0
  tem flatpak && flatpak info md.obsidian.Obsidian >/dev/null 2>&1 && return 0
  return 1
}

instalar_obsidian_macos() {
  if tem brew; then
    brew install --cask obsidian && return 0
    aviso "brew falhou; tentando o download direto"
  fi
  local url dmg mnt
  url="$(url_release obsidianmd/obsidian-releases '\.dmg$')" \
    || morre "não consegui descobrir a versão mais recente do Obsidian"
  dmg="$(mktemp -d)/Obsidian.dmg"
  baixar "${url}" "${dmg}" || morre "falha ao baixar o Obsidian"
  mnt="$(mktemp -d)"
  hdiutil attach -nobrowse -quiet -mountpoint "${mnt}" "${dmg}" \
    || morre "falha ao montar o instalador"
  cp -R "${mnt}/Obsidian.app" /Applications/ || { hdiutil detach -quiet "${mnt}"; morre "falha ao copiar para /Applications"; }
  hdiutil detach -quiet "${mnt}"
  rm -f "${dmg}"
}

instalar_obsidian_linux() {
  # Preferência 1: pacote .deb em distros Debian/Ubuntu
  if tem apt-get && tem dpkg; then
    local url deb
    if url="$(url_release obsidianmd/obsidian-releases "_${ARCH}\.deb$")" && [ -n "${url}" ]; then
      deb="$(mktemp -d)/obsidian.deb"
      if baixar "${url}" "${deb}"; then
        ${SUDO} apt-get install -y "${deb}" && { rm -f "${deb}"; return 0; }
        aviso "instalação do .deb falhou; tentando AppImage"
      fi
    fi
  fi

  # Preferência 2: Flatpak
  if tem flatpak; then
    flatpak install -y --noninteractive flathub md.obsidian.Obsidian && return 0
    aviso "flatpak falhou; tentando AppImage"
  fi

  # Preferência 3: AppImage no diretório do usuário
  local url dest
  url="$(url_release obsidianmd/obsidian-releases "${PADRAO_APPIMAGE}")" \
    || morre "não consegui descobrir a versão mais recente do Obsidian"
  [ -n "${url}" ] || morre "nenhum AppImage disponível para ${ARCH}"
  mkdir -p "${HOME}/.local/bin" "${HOME}/.local/share/applications"
  dest="${HOME}/.local/bin/obsidian"
  baixar "${url}" "${dest}" || morre "falha ao baixar o AppImage"
  chmod +x "${dest}"
  cat >"${HOME}/.local/share/applications/obsidian.desktop" <<EOF
[Desktop Entry]
Name=Obsidian
Exec=${dest} %u
Icon=obsidian
Type=Application
Categories=Office;
MimeType=x-scheme-handler/obsidian;
EOF
  aviso "instalado como AppImage em ${dest}"
  case ":${PATH}:" in
    *":${HOME}/.local/bin:"*) : ;;
    *) aviso "adicione ~/.local/bin ao seu PATH para chamar 'obsidian' no terminal" ;;
  esac
}

if [ "${INSTALAR_OBSIDIAN}" -eq 1 ]; then
  titulo "Instalando o Obsidian"
  if obsidian_instalado; then
    ok "Obsidian já está instalado"
  else
    if [ "${SO}" = "macos" ]; then instalar_obsidian_macos; else instalar_obsidian_linux; fi
    if obsidian_instalado; then
      ok "Obsidian instalado"
    else
      aviso "não consegui confirmar a instalação do Obsidian"
    fi
  fi
else
  titulo "Instalação do Obsidian pulada (--sem-obsidian)"
fi

# --------------------------------------------------------------------------
# 3. Vault
# --------------------------------------------------------------------------

titulo "Preparando o vault"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
POSSIVEL_VAULT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

if [ -z "${VAULT_DIR}" ]; then
  if git -C "${POSSIVEL_VAULT}" rev-parse --git-dir >/dev/null 2>&1; then
    VAULT_DIR="${POSSIVEL_VAULT}"      # rodando de dentro do repositório já clonado
  else
    VAULT_DIR="${VAULT_PADRAO}"
  fi
fi

if git -C "${VAULT_DIR}" rev-parse --git-dir >/dev/null 2>&1; then
  ok "usando o vault existente em ${VAULT_DIR}"
else
  [ -e "${VAULT_DIR}" ] && [ -n "$(ls -A "${VAULT_DIR}" 2>/dev/null)" ] \
    && morre "${VAULT_DIR} já existe e não está vazio; use --vault com outro caminho"
  mkdir -p "$(dirname "${VAULT_DIR}")"
  git clone "${REPO_URL}" "${VAULT_DIR}" || morre "falha ao clonar o vault de ${REPO_URL}"
  ok "vault clonado em ${VAULT_DIR}"
fi

VAULT_DIR="$(cd -- "${VAULT_DIR}" && pwd)"

titulo "Ajustando o git do vault"
git -C "${VAULT_DIR}" config core.quotepath false        # nomes acentuados legíveis
git -C "${VAULT_DIR}" config core.precomposeunicode true # acentos iguais entre macOS e Linux/Windows
git -C "${VAULT_DIR}" config pull.rebase false           # o sync.sh cuida do merge
git -C "${VAULT_DIR}" config merge.ff false
git -C "${VAULT_DIR}" config push.default current
if [ "${SO}" != "macos" ]; then
  git -C "${VAULT_DIR}" config core.autocrlf input
fi
ok "git do vault configurado para sincronia entre sistemas diferentes"

if ! git -C "${VAULT_DIR}" config user.name >/dev/null 2>&1; then
  git -C "${VAULT_DIR}" config user.name "${USER:-obsidian}@$(uname -n | cut -d. -f1)"
  git -C "${VAULT_DIR}" config user.email "${USER:-obsidian}@$(uname -n | cut -d. -f1).local"
  aviso "identidade do git definida automaticamente; ajuste com 'git -C \"${VAULT_DIR}\" config user.name \"Seu Nome\"'"
fi

chmod +x "${VAULT_DIR}/scripts/sync.sh" 2>/dev/null || true

# --------------------------------------------------------------------------
# 4. Plugin obsidian-git
# --------------------------------------------------------------------------

titulo "Instalando o plugin de sincronia (obsidian-git)"
PLUGIN_DIR="${VAULT_DIR}/.obsidian/plugins/obsidian-git"
mkdir -p "${PLUGIN_DIR}"

plugin_falhou=0
for arquivo in main.js manifest.json styles.css; do
  url="$(url_release Vinzent03/obsidian-git "^${arquivo//./\\.}$")" || url=""
  if [ -n "${url}" ] && baixar "${url}" "${PLUGIN_DIR}/${arquivo}"; then
    ok "${arquivo}"
  else
    [ "${arquivo}" = "styles.css" ] && continue   # nem toda release publica styles.css
    plugin_falhou=1
    erro "não consegui baixar ${arquivo}"
  fi
done

if [ "${plugin_falhou}" -eq 1 ]; then
  aviso "o plugin não foi instalado automaticamente."
  aviso "instale pelo app: Configurações > Plugins da comunidade > Procurar > 'Git'."
  aviso "as configurações dele já estão no vault e serão aplicadas sozinhas."
else
  ok "plugin instalado e já configurado (sincroniza a cada ${INTERVALO} min com o app aberto)"
fi

# --------------------------------------------------------------------------
# 5. Registro do vault no Obsidian
# --------------------------------------------------------------------------

titulo "Registrando o vault no Obsidian"
mkdir -p "${OBSIDIAN_CONFIG_DIR}"
OBSIDIAN_JSON="${OBSIDIAN_CONFIG_DIR}/obsidian.json"

# id de 16 hex derivado do caminho — estável entre execuções
VAULT_ID="$(printf '%s' "${VAULT_DIR}" | (md5sum 2>/dev/null || md5) | tr -d ' -' | cut -c1-16)"
AGORA="$(date +%s)000"

if [ ! -f "${OBSIDIAN_JSON}" ]; then
  cat >"${OBSIDIAN_JSON}" <<EOF
{
  "vaults": {
    "${VAULT_ID}": {
      "path": "${VAULT_DIR}",
      "ts": ${AGORA},
      "open": true
    }
  }
}
EOF
  ok "vault registrado — o Obsidian vai abrir nele direto"
elif tem jq; then
  tmp="$(mktemp)"
  if jq --arg id "${VAULT_ID}" --arg p "${VAULT_DIR}" --argjson ts "${AGORA}" \
        '.vaults = ((.vaults // {}) + {($id): {path: $p, ts: $ts, open: true}})' \
        "${OBSIDIAN_JSON}" >"${tmp}" && [ -s "${tmp}" ]; then
    mv "${tmp}" "${OBSIDIAN_JSON}"
    ok "vault registrado na lista existente do Obsidian"
  else
    rm -f "${tmp}"
    aviso "não consegui editar ${OBSIDIAN_JSON}; abra o vault manualmente pelo app"
  fi
else
  aviso "jq não instalado e já existe configuração do Obsidian."
  aviso "abra o app e use 'Abrir pasta como vault' apontando para ${VAULT_DIR}"
fi

# --------------------------------------------------------------------------
# 6. Sincronia de fundo (com o Obsidian fechado)
# --------------------------------------------------------------------------

instalar_systemd() {
  local dir="${HOME}/.config/systemd/user"
  mkdir -p "${dir}"
  cat >"${dir}/${SERVICE_ID}.service" <<EOF
[Unit]
Description=Sincronia do vault Obsidian ${VAULT_NAME}
After=network-online.target

[Service]
Type=oneshot
ExecStart=${VAULT_DIR}/scripts/sync.sh --quiet
WorkingDirectory=${VAULT_DIR}
EOF
  cat >"${dir}/${SERVICE_ID}.timer" <<EOF
[Unit]
Description=Sincroniza o vault ${VAULT_NAME} a cada ${INTERVALO} min

[Timer]
OnBootSec=2min
OnUnitActiveSec=${INTERVALO}min
Persistent=true

[Install]
WantedBy=timers.target
EOF
  systemctl --user daemon-reload
  systemctl --user enable --now "${SERVICE_ID}.timer"
  ok "timer systemd ativo (a cada ${INTERVALO} min, mesmo com o Obsidian fechado)"
  aviso "para sincronizar também com a sessão deslogada: sudo loginctl enable-linger ${USER}"
}

instalar_launchd() {
  local plist="${HOME}/Library/LaunchAgents/com.${SERVICE_ID}.plist"
  mkdir -p "$(dirname "${plist}")"
  cat >"${plist}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.${SERVICE_ID}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${VAULT_DIR}/scripts/sync.sh</string>
    <string>--quiet</string>
  </array>
  <key>WorkingDirectory</key><string>${VAULT_DIR}</string>
  <key>StartInterval</key><integer>$((INTERVALO * 60))</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardErrorPath</key><string>${VAULT_DIR}/.sync/launchd.err.log</string>
</dict>
</plist>
EOF
  mkdir -p "${VAULT_DIR}/.sync"
  launchctl unload "${plist}" 2>/dev/null || true
  if launchctl load "${plist}" 2>/dev/null; then
    ok "agente launchd ativo (a cada ${INTERVALO} min, mesmo com o Obsidian fechado)"
  else
    aviso "não consegui carregar o agente launchd; rode: launchctl load ${plist}"
  fi
}

instalar_cron() {
  local linha="*/${INTERVALO} * * * * ${VAULT_DIR}/scripts/sync.sh --quiet # ${SERVICE_ID}"
  if { crontab -l 2>/dev/null | grep -v "${SERVICE_ID}"; printf '%s\n' "${linha}"; } | crontab -; then
    ok "entrada de cron criada (a cada ${INTERVALO} min)"
  else
    aviso "não consegui criar a entrada de cron"
  fi
}

if [ "${INSTALAR_AGENDADOR}" -eq 1 ]; then
  titulo "Agendando a sincronia de fundo"
  if [ "${SO}" = "macos" ]; then
    instalar_launchd
  elif tem systemctl && systemctl --user show-environment >/dev/null 2>&1; then
    instalar_systemd
  elif tem crontab; then
    aviso "systemd de usuário indisponível; usando cron"
    instalar_cron
  else
    aviso "nenhum agendador disponível; a sincronia vai acontecer só com o Obsidian aberto"
  fi
else
  titulo "Agendador pulado (--sem-agendador)"
fi

# --------------------------------------------------------------------------
# 7. Verificação
# --------------------------------------------------------------------------

titulo "Testando a sincronia"
if "${VAULT_DIR}/scripts/sync.sh" --quiet; then
  ok "ciclo de sincronia concluído com sucesso"
else
  aviso "o ciclo de teste não completou — provavelmente falta autenticação no GitHub"
  aviso "veja o log em ${VAULT_DIR}/.sync/sync.log"
fi

# --------------------------------------------------------------------------
# Resumo
# --------------------------------------------------------------------------

cat <<EOF

${C_T}Pronto.${C_0}

  Vault:      ${VAULT_DIR}
  Intervalo:  a cada ${INTERVALO} min (app aberto E app fechado)
  Conflitos:  nada é sobrescrito — a sua versão vira uma cópia ao lado

${C_T}Comandos úteis${C_0}
  ${VAULT_DIR}/scripts/sync.sh            sincronizar agora
  ${VAULT_DIR}/scripts/sync.sh --status   ver o estado da sincronia
  ${VAULT_DIR}/scripts/instalar.sh --remover   desligar a sincronia de fundo

${C_T}Um detalhe que depende de você${C_0}
  O git precisa conseguir autenticar no GitHub sem pedir senha, senão a
  sincronia de fundo trava esperando digitação. Escolha um caminho:

    • Chave SSH (recomendado):
        ssh-keygen -t ed25519 -C "${VAULT_NAME}"
        cat ~/.ssh/id_ed25519.pub     # adicione em github.com/settings/keys
        git -C "${VAULT_DIR}" remote set-url origin git@github.com:vicdeleao1997-arch/${VAULT_NAME}.git

    • Ou um gerenciador de credenciais:
        git config --global credential.helper store   # (osxkeychain no macOS)

  Confira com:  ${VAULT_DIR}/scripts/sync.sh --status

EOF
