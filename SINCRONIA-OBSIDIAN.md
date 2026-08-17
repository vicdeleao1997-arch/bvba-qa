# Vault Obsidian — sincronia total entre PCs

Este repositório também é um vault Obsidian. Abrir a pasta clonada no
Obsidian dá acesso a todo o material escrito da marca — `PLANO.md`,
`plano-360/`, `pesquisa/`, `CLAUDE.md`, `HANDOFF.md` — com busca, links
entre notas e grafo, sincronizado entre todos os PCs.

O código (`agente_drop/`, `testes/`, `ferramentas/`) fica escondido dentro
do Obsidian: ele continua no repositório, só não aparece no explorador de
arquivos do app.

---

## ⚠️ Antes de ligar: este repositório tem dados sensíveis

A sincronia commita e envia **automaticamente**, a cada poucos minutos, sem
ninguém revisar. Neste repositório isso exige cuidado que um vault de notas
comum não exigiria:

- O `.gitignore` bloqueia bases de contato (`*contatos*.csv`,
  `*telefone*.csv`, `*clientes*.csv`, `*publico-personalizado*.csv`) e
  credenciais (`.env`, `*.pem`, `*.key`). **Não remova essas regras.**
- Como defesa extra, o `scripts/sync.sh` confere os arquivos antes de cada
  commit: se algo com cara de dado pessoal ou credencial estiver prestes a
  subir, ele tira aquele arquivo do commit, registra no log e sincroniza o
  resto. Nada de dado pessoal sobe por descuido.
- Ainda assim: **não coloque base de clientes nesta pasta.** Ela fica no
  Google Drive da marca.

Confira o que a sincronia está prestes a enviar a qualquer momento:

```bash
./scripts/sync.sh --status
```

---

## Instalação

### Linux e macOS

```bash
git clone https://github.com/vicdeleao1997-arch/bvba-qa.git
cd bvba-qa
./scripts/instalar.sh
```

### Windows (PowerShell)

```powershell
git clone https://github.com/vicdeleao1997-arch/bvba-qa.git
cd bvba-qa
.\scripts\instalar.ps1
```

Se o Windows bloquear a execução:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

O instalador:

1. instala o **git** e o **Obsidian**, se faltarem;
2. configura o git para sincronizar entre Windows, macOS e Linux sem
   conflito falso de acentuação ou de fim de linha;
3. instala e configura o plugin **obsidian-git**;
4. registra o vault no Obsidian — ele já abre direto nele;
5. agenda a sincronia de fundo (systemd, launchd ou Tarefa Agendada);
6. roda um ciclo de teste e mostra o resultado.

Ele é **idempotente**: rodar de novo na mesma máquina não duplica nada.

### Opções

| Opção (`.sh`) | Opção (`.ps1`) | Efeito |
|---|---|---|
| `--vault <caminho>` | `-Vault <caminho>` | onde colocar o vault |
| `--intervalo <min>` | `-Intervalo <min>` | intervalo da sincronia de fundo (padrão: 5) |
| `--sem-obsidian` | `-SemObsidian` | não instala o app, só a sincronia |
| `--sem-agendador` | `-SemAgendador` | não cria a tarefa de fundo |
| `--remover` | `-Remover` | desliga só a sincronia de fundo |

---

## Autenticação no GitHub

**É o único passo que depende de você.** Sem isso, a sincronia de fundo
trava esperando uma senha que ninguém vai digitar.

**Windows** — o Git for Windows já traz o Git Credential Manager. Faça um
push manual uma vez e autorize na janela que abrir:

```powershell
cd <pasta-do-repo>; git push
```

**Linux e macOS** — o caminho mais estável é chave SSH:

```bash
ssh-keygen -t ed25519 -C "bvba-qa"
cat ~/.ssh/id_ed25519.pub          # cole em github.com/settings/keys
git remote set-url origin git@github.com:vicdeleao1997-arch/bvba-qa.git
```

Confirme com `./scripts/sync.sh --status`.

---

## Como a sincronia funciona

Dois mecanismos cobrindo os dois estados do app:

| Situação | Quem sincroniza | Padrão |
|---|---|---|
| Obsidian aberto | plugin obsidian-git | a cada 2 min |
| Obsidian fechado | systemd / launchd / Tarefa Agendada | a cada 5 min |

Os dois chamam a mesma lógica de merge, e uma trava (`.sync/lock`) impede
que rodem em cima um do outro.

