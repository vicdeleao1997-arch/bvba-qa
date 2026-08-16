#Requires -Version 5.1
<#
.SYNOPSIS
  Sincroniza o repositorio da BVBA entre as maquinas. Versao do Windows 11.

.DESCRIPTION
  Espelho exato do sinc/sincronizar.sh, que roda no MacBook. As duas maquinas
  seguem a mesma ordem:

    1. tranca, para duas execucoes nunca se atropelarem
    2. recusa rodar se ha um merge/rebase pendente na frente
    3. barra dado de cliente e credencial antes de qualquer commit
    4. comita o que voce mexeu localmente
    5. traz o que a outra maquina mandou (rebase, nunca merge sujo)
    6. se o codigo mudou, roda os 156 testes antes de publicar
    7. envia

  Nunca usa --force. Nunca descarta trabalho. Em conflito real ele para,
  desfaz o rebase e avisa — o repositorio fica exatamente como estava.

.EXAMPLE
  .\sinc\sincronizar.ps1
.EXAMPLE
  .\sinc\sincronizar.ps1 -Simular
#>
[CmdletBinding()]
param(
  [switch]$Simular,
  [switch]$Silencioso
)

$ErrorActionPreference = 'Continue'

# --- localizacao -------------------------------------------------------------
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$raiz = (& git -C $aqui rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $raiz) {
  Write-Error "Nao estou dentro de um repositorio git."; exit 65
}
$raiz = $raiz.Trim()
Set-Location $raiz

$dirLog        = Join-Path $raiz 'sinc\.log'
$arqLog        = Join-Path $dirLog 'sincronizar.log'
$marcaProblema = Join-Path $dirLog 'PROBLEMA.txt'
$trava         = Join-Path $dirLog '.trava'
New-Item -ItemType Directory -Force -Path $dirLog | Out-Null

$maquina = if ($env:COMPUTERNAME) { $env:COMPUTERNAME } else { 'desconhecida' }
$agora   = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

# --- saida -------------------------------------------------------------------
function Registrar([string]$texto) {
  $linha = "{0} [{1}] {2}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $maquina, $texto
  Add-Content -Path $arqLog -Value $linha -Encoding UTF8
  if (-not $Silencioso) { Write-Host $texto }
}

