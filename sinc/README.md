# Sincronia entre o MacBook e o desktop Windows 11

O GitHub é o meio de campo. As duas máquinas rodam a mesma rotina a cada 15
minutos: comita o que você mexeu, traz o que a outra mandou, envia. Você não
pensa nisso.

```
   MacBook  ──┐                    ┌──  Desktop Windows 11
  (launchd)   ├──►  GitHub  ◄──────┤   (Agendador de Tarefas)
   15 em 15   ┘   vicdeleao1997    └──   15 em 15
                    /bvba-qa
```

---

## Instalar

Uma vez em cada máquina. O instalador confere tudo **antes** de ligar e recusa
ligar se algo falharia calado depois.

**MacBook**

```bash
git clone https://github.com/vicdeleao1997-arch/bvba-qa.git
cd bvba-qa
./sinc/instalar-macos.sh
```

**Desktop Windows 11** — PowerShell, na pasta do repositório:

```powershell
git clone https://github.com/vicdeleao1997-arch/bvba-qa.git
cd bvba-qa
.\sinc\instalar-windows.ps1
```

Se o PowerShell reclamar de política de execução:
`powershell -ExecutionPolicy Bypass -File .\sinc\instalar-windows.ps1`

### O que o instalador confere antes de ligar

1. **git instalado**
2. **credencial do GitHub funcionando sem pedir senha** — este é o teste que
   importa. Uma tarefa de fundo não tem como digitar senha: se a credencial não
   estiver guardada, a sincronia falharia todo dia sem ninguém notar. O
   instalador roda `git ls-remote` e se recusa a continuar se travar.
3. **uma passada completa em simulação**

Se o passo 2 falhar, ele diz exatamente o que rodar (`credential.helper
osxkeychain` no Mac, `credential.helper manager` no Windows).

---

## No dia a dia

Nada. É esse o ponto.

Quando quiser forçar agora:

```bash
./sinc/sincronizar.sh              # Mac
```
```powershell
.\sinc\sincronizar.ps1             # Windows
```

Ver o que andou acontecendo:

```bash
tail -f sinc/.log/sincronizar.log                        # Mac
```
```powershell
Get-Content sinc\.log\sincronizar.log -Tail 30 -Wait     # Windows
```

Desligar:

```bash
./sinc/instalar-macos.sh --remover
```
```powershell
.\sinc\instalar-windows.ps1 -Remover
```

---

## As três travas de segurança

**1. Dado de cliente nunca sai daqui.** Antes de qualquer commit, a sincronia
varre o que está no stage atrás de nome de arquivo com cara de base de
telefones (`*clientes*.csv`, `*telefone*.csv`, `*E164*.csv`…) ou de credencial
(`.env`, `*.pem`, `*.key`). Se achar, **tira do stage, para tudo e avisa**. É o
segundo cadeado — o `.gitignore` é o primeiro. Testado inclusive contra
`git add -f`.

**2. Código quebrado não viaja.** Se os commits a enviar tocam `agente_drop/`,
`testes/`, `ferramentas/` ou `.github/`, a sincronia roda os 156 testes antes
de publicar. Falhou? Seu trabalho **fica comitado localmente** — nada se perde —
mas não sobe, para não quebrar a outra máquina. Corrigiu, a próxima passada
envia sozinha. Documento e planilha passam direto, sem teste.

**3. Conflito nunca vira sobrescrita.** Se você e a outra máquina editaram as
**mesmas linhas** do mesmo arquivo, a sincronia desfaz o rebase, deixa o
repositório exatamente como estava e cria `sinc/.log/PROBLEMA.txt` mais uma
notificação. Nenhum `--force` existe neste código. Resolva com
`git pull --rebase` e siga.

Editar **arquivos diferentes** ao mesmo tempo não é conflito — as duas máquinas
convergem sozinhas.

---

## O que NÃO é sincronizado

Sincronia honesta é sincronia com fronteira declarada. Isto aqui cuida **só do
repositório git**:

| | Sincronizado por |
|---|---|
| Este repositório (código, planos, pesquisa) | **esta sincronia** |
| Cofre do Obsidian | Obsidian Sync, ou o próprio iCloud/Drive |
| Fotos do shooting, PDFs de ficha técnica | Google Drive |
| Base de telefones dos clientes | Google Drive — **e nunca o Git**, por regra da marca |
| Token da Nuvemshop, credencial da Meta | `.env` local em cada máquina, e os secrets do GitHub |

O `.env` fica de fora de propósito. Copie `.env.exemplo` para `.env` em cada
máquina e preencha lá — segredo não anda por repositório público.

---

## Fim de linha: por que existe um `.gitattributes`

O Windows grava CRLF, o Mac grava LF. Sem tratamento, cada troca de máquina faz
o git enxergar o arquivo *inteiro* como modificado, e duas máquinas
sincronizando viram um moinho de conflito falso.

O `.gitattributes` na raiz normaliza tudo para LF no repositório e marca os
binários (`.png`, `.pdf`) como intocáveis. Quando isto foi ligado, o
`catalogo/produtos.csv` estava versionado em CRLF — foi convertido, com os dados
conferidos linha a linha.

---

## Códigos de saída

Úteis se você for encadear a sincronia em outro script.

| | |
|---|---|
| `0` | em dia |
| `64–65` | argumento inválido, ou não é um repositório git |
| `66` | HEAD destacado — rode `git checkout main` |
| `67` | merge ou rebase pela metade na sua frente |
| `68` | **dado sensível barrado** |
| `69` | `git commit` falhou |
| `70` | GitHub inalcançável depois de 4 tentativas |
| `71` | **conflito real** — precisa de você |
| `72` | testes falharam; trabalho salvo local, envio segurado |
| `73` | `git push` falhou depois de 4 tentativas |
| `75` | não consegui pegar a trava |

---

## Quando algo trava

**`sinc/.log/PROBLEMA.txt` existe** — abra. Ele diz o que houve, quando e em
qual máquina. Some sozinho na primeira sincronia que der certo.

**"Nao consegui falar com o GitHub"** — credencial expirou. Rode
`git fetch origin` na mão, autentique, e a sincronia volta ao normal sozinha.

**Sincronia parece morta** — confira se o agendador está de pé:

```bash
launchctl list | grep bvba                                    # Mac
```
```powershell
Get-ScheduledTask -TaskName 'BVBA - Sincronizar repositorio'  # Windows
```

**Trava presa** — se uma execução morrer no meio (queda de energia), a trava
fica. A sincronia seguinte detecta que ela passou de 30 minutos e remove
sozinha. Para forçar: apague `sinc/.log/.trava`.
