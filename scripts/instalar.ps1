# instalar.ps1 — instala o Obsidian e coloca o vault bvba-qa em sincronia total no Windows.
#
# Faz, de ponta a ponta:
#   1. instala o Git for Windows (se faltar) e o Obsidian
#   2. baixa o vault do GitHub (ou usa o que ja esta aqui)
#   3. instala e configura o plugin obsidian-git (sincronia com o app aberto)
#   4. registra o vault no Obsidian, para ele abrir sozinho
#   5. cria uma Tarefa Agendada para a sincronia de fundo (app fechado)
#
# NOTA DE PROJETO: a sincronia em si e feita pelo MESMO scripts/sync.sh usado no
# Linux e no macOS, executado pelo Bash que vem junto com o Git for Windows.
# Manter um unico motor de sincronia evita que a versao Windows saia do ar
# silenciosamente por divergir das outras.
#
# Uso (PowerShell, nao precisa de administrador):
#   .\scripts\instalar.ps1
#   .\scripts\instalar.ps1 -Vault "D:\bvba-qa" -Intervalo 5
#   .\scripts\instalar.ps1 -SemObsidian -SemAgendador
#   .\scripts\instalar.ps1 -Remover
#
# Se o Windows bloquear a execucao do script, rode antes:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

[CmdletBinding()]
param(
  [string] $Vault = "",
  [int]    $Intervalo = 5,
  [switch] $SemObsidian,
  [switch] $SemAgendador,
  [switch] $Remover
)

$ErrorActionPreference = 'Stop'

$RepoUrl   = 'https://github.com/vicdeleao1997-arch/bvba-qa.git'
$VaultName = 'bvba-qa'
$TaskName  = 'ObsidianSync-bvba-qa'

# ---------------------------------------------------------------------------
# Saida
# ---------------------------------------------------------------------------

function Write-Titulo { param([string]$T) Write-Host "`n==> $T" -ForegroundColor White }
function Write-Ok     { param([string]$T) Write-Host "  [ok] $T"    -ForegroundColor Green }
function Write-Aviso  { param([string]$T) Write-Host "  [!]  $T"    -ForegroundColor Yellow }
function Write-Erro   { param([string]$T) Write-Host "  [x]  $T"    -ForegroundColor Red }
function Morre        { param([string]$T) Write-Erro $T; exit 1 }

function Existe { param([string]$Cmd) return [bool](Get-Command $Cmd -ErrorAction SilentlyContinue) }

if ($Intervalo -lt 1) { Morre "-Intervalo deve ser um numero de minutos >= 1" }

# ---------------------------------------------------------------------------
# Remocao do agendador
# ---------------------------------------------------------------------------

if ($Remover) {
  Write-Titulo "Removendo a sincronia de fundo"
  $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  if ($t) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Ok "tarefa agendada removida"
  } else {
    Write-Aviso "nenhuma tarefa agendada encontrada"
  }
  Write-Host "`nO vault e o Obsidian continuam instalados. So a sincronia de fundo"
  Write-Host "foi desligada — dentro do Obsidian o plugin continua ativo."
  exit 0
}

# ---------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------

# Converte C:\Users\x\vault  ->  /c/Users/x/vault  (formato que o Git-Bash entende)
function ConvertTo-CaminhoBash {
  param([string]$Caminho)
  $p = $Caminho -replace '\\', '/'
  if ($p -match '^([A-Za-z]):(.*)$') {
    return ('/' + $Matches[1].ToLower() + $Matches[2])
  }
  return $p
}

# Descobre a URL de download de um asset da ultima release do GitHub.
# O padrao e casado contra o NOME do arquivo, igual ao instalar.sh.
function Get-UrlRelease {
  param([string]$Repo, [string]$Padrao)
  try {
    $r = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" `
                           -Headers @{ 'User-Agent' = 'bvba-qa-installer' } -TimeoutSec 30
  } catch {
    return $null
  }
  foreach ($a in $r.assets) {
    if ($a.name -match $Padrao) { return $a.browser_download_url }
  }
  return $null
}

function Get-Arquivo {
  param([string]$Url, [string]$Destino)
  try {
    Invoke-WebRequest -Uri $Url -OutFile $Destino -UseBasicParsing -TimeoutSec 300
    return $true
  } catch {
    return $false
  }
}

# ---------------------------------------------------------------------------
# 1. Git
# ---------------------------------------------------------------------------

