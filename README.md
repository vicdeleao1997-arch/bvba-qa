# bvba-qa — vault Obsidian em sincronia total

Este repositório **é** o vault. Clonar o repositório é ter o vault; o
histórico do git é o histórico das notas.

Um comando instala o Obsidian, configura tudo e deixa a máquina
sincronizando — com o app aberto e com o app fechado.

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
2. configura o git do vault para sincronizar entre Windows, macOS e Linux
   sem conflito falso de acentuação ou de fim de linha;
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
cd <pasta-do-vault>; git push
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

Se a mesma nota mudou em dois PCs antes de sincronizar:

- a versão que chegou primeiro fica com o **nome original** (os dois PCs
  convergem para o mesmo arquivo);
- a sua versão é salva ao lado como `Nota (conflito <pc> <data>).md`.

Nenhum byte é descartado. Casos assimétricos também são tratados: nota
apagada num PC e editada no outro é **restaurada** — a edição vence a
exclusão, porque perder trabalho é pior que um arquivo a mais.

### O que sincroniza

Sincroniza: notas, anexos, canvas, e as configurações do vault
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

---

## Solução de problemas

| Sintoma | O que fazer |
|---|---|
| "não consegui baixar main.js" | Instale pelo app: *Configurações → Plugins da comunidade → Procurar → "Git"*. As configurações já estão no vault. |
| Sincronia parou | `./scripts/sync.sh --status` e depois `cat .sync/sync.log` |
| Pede senha o tempo todo | Configure SSH ou o credential manager (seção *Autenticação*) |
| Muitas cópias de conflito | Dois PCs editando junto entre ciclos. Diminua o intervalo: `./scripts/instalar.sh --intervalo 2` |
| Desligar a sincronia de fundo | `./scripts/instalar.sh --remover` |
| Sincronizar com a sessão deslogada (Linux) | `sudo loginctl enable-linger $USER` |

Verificar o agendador:

```bash
systemctl --user status obsidian-sync-bvba-qa.timer   # Linux
launchctl list | grep obsidian-sync                   # macOS
Get-ScheduledTask -TaskName ObsidianSync-bvba-qa      # Windows
```
