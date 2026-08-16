# Bem-vindo ao vault bvba-qa

Este é o nosso Obsidian compartilhado. Tudo que você escrever aqui aparece
nos outros PCs sozinho — e o contrário também.

## Como a sincronia funciona

Sincroniza em dois momentos, para cobrir os dois casos:

| Situação | Quem sincroniza | A cada |
|---|---|---|
| Obsidian aberto | plugin **Git** (dentro do app) | 2 min |
| Obsidian fechado | agendador do sistema | 5 min |

O histórico fica no GitHub. Nada é sobrescrito silenciosamente: se a mesma
nota for editada em dois PCs antes de sincronizar, as **duas versões são
mantidas** — a que chegou primeiro fica com o nome original e a sua aparece
ao lado como `Nota (conflito <pc> <data>).md`. Você abre, junta o que
interessa e apaga a cópia.

## Estrutura das pastas

| Pasta | Para que serve |
|---|---|
| `00 - Inbox` | entrada rápida; notas novas caem aqui |
| `10 - Projetos` | trabalho com prazo e resultado definido |
| `20 - Áreas` | responsabilidades contínuas, sem data de fim |
| `30 - Recursos` | referência, pesquisa, material de apoio |
| `40 - Arquivo` | encerrado, guardado para consulta |
| `50 - Diário` | notas diárias (`Ctrl/Cmd + P` → *Nota diária*) |
| `80 - Modelos` | modelos de nota |
| `90 - Anexos` | imagens e arquivos colados nas notas |

Nada disso é obrigatório — mova e renomeie à vontade, a sincronia acompanha.

## Atalhos já configurados

| Atalho | Ação |
|---|---|
| `Ctrl/Cmd + Shift + S` | enviar alterações agora |
| `Ctrl/Cmd + Shift + P` | buscar alterações agora |
| `Ctrl/Cmd + Shift + G` | abrir o painel de sincronia |

## Se algo parecer fora de sincronia

Primeiro, confira o estado pelo terminal, na pasta do vault:

```
./scripts/sync.sh --status
```

Isso mostra quantas alterações ainda não subiram e se o PC está atrás do
remoto. Para forçar um ciclo na hora:

```
./scripts/sync.sh
```

Se aparecer erro de autenticação, é o git pedindo credencial do GitHub —
veja a seção *Autenticação* no `README.md`.

## Ao instalar em mais um PC

Um comando só, dentro da pasta do vault clonado:

```
./scripts/instalar.sh          # Linux e macOS
.\scripts\instalar.ps1         # Windows
```

Ele instala o Obsidian, configura o plugin, registra o vault e liga a
sincronia de fundo.