### Conflitos: nada é sobrescrito

Se o mesmo arquivo mudou em dois PCs antes de sincronizar:

- a versão que chegou primeiro fica com o **nome original** (os dois PCs
  convergem para o mesmo arquivo);
- a sua versão é salva ao lado, como
  `Nota (conflito NOME-DO-PC DATA HORA).md`.

Nenhum byte é descartado. Casos assimétricos também são tratados: arquivo
apagado num PC e editado no outro é **restaurado** — a edição vence a
exclusão, porque perder trabalho é pior que um arquivo a mais.

### O que sincroniza

Tudo que já está versionado no repositório, mais as configurações do vault
(`.obsidian/`) — tema, atalhos, plugins ativos, modelos.

Não sincroniza (proposital, é estado local de cada máquina): layout de
janelas (`workspace.json`), cache, lixeira, e os binários dos plugins —
que o instalador baixa da release oficial.

### Sincronia manual

```bash
./scripts/sync.sh            # sincroniza agora
./scripts/sync.sh --status   # mostra o estado, não altera nada
./scripts/sync.sh --quiet    # sem saída (usado pelo agendador)
```

Log em `.sync/sync.log` (rotaciona em 1 MB).

---

## Estrutura do vault

O material da marca já está organizado nas pastas do repositório
(`plano-360/`, `pesquisa/`, `catalogo/`). O vault só acrescenta o que
faltava para o dia a dia:

| Pasta | Para que serve |
|---|---|
| `00 - Inbox` | entrada rápida; notas novas caem aqui |
| `50 - Diário` | notas diárias (`Ctrl/Cmd + P` → *Nota diária*) |
| `80 - Modelos` | modelos de nota (diária, projeto, reunião) |
| `90 - Anexos` | imagens e arquivos colados nas notas |

### Atalhos já configurados

| Atalho | Ação |
|---|---|
| `Ctrl/Cmd + Shift + S` | enviar alterações agora |
| `Ctrl/Cmd + Shift + P` | buscar alterações agora |
| `Ctrl/Cmd + Shift + G` | abrir o painel de sincronia |

---

## Notas de projeto

**Um motor de sincronia só.** No Windows, a Tarefa Agendada executa o
mesmo `scripts/sync.sh` através do Bash que vem com o Git for Windows.
Uma segunda implementação em PowerShell divergiria da primeira sem
ninguém perceber; um motor só significa que o que foi testado é o que
roda nas três plataformas.

**Sem merge automático de texto.** O git sabe juntar duas edições no
mesmo arquivo, mas em prosa isso produz parágrafos intercalados sem
sentido. Preferimos duas versões limpas lado a lado.

**Fast-forward quando possível.** A sincronia só cria commit de merge
quando os dois lados realmente divergiram. Forçar `--no-ff` faria cada
ciclo gerar um commit vazio, e os PCs ficariam se empurrando commits
para sempre sem nunca convergir.

**CI separado.** `testes.yml` roda os testes Python do agente de drop;
`testes-vault.yml` roda o motor de sincronia. Juntar os dois faria uma
falha de shell script mascarar o resultado dos testes do agente.

---

## Solução de problemas

| Sintoma | O que fazer |
|---|---|
| "não consegui baixar main.js" | Instale pelo app: *Configurações → Plugins da comunidade → Procurar → "Git"*. As configurações já estão no vault. |
| Sincronia parou | `./scripts/sync.sh --status` e depois `cat .sync/sync.log` |
| Pede senha o tempo todo | Configure SSH ou o credential manager (seção *Autenticação*) |
| "arquivo sensível retirado do commit" no log | A defesa de dados pessoais agiu. Tire o arquivo da pasta — ele não deve morar aqui. |
| Muitas cópias de conflito | Dois PCs editando junto entre ciclos. Diminua o intervalo: `./scripts/instalar.sh --intervalo 2` |
| Desligar a sincronia de fundo | `./scripts/instalar.sh --remover` |
| Sincronizar com a sessão deslogada (Linux) | `sudo loginctl enable-linger $USER` |

Verificar o agendador:

```bash
systemctl --user status obsidian-sync-bvba-qa.timer   # Linux
launchctl list | grep obsidian-sync                   # macOS
Get-ScheduledTask -TaskName ObsidianSync-bvba-qa      # Windows
```
