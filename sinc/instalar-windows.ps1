#Requires -Version 5.1
<#
.SYNOPSIS
  Liga a sincronia automatica no desktop Windows 11.

.DESCRIPTION
  Registra uma tarefa no Agendador do Windows que roda o sinc\sincronizar.ps1
  a cada 15 minutos, escondida, sem piscar janela.

  Antes de registrar, confere o que faria a tarefa falhar calada mais tarde:
  git instalado, credencial do GitHub funcionando sem pedir senha, e uma
  passada de simulacao completa.

.EXAMPLE
  .\sinc\instalar-windows.ps1
.EXAMPLE
  .\sinc\instalar-windows.ps1 -Remover
.EXAMPLE
  .\sinc\instalar-windows.ps1 -IntervaloMinutos 5
#>
[CmdletBinding()]
param(
  [switch]$Remover,
  [int]$IntervaloMinutos = 15
)

$ErrorActionPreference = 'Stop'
$nomeTarefa = 'BVBA - Sincronizar repositorio'

$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$raiz = (& git -C $aqui rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $raiz) {
  Write-Error 'Rode este script de dentro do repositorio bvba-qa.'; exit 65
}
$raiz    = $raiz.Trim() -replace '/', '\'
$script  = Join-Path $raiz 'sinc\sincronizar.ps1'

if ($Remover) {
  Unregister-ScheduledTask -TaskName $nomeTarefa -Confirm:$false -ErrorAction SilentlyContinue
  Write-Host 'Sincronia automatica desligada. O repositorio e o historico continuam intactos.'
  Write-Host 'Voce ainda pode sincronizar na mao: .\sinc\sincronizar.ps1'
  exit 0
}

Write-Host 'Conferindo antes de ligar...'

# 1. git existe?
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host '  FALHOU: git nao esta instalado. Instale o Git for Windows: https://git-scm.com/download/win'
  exit 66
}
Write-Host '  ok  git'

# 2. credencial funciona sem pedir senha? Este e o teste que importa: uma tarefa
#    agendada nao tem como digitar senha. Se falhar aqui, falharia calada depois.
& git -C $raiz ls-remote origin *> $null
if ($LASTEXITCODE -ne 0) {
  Write-Host '  FALHOU: o git nao conseguiu falar com o GitHub sem interacao.'
  Write-Host ''
  Write-Host '  Resolva uma vez e rode este instalador de novo:'
  Write-Host '    git config --global credential.helper manager'
  Write-Host "    git -C `"$raiz`" fetch origin     # autentique uma vez; o Credential Manager guarda"
  exit 67
}
Write-Host '  ok  credencial do GitHub (sem pedir senha)'

# 3. uma passada de verdade, em simulacao
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script -Simular -Silencioso
if ($LASTEXITCODE -ne 0) {
  Write-Host '  FALHOU: a simulacao da sincronia deu erro. Veja sinc\.log\sincronizar.log'
  exit 68
}
Write-Host '  ok  simulacao da sincronia'

# --- registrar a tarefa ------------------------------------------------------
$acao = New-ScheduledTaskAction `
  -Execute 'powershell.exe' `
  -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`" -Silencioso" `
  -WorkingDirectory $raiz

# Um gatilho unico que se repete para sempre. E o jeito do Agendador de dizer
# "a cada N minutos, indefinidamente".
$gatilho = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
  -RepetitionInterval (New-TimeSpan -Minutes $IntervaloMinutos)

$config = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -Hidden `
  -MultipleInstances IgnoreNew `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

$quem = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

Unregister-ScheduledTask -TaskName $nomeTarefa -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName $nomeTarefa -Action $acao -Trigger $gatilho `
  -Settings $config -Principal $quem `
  -Description 'Mantem o repositorio bvba-qa em sincronia com o MacBook via GitHub.' | Out-Null

Write-Host ''
Write-Host "Ligado. O desktop sincroniza a cada $IntervaloMinutos minutos, sozinho."
Write-Host ''
Write-Host '  ver o que aconteceu:  Get-Content sinc\.log\sincronizar.log -Tail 30 -Wait'
Write-Host '  sincronizar agora:    .\sinc\sincronizar.ps1'
Write-Host '  desligar:             .\sinc\instalar-windows.ps1 -Remover'