Write-Titulo "Verificando o Git"
if (Existe git) {
  Write-Ok ("git presente (" + ((git --version) -split ' ')[2] + ")")
} else {
  Write-Aviso "git nao encontrado; instalando o Git for Windows"
  if (Existe winget) {
    winget install --id Git.Git -e --source winget `
      --accept-package-agreements --accept-source-agreements | Out-Null
  } else {
    Morre "instale o Git for Windows em https://git-scm.com/download/win e rode de novo"
  }
  $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
              [Environment]::GetEnvironmentVariable('Path','User')
  if (-not (Existe git)) {
    Morre "git instalado mas ainda fora do PATH — feche e reabra o PowerShell, depois rode de novo"
  }
  Write-Ok "git instalado"
}

# Localiza o bash do Git for Windows — e ele que roda o motor de sincronia.
$BashExe = $null
$candidatos = @(
  (Join-Path $env:ProgramFiles 'Git\bin\bash.exe'),
  (Join-Path ${env:ProgramFiles(x86)} 'Git\bin\bash.exe'),
  (Join-Path $env:LOCALAPPDATA 'Programs\Git\bin\bash.exe')
)
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if ($gitCmd) {
  $candidatos += (Join-Path (Split-Path (Split-Path $gitCmd.Source -Parent) -Parent) 'bin\bash.exe')
}
foreach ($c in $candidatos) {
  if ($c -and (Test-Path $c)) { $BashExe = $c; break }
}
if ($BashExe) { Write-Ok "bash do Git encontrado" }
else { Write-Aviso "nao achei o bash do Git; a sincronia de fundo pode nao funcionar" }

# ---------------------------------------------------------------------------
# 2. Obsidian
# ---------------------------------------------------------------------------

function Test-ObsidianInstalado {
  $caminhos = @(
    (Join-Path $env:LOCALAPPDATA 'Obsidian\Obsidian.exe'),
    (Join-Path $env:ProgramFiles 'Obsidian\Obsidian.exe')
  )
  foreach ($p in $caminhos) { if (Test-Path $p) { return $true } }
  return [bool](Get-Command obsidian -ErrorAction SilentlyContinue)
}

if (-not $SemObsidian) {
  Write-Titulo "Instalando o Obsidian"
  if (Test-ObsidianInstalado) {
    Write-Ok "Obsidian ja esta instalado"
  } else {
    $instalou = $false
    if (Existe winget) {
      try {
        winget install --id Obsidian.Obsidian -e --source winget `
          --accept-package-agreements --accept-source-agreements | Out-Null
        $instalou = $true
      } catch {
        Write-Aviso "winget falhou; tentando o download direto"
      }
    }
    if (-not $instalou) {
      $url = Get-UrlRelease -Repo 'obsidianmd/obsidian-releases' -Padrao '^Obsidian-[\d.]+\.exe$'
      if (-not $url) { Morre "nao consegui descobrir a versao mais recente do Obsidian" }
      $exe = Join-Path $env:TEMP 'ObsidianSetup.exe'
      if (-not (Get-Arquivo -Url $url -Destino $exe)) { Morre "falha ao baixar o Obsidian" }
      Write-Aviso "abrindo o instalador do Obsidian — conclua a instalacao na janela"
      Start-Process -FilePath $exe -Wait
      Remove-Item $exe -ErrorAction SilentlyContinue
    }
    if (Test-ObsidianInstalado) { Write-Ok "Obsidian instalado" }
    else { Write-Aviso "nao consegui confirmar a instalacao do Obsidian" }
  }
} else {
  Write-Titulo "Instalacao do Obsidian pulada (-SemObsidian)"
}

# ---------------------------------------------------------------------------
# 3. Vault
# ---------------------------------------------------------------------------

Write-Titulo "Preparando o vault"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PossivelVault = Split-Path -Parent $ScriptDir

if ([string]::IsNullOrWhiteSpace($Vault)) {
  git -C $PossivelVault rev-parse --git-dir *>$null
  if ($LASTEXITCODE -eq 0) {
    $Vault = $PossivelVault          # rodando de dentro do repositorio ja clonado
  } else {
    $Vault = Join-Path ([Environment]::GetFolderPath('MyDocuments')) $VaultName
  }
}

git -C $Vault rev-parse --git-dir *>$null
if ($LASTEXITCODE -eq 0) {
  Write-Ok "usando o vault existente em $Vault"
} else {
  if ((Test-Path $Vault) -and (Get-ChildItem $Vault -Force -ErrorAction SilentlyContinue)) {
    Morre "$Vault ja existe e nao esta vazio; use -Vault com outro caminho"
  }
  $pai = Split-Path -Parent $Vault
  if ($pai -and -not (Test-Path $pai)) { New-Item -ItemType Directory -Path $pai -Force | Out-Null }
  git clone $RepoUrl $Vault
  if ($LASTEXITCODE -ne 0) { Morre "falha ao clonar o vault de $RepoUrl" }
  Write-Ok "vault clonado em $Vault"
}

