$fails = 0
$ErrorActionPreference = "Stop"

Write-Host "=== 1. Aspas do launcher VBS ==="
# Reproduz exatamente a construcao usada no instalar.ps1
$BashExe  = 'C:\Program Files\Git\bin\bash.exe'
$syncBash = '/c/Users/vic/Meus Documentos/bvba-qa/scripts/sync.sh'

$cmdLinha = '"' + $BashExe + '" -c "' + "'" + $syncBash + "' --quiet" + '"'
$vbsCmd   = $cmdLinha -replace '"', '""'
$linha    = ('sh.Run "' + $vbsCmd + '", 0, False')

Write-Host "  VBS gerado : $linha"

# Simula o parser do VBS: conteudo entre as aspas externas, com "" desdobrado em "
$ini   = $linha.IndexOf('"')
$fim   = $linha.LastIndexOf('"')
$inner = $linha.Substring($ini + 1, $fim - $ini - 1)
$resolvido = $inner -replace '""', '"'
Write-Host "  Comando real: $resolvido"

$esperado = '"C:\Program Files\Git\bin\bash.exe" -c "''/c/Users/vic/Meus Documentos/bvba-qa/scripts/sync.sh'' --quiet"'
if ($resolvido -eq $esperado) {
  Write-Host "  PASSOU  o VBS resolve para o comando correto" -ForegroundColor Green
} else {
  Write-Host "  FALHOU  esperado : $esperado" -ForegroundColor Red
  $fails++
}

# O caminho do bash tem espaco: precisa continuar entre aspas no comando final
if ($resolvido -match '^"C:\\Program Files\\Git\\bin\\bash\.exe"') {
  Write-Host "  PASSOU  caminho do bash com espaco fica protegido por aspas" -ForegroundColor Green
} else {
  Write-Host "  FALHOU  caminho do bash desprotegido" -ForegroundColor Red; $fails++
}
# O caminho do vault tem espaco: precisa continuar entre aspas simples para o bash
if ($resolvido -match "'/c/Users/vic/Meus Documentos/bvba-qa/scripts/sync\.sh'") {
  Write-Host "  PASSOU  caminho do vault com espaco protegido para o bash" -ForegroundColor Green
} else {
  Write-Host "  FALHOU  caminho do vault desprotegido" -ForegroundColor Red; $fails++
}

Write-Host ""
Write-Host "=== 2. Deteccao da chave 'vaults' no obsidian.json ==="
$vazio     = [PSCustomObject]@{}
$comVaults = [PSCustomObject]@{ vaults = [PSCustomObject]@{ abc = 1 } }

foreach ($caso in @( ,@('objeto vazio', $vazio, $false)) + @( ,@('ja com vaults', $comVaults, $true))) {
  $nome = $caso[0]; $obj = $caso[1]; $esp = $caso[2]
  $viaOperador = ($obj.PSObject.Properties.Name -contains 'vaults')
  if ($viaOperador -eq $esp) {
    Write-Host "  PASSOU  operador -contains em '$nome'" -ForegroundColor Green
  } else {
    Write-Host "  FALHOU  operador -contains em '$nome'" -ForegroundColor Red; $fails++
  }
  try {
    $viaMetodo = $obj.PSObject.Properties.Name.Contains('vaults')
    Write-Host "          (.Contains() respondeu '$viaMetodo' em '$nome')"
  } catch {
    Write-Host "  AVISO   .Contains() lancou excecao em '$nome'" -ForegroundColor Yellow
  }
}

Write-Host ""
Write-Host "=== 3. Round-trip do obsidian.json ==="
$cfg = [PSCustomObject]@{}
if ($cfg.PSObject.Properties.Name -notcontains 'vaults') {
  $cfg | Add-Member -NotePropertyName vaults -NotePropertyValue ([PSCustomObject]@{}) -Force
}
$entrada = [PSCustomObject]@{ path = 'C:\Users\vic\Documentos\bvba-qa'; ts = 1755300000000; open = $true }
$cfg.vaults | Add-Member -NotePropertyName 'a1b2c3d4e5f60718' -NotePropertyValue $entrada -Force
$json = $cfg | ConvertTo-Json -Depth 10
Write-Host $json

$volta = $json | ConvertFrom-Json
if ($volta.vaults.'a1b2c3d4e5f60718'.path -eq 'C:\Users\vic\Documentos\bvba-qa') {
  Write-Host "  PASSOU  caminho Windows sobrevive ao round-trip JSON" -ForegroundColor Green
} else {
  Write-Host "  FALHOU  caminho corrompido no JSON" -ForegroundColor Red; $fails++
}
if ($volta.vaults.'a1b2c3d4e5f60718'.open -eq $true) {
  Write-Host "  PASSOU  flag 'open' preservada" -ForegroundColor Green
} else {
  Write-Host "  FALHOU  flag 'open' perdida" -ForegroundColor Red; $fails++
}

# Preserva vaults ja existentes de outro projeto?
$existente = '{"vaults":{"ffff0000ffff0000":{"path":"C:\\Outro","ts":1,"open":false}}}'
$cfg2 = $existente | ConvertFrom-Json
$cfg2.vaults | Add-Member -NotePropertyName 'novo123456789abc' -NotePropertyValue $entrada -Force
$v2 = ($cfg2 | ConvertTo-Json -Depth 10) | ConvertFrom-Json
if ($v2.vaults.'ffff0000ffff0000'.path -eq 'C:\Outro' -and $v2.vaults.'novo123456789abc') {
  Write-Host "  PASSOU  vault preexistente do usuario NAO foi apagado" -ForegroundColor Green
} else {
  Write-Host "  FALHOU  registro destruiu vaults existentes" -ForegroundColor Red; $fails++
}

Write-Host ""
if ($fails -eq 0) { Write-Host "TODOS OS TESTES PASSARAM" -ForegroundColor Green }
else { Write-Host "$fails FALHA(S)" -ForegroundColor Red }
exit $fails