function AvisarHumano([string]$titulo, [string]$texto) {
  # Toast do Windows. Se falhar, o log e o PROBLEMA.txt continuam valendo —
  # notificacao quebrada nunca derruba a sincronia.
  try {
    [void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
    $modelo = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
                [Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $textos = $modelo.GetElementsByTagName('text')
    $textos.Item(0).AppendChild($modelo.CreateTextNode($titulo)) | Out-Null
    $textos.Item(1).AppendChild($modelo.CreateTextNode($texto))  | Out-Null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($modelo)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('BVBA Sync').Show($toast)
  } catch {
    # sem toast nesta maquina; segue o jogo
  }
}

function PararComProblema([int]$codigo, [string]$texto) {
  Registrar "PARADO: $texto"
  @(
    "Sincronia parada em $agora na maquina $maquina", '',
    $texto, '',
    'O repositorio NAO foi alterado de forma destrutiva. Nada foi perdido.',
    "Detalhes em: $arqLog"
  ) | Set-Content -Path $marcaProblema -Encoding UTF8
  AvisarHumano 'BVBA — sincronia parada' $texto
  if (Test-Path $trava) { Remove-Item -Recurse -Force $trava -ErrorAction SilentlyContinue }
  exit $codigo
}

# --- trava -------------------------------------------------------------------
$travaMinha = $false
try {
  New-Item -ItemType Directory -Path $trava -ErrorAction Stop | Out-Null
  $travaMinha = $true
} catch {
  $idadeMin = ((Get-Date) - (Get-Item $trava).CreationTime).TotalMinutes
  if ($idadeMin -gt 30) {
    Registrar ("trava com {0:N0} min, presumo execucao morta — removendo" -f $idadeMin)
    Remove-Item -Recurse -Force $trava -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $trava -ErrorAction SilentlyContinue | Out-Null
    $travaMinha = $true
  } else {
    Registrar ("outra sincronia em andamento ({0:N0} min) — saindo sem fazer nada" -f $idadeMin)
    exit 0
  }
}

try {
  # --- estado do repositorio -------------------------------------------------
  $ramo = (& git rev-parse --abbrev-ref HEAD 2>$null).Trim()
  if ($ramo -eq 'HEAD') {
    PararComProblema 66 'O repositorio esta em HEAD destacado (detached HEAD). Rode: git checkout main'
  }
  $gitDir = Join-Path $raiz '.git'
  if ((Test-Path (Join-Path $gitDir 'rebase-merge')) -or
      (Test-Path (Join-Path $gitDir 'rebase-apply')) -or
      (Test-Path (Join-Path $gitDir 'MERGE_HEAD'))) {
    PararComProblema 67 'Ha um merge ou rebase pela metade neste repositorio. Termine ou cancele antes: git rebase --abort  (ou  git merge --abort)'
  }

  # --- barreira de dado sensivel ---------------------------------------------
  # O .gitignore ja bloqueia os padroes. Isto e o segundo cadeado, para o caso
  # de alguem ter feito `git add -f`. Regra da marca: base de telefones e
  # credencial NUNCA entram no Git — o repo e publico.
  $padroesProibidos = '(telefone|contatos|clientes|publico-personalizado|E164)[^/\\]*\.csv$|\.(pfx|p12|pem|key)$|(^|[/\\])\.env$'

  function VerificarSensivel {
    $lista = (& git diff --cached --name-only 2>$null) | Where-Object { $_ -imatch $padroesProibidos }
    if ($lista) {
      foreach ($f in $lista) { & git reset -q HEAD -- $f 2>$null }
      PararComProblema 68 ("Bloqueei o envio: arquivo com cara de dado de cliente ou credencial foi para o commit. Tirei do stage. Arquivos: " + ($lista -join ' '))
    }
  }

  # --- 1. comitar o que mudou aqui -------------------------------------------
  $mudancas = & git status --porcelain
  if ($mudancas) {
    $n = @($mudancas).Count
    if ($Simular) {
      Registrar "[simulacao] comitaria $n arquivo(s):"
      $mudancas | ForEach-Object { Registrar "    $_" }
    } else {
      & git add -A
      VerificarSensivel
      & git diff --cached --quiet
      if ($LASTEXITCODE -ne 0) {
        & git commit -q -m "sync($maquina): $n arquivo(s) — $agora"
        if ($LASTEXITCODE -ne 0) { PararComProblema 69 "git commit falhou. Veja $arqLog" }
        Registrar "comitado: $n arquivo(s)"
      } else {
        Registrar 'nada para comitar depois do filtro'
      }
    }
  } else {
    Registrar 'nada mudou aqui'
  }

  # --- 2. buscar o que veio da outra maquina ---------------------------------
  $tentativa = 0
  while ($true) {
    & git fetch -q origin $ramo 2>&1 | Add-Content -Path $arqLog -Encoding UTF8
    if ($LASTEXITCODE -eq 0) { break }
    $tentativa++
    if ($tentativa -ge 4) {
      PararComProblema 70 'Nao consegui falar com o GitHub depois de 4 tentativas. Sem internet, ou a credencial expirou. Teste: git ls-remote origin'
    }
    Start-Sleep -Seconds ([Math]::Pow(2, $tentativa))
  }

  $atras  = [int](& git rev-list --count "HEAD..origin/$ramo" 2>$null)
  $frente = [int](& git rev-list --count "origin/$ramo..HEAD" 2>$null)
  Registrar "estado: $frente commit(s) a enviar, $atras a receber"

  if ($atras -gt 0) {
    if ($Simular) {
      Registrar "[simulacao] traria $atras commit(s) por rebase"
    } else {
      & git rebase -q "origin/$ramo" 2>&1 | Add-Content -Path $arqLog -Encoding UTF8
      if ($LASTEXITCODE -ne 0) {
        & git rebase --abort 2>$null
        PararComProblema 71 'Conflito real: voce e a outra maquina editaram as mesmas linhas. Desfiz o rebase, seu trabalho esta intacto no commit local. Resolva a mao: git pull --rebase'
      }
      Registrar "recebido: $atras commit(s) da outra maquina"
    }
  }

  # --- 3. portao dos testes --------------------------------------------------
  # So roda quando os commits a enviar tocam codigo. Doc e planilha passam direto.
  $frente = [int](& git rev-list --count "origin/$ramo..HEAD" 2>$null)

  if ($frente -gt 0 -and -not $Simular) {
    $tocouCodigo = & git diff --name-only "origin/$ramo...HEAD" -- agente_drop testes ferramentas .github 2>$null
    if ($tocouCodigo) {
      # Ordem importa no Windows: o launcher `py` e o mais confiavel, e
      # `python3` costuma ser o stub da Microsoft Store, que nao executa nada.
      $py = $null
      foreach ($nome in @('py', 'python', 'python3')) {
        $c = Get-Command $nome -ErrorAction SilentlyContinue
        if ($c) { $py = $c; break }
      }
      if (-not $py) {
        Registrar 'AVISO: codigo mudou mas nao achei python — enviando sem testar'
      } else {
        Registrar "codigo mudou — rodando os testes antes de enviar ($($py.Name))"
        & $py.Source -m unittest discover -s testes -t . 2>&1 | Add-Content -Path $arqLog -Encoding UTF8
        if ($LASTEXITCODE -ne 0) {
          Registrar 'TESTES FALHARAM — seu trabalho esta comitado aqui, mas NAO foi enviado'
          @(
            "Sincronia segurou o envio em $agora na maquina $maquina", '',
            'Os testes do agente de drop falharam. Seu trabalho esta salvo no',
            'commit local — nada foi perdido — mas nao subiu, para nao quebrar',
            'a outra maquina.', '',
            'Rode para ver o erro:',
            '  python -m unittest discover -s testes -t .', '',
            'Corrija e a proxima sincronia envia sozinha.'
          ) | Set-Content -Path $marcaProblema -Encoding UTF8
          AvisarHumano 'BVBA — envio segurado' 'Testes falharam. Trabalho salvo local, nao enviado.'
          exit 72
        }
        Registrar 'testes passaram'
      }
    }
  }

  # --- 4. enviar -------------------------------------------------------------
  if ($frente -gt 0) {
    if ($Simular) {
      Registrar "[simulacao] enviaria $frente commit(s) para origin/$ramo"
    } else {
      $tentativa = 0
      while ($true) {
        & git push -q origin $ramo 2>&1 | Add-Content -Path $arqLog -Encoding UTF8
        if ($LASTEXITCODE -eq 0) { break }
        $tentativa++
        if ($tentativa -ge 4) {
          PararComProblema 73 'Nao consegui enviar depois de 4 tentativas. Se a outra maquina publicou nesse meio tempo, rode de novo — a proxima passada resolve.'
        }
        Start-Sleep -Seconds ([Math]::Pow(2, $tentativa))
        & git fetch -q origin $ramo 2>$null
        & git rebase -q "origin/$ramo" 2>$null
        if ($LASTEXITCODE -ne 0) { & git rebase --abort 2>$null }
      }
      Registrar "enviado: $frente commit(s)"
    }
  }

  # --- fim -------------------------------------------------------------------
  Remove-Item -Force $marcaProblema -ErrorAction SilentlyContinue
  if ($Simular) {
    Registrar 'simulacao terminada — nada foi escrito'
  } else {
    Registrar ("em dia (" + (& git rev-parse --short HEAD).Trim() + ")")
  }

  # Log nao cresce para sempre: corta em 2000 linhas.
  if ((Get-Content $arqLog -ErrorAction SilentlyContinue).Count -gt 2000) {
    Get-Content $arqLog -Tail 1000 | Set-Content "$arqLog.tmp" -Encoding UTF8
    Move-Item -Force "$arqLog.tmp" $arqLog
  }
}
finally {
  if ($travaMinha -and (Test-Path $trava)) {
    Remove-Item -Recurse -Force $trava -ErrorAction SilentlyContinue
  }
}
exit 0