$Vault = (Resolve-Path $Vault).Path

Write-Titulo "Ajustando o git do vault"
git -C $Vault config core.quotepath false
git -C $Vault config core.precomposeunicode true
git -C $Vault config core.autocrlf false      # o .gitattributes ja normaliza as pontas de linha
git -C $Vault config pull.rebase false
git -C $Vault config merge.ff false
git -C $Vault config push.default current
# Nomes de notas costumam passar de 260 caracteres com pastas aninhadas.
git -C $Vault config core.longpaths true
Write-Ok "git do vault configurado para sincronia entre sistemas diferentes"

git -C $Vault config user.name *>$null
if ($LASTEXITCODE -ne 0) {
  git -C $Vault config user.name  "$env:USERNAME@$env:COMPUTERNAME"
  git -C $Vault config user.email "$env:USERNAME@$env:COMPUTERNAME.local"
  Write-Aviso "identidade do git definida automaticamente; ajuste com: git -C `"$Vault`" config user.name `"Seu Nome`""
}

# ---------------------------------------------------------------------------
# 4. Plugin obsidian-git
# ---------------------------------------------------------------------------

Write-Titulo "Instalando o plugin de sincronia (obsidian-git)"
$PluginDir = Join-Path $Vault '.obsidian\plugins\obsidian-git'
New-Item -ItemType Directory -Path $PluginDir -Force | Out-Null

$pluginFalhou = $false
foreach ($arquivo in @('main.js','manifest.json','styles.css')) {
  $padrao = '^' + [regex]::Escape($arquivo) + '$'
  $url = Get-UrlRelease -Repo 'Vinzent03/obsidian-git' -Padrao $padrao
  if ($url -and (Get-Arquivo -Url $url -Destino (Join-Path $PluginDir $arquivo))) {
    Write-Ok $arquivo
  } elseif ($arquivo -eq 'styles.css') {
    continue    # nem toda release publica styles.css
  } else {
    $pluginFalhou = $true
    Write-Erro "nao consegui baixar $arquivo"
  }
}

if ($pluginFalhou) {
  Write-Aviso "o plugin nao foi instalado automaticamente."
  Write-Aviso "instale pelo app: Configuracoes > Plugins da comunidade > Procurar > 'Git'."
  Write-Aviso "as configuracoes dele ja estao no vault e serao aplicadas sozinhas."
} else {
  Write-Ok "plugin instalado e ja configurado (sincroniza a cada $Intervalo min com o app aberto)"
}

# ---------------------------------------------------------------------------
# 5. Registro do vault no Obsidian
# ---------------------------------------------------------------------------

Write-Titulo "Registrando o vault no Obsidian"
$ObsidianDir  = Join-Path $env:APPDATA 'obsidian'
$ObsidianJson = Join-Path $ObsidianDir 'obsidian.json'
New-Item -ItemType Directory -Path $ObsidianDir -Force | Out-Null

# id de 16 hex derivado do caminho — estavel entre execucoes
$md5   = [System.Security.Cryptography.MD5]::Create()
$hash  = $md5.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Vault))
$VaultId = -join ($hash | ForEach-Object { $_.ToString('x2') })
$VaultId = $VaultId.Substring(0,16)
$Agora   = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()

try {
  if (Test-Path $ObsidianJson) {
    $cfg = Get-Content $ObsidianJson -Raw -Encoding UTF8 | ConvertFrom-Json
  } else {
    $cfg = [PSCustomObject]@{}
  }
  # Operador -contains, e nao o metodo .Contains(): o metodo lanca excecao
  # quando o objeto ainda nao tem propriedade nenhuma (obsidian.json novo).
  if ($cfg.PSObject.Properties.Name -notcontains 'vaults') {
    $cfg | Add-Member -NotePropertyName vaults -NotePropertyValue ([PSCustomObject]@{}) -Force
  }
  $entrada = [PSCustomObject]@{ path = $Vault; ts = $Agora; open = $true }
  $cfg.vaults | Add-Member -NotePropertyName $VaultId -NotePropertyValue $entrada -Force
  $cfg | ConvertTo-Json -Depth 10 | Set-Content $ObsidianJson -Encoding UTF8
  Write-Ok "vault registrado — o Obsidian vai abrir nele direto"
} catch {
  Write-Aviso "nao consegui editar $ObsidianJson"
  Write-Aviso "abra o app e use 'Abrir pasta como vault' apontando para $Vault"
}

