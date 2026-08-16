#!/usr/bin/env bash
#
# Liga a sincronia automatica no MacBook. Registra um agente do launchd que
# roda o sinc/sincronizar.sh a cada 15 minutos, em segundo plano, sem janela.
#
#   ./sinc/instalar-macos.sh              # liga
#   ./sinc/instalar-macos.sh --remover    # desliga e apaga o agente
#   ./sinc/instalar-macos.sh --intervalo 300   # a cada 5 min em vez de 15

set -uo pipefail

INTERVALO=900
REMOVER=0
while [ $# -gt 0 ]; do
  case "$1" in
    --remover)   REMOVER=1; shift ;;
    --intervalo) INTERVALO="${2:?--intervalo precisa de um numero em segundos}"; shift 2 ;;
    -h|--help)   sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Opcao desconhecida: $1" >&2; exit 64 ;;
  esac
done

RAIZ="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Rode este script de dentro do repositorio bvba-qa." >&2; exit 65
}
ROTULO="com.bvba.sincronizar"
PLIST="$HOME/Library/LaunchAgents/$ROTULO.plist"

descarregar() {
  launchctl bootout "gui/$UID/$ROTULO" 2>/dev/null || launchctl unload "$PLIST" 2>/dev/null || true
}

if [ "$REMOVER" -eq 1 ]; then
  descarregar
  rm -f "$PLIST"
  echo "Sincronia automatica desligada. O repositorio e o historico continuam intactos."
  echo "Voce ainda pode sincronizar na mao: ./sinc/sincronizar.sh"
  exit 0
fi

echo "Conferindo antes de ligar..."

# 1. git existe?
command -v git >/dev/null 2>&1 || { echo "  FALHOU: git nao esta instalado."; exit 66; }
echo "  ok  git"

# 2. o script roda?
chmod +x "$RAIZ/sinc/sincronizar.sh"
echo "  ok  sincronizar.sh executavel"

# 3. credencial funciona sem pedir senha? Este e o teste que importa: um agente
#    de fundo nao tem como digitar senha. Se falhar aqui, falharia calado depois.
if ! git -C "$RAIZ" ls-remote origin >/dev/null 2>&1; then
  echo "  FALHOU: o git nao conseguiu falar com o GitHub sem interacao."
  echo ""
  echo "  Resolva uma vez e rode este instalador de novo:"
  echo "    gh auth login                       # se usa o GitHub CLI"
  echo "    git config --global credential.helper osxkeychain"
  echo "    git -C '$RAIZ' fetch origin          # digite a senha uma vez; fica no chaveiro"
  exit 67
fi
echo "  ok  credencial do GitHub (sem pedir senha)"

# 4. uma passada de verdade, em simulacao
if ! "$RAIZ/sinc/sincronizar.sh" --simular --silencioso; then
  echo "  FALHOU: a simulacao da sincronia deu erro. Veja sinc/.log/sincronizar.log"
  exit 68
fi
echo "  ok  simulacao da sincronia"

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PLIST_FIM
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>            <string>$ROTULO</string>
  <key>ProgramArguments</key>
  <array>
    <string>$RAIZ/sinc/sincronizar.sh</string>
    <string>--silencioso</string>
  </array>
  <key>WorkingDirectory</key> <string>$RAIZ</string>
  <key>StartInterval</key>    <integer>$INTERVALO</integer>
  <key>RunAtLoad</key>        <true/>
  <key>ProcessType</key>      <string>Background</string>
  <key>StandardOutPath</key>  <string>$RAIZ/sinc/.log/launchd.out</string>
  <key>StandardErrorPath</key><string>$RAIZ/sinc/.log/launchd.err</string>
</dict>
</plist>
PLIST_FIM

descarregar
if ! launchctl bootstrap "gui/$UID" "$PLIST" 2>/dev/null; then
  launchctl load "$PLIST" 2>/dev/null || { echo "Nao consegui registrar o agente no launchd." >&2; exit 69; }
fi

echo ""
echo "Ligado. O MacBook sincroniza a cada $((INTERVALO/60)) minutos, sozinho."
echo ""
echo "  ver o que aconteceu:  tail -f sinc/.log/sincronizar.log"
echo "  sincronizar agora:    ./sinc/sincronizar.sh"
echo "  desligar:             ./sinc/instalar-macos.sh --remover"