# ---------------------------------------------------------------------------
# 6. Sincronia de fundo (Tarefa Agendada)
# ---------------------------------------------------------------------------

if (-not $SemAgendador) {
  Write-Titulo "Agendando a sincronia de fundo"
  if (-not $BashExe) {
    Write-Aviso "sem o bash do Git, nao da para agendar; a sincronia vai rodar so com o Obsidian aberto"
  } else {
    try {
      $syncBash = (ConvertTo-CaminhoBash (Join-Path $Vault 'scripts\sync.sh'))
      $syncDir  = Join-Path $Vault '.sync'
      New-Item -ItemType Directory -Path $syncDir -Force | Out-Null

      # Launcher .vbs: roda o bash com a janela oculta, senao um console preto
      # pisca na tela do usuario a cada ciclo de sincronia.
      $cmdLinha = '"' + $BashExe + '" -c "' + "'" + $syncBash + "' --quiet" + '"'
      $vbsPath  = Join-Path $syncDir 'sync-oculto.vbs'
      $vbsCmd   = $cmdLinha -replace '"', '""'
      @(
        'Set sh = CreateObject("WScript.Shell")'
        ('sh.Run "' + $vbsCmd + '", 0, False')
      ) | Set-Content -Path $vbsPath -Encoding ASCII

      $acao = New-ScheduledTaskAction -Execute 'wscript.exe' `
                -Argument ('"' + $vbsPath + '"') -WorkingDirectory $Vault
      $gatilho = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
                   -RepetitionInterval (New-TimeSpan -Minutes $Intervalo)
      $config = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
                  -DontStopIfGoingOnBatteries -StartWhenAvailable `
                  -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
                  -MultipleInstances IgnoreNew

      Register-ScheduledTask -TaskName $TaskName -Action $acao -Trigger $gatilho `
        -Settings $config -Description "Sincroniza o vault Obsidian $VaultName" -Force | Out-Null

      Write-Ok "tarefa agendada ativa (a cada $Intervalo min, mesmo com o Obsidian fechado)"
    } catch {
      Write-Aviso "nao consegui criar a tarefa agendada: $($_.Exception.Message)"
      Write-Aviso "a sincronia continua funcionando com o Obsidian aberto"
    }
  }
} else {
  Write-Titulo "Agendador pulado (-SemAgendador)"
}

# ---------------------------------------------------------------------------
# 7. Verificacao
# ---------------------------------------------------------------------------

Write-Titulo "Testando a sincronia"
if ($BashExe) {
  $syncBash = (ConvertTo-CaminhoBash (Join-Path $Vault 'scripts\sync.sh'))
  & $BashExe -c "'$syncBash' --quiet"
  if ($LASTEXITCODE -eq 0) {
    Write-Ok "ciclo de sincronia concluido com sucesso"
  } else {
    Write-Aviso "o ciclo de teste nao completou — provavelmente falta autenticacao no GitHub"
    Write-Aviso "veja o log em $Vault\.sync\sync.log"
  }
} else {
  Write-Aviso "sem o bash do Git nao da para testar a sincronia por aqui"
}

# ---------------------------------------------------------------------------
# Resumo
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "Pronto." -ForegroundColor White
Write-Host ""
Write-Host "  Vault:      $Vault"
Write-Host "  Intervalo:  a cada $Intervalo min (app aberto E app fechado)"
Write-Host "  Conflitos:  nada e sobrescrito — a sua versao vira uma copia ao lado"
Write-Host ""
Write-Host "Comandos uteis" -ForegroundColor White
Write-Host "  .\scripts\instalar.ps1 -Remover      desligar a sincronia de fundo"
Write-Host "  Get-ScheduledTask -TaskName $TaskName   ver a tarefa agendada"
Write-Host "  (no Git Bash) ./scripts/sync.sh --status   ver o estado da sincronia"
Write-Host ""
Write-Host "Um detalhe que depende de voce" -ForegroundColor White
Write-Host "  O git precisa autenticar no GitHub sem pedir senha, senao a sincronia"
Write-Host "  de fundo trava esperando digitacao. O Git for Windows ja instala o"
Write-Host "  Git Credential Manager: faca um push manual uma vez e autorize na janela"
Write-Host "  que abrir. Depois disso a sincronia roda sozinha."
Write-Host ""
Write-Host "    cd `"$Vault`"; git push"
Write-Host ""
