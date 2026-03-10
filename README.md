# IA Local Assistente Técnico

Assistente de linha de comando com **memória persistente**, **RAG local** e **execução de shell**, projetado para operar diretamente no terminal.

O agente:

- mantém memória de contexto persistente
- indexa documentos automaticamente
- consulta documentação antes de responder
- executa comandos locais sob confirmação
- opera inteiramente via terminal

---

# Arquitetura

WORKDIR/

conf/
  .env

base/
  profile/
    base_memory.json
    overlay_memory.json
    history.json

  tmp/
    .raw/

  knowledge/
    .raw/

  parsed/

---

# Dependências

Python 3.10+

Pacotes necessários:

pip install \
openai \
python-dotenv \
pypdf2 \
openpyxl \
pillow

---

# Instalação

## 1. Criar diretório

mkdir -p /data
cd /data

## 2. Clonar repositório
---
git clone https://github.com/mantenedor/iashell.git ia
cd ia
---

## 3. Criar ambiente virtual

python3 -m venv .venv
source .venv/bin/activate

---

## 4. Instalar dependências

pip install \
openai \
python-dotenv \
pypdf2 \
openpyxl \
pillow

---

## 5. Criar configuração

mkdir -p conf
vim conf/.env

Exemplo:

OPENAI_API_KEY=sk-xxxxx

TMP_DIR=/data/ia/base/tmp
TMP_RAW_DIR=/data/ia/base/tmp/.raw

KNOWLEDGE_DIR=/data/ia/base/knowledge
KNOWLEDGE_RAW_DIR=/data/ia/base/knowledge/.raw

PARSED_DIR=/data/ia/base/parsed

DOCS_INDEX_FILE=/data/ia/base/index.json
CHUNKS_FILE=/data/ia/base/chunks.jsonl

PROMPT_HISTORY_FILE=/data/ia/base/profile/.prompt_history

---

## 6. Criar estrutura de diretórios

mkdir -p base/profile
mkdir -p base/tmp/.raw
mkdir -p base/knowledge/.raw
mkdir -p base/parsed

---

## 7. Criar alias

Editar ~/.bashrc

Adicionar:

alias ia="/data/ia/run-prompt.sh"

Recarregar:

source ~/.bashrc

---

# Execução

Iniciar o assistente:

ia

---

# Comandos do Prompt

Executar shell:

!ls

A saída será exibida e poderá ser enviada para análise da IA.

---

Indexar documento:

:add /caminho/arquivo.pdf

---

Listar documentos:

:docs

---

Sair:

q

ou

quit

---

# Indexação automática

Arquivos colocados em:

base/tmp

ou

base/knowledge

são detectados automaticamente e indexados.

A indexação é incremental:

- arquivos novos → indexados
- arquivos alterados → reindexados
- arquivos iguais → ignorados

---

# Formatos suportados

PDF  
TXT  
CSV  
Excel  
Imagem

---

# Funcionamento do RAG

1. documento é copiado para .raw
2. parser extrai conteúdo
3. conteúdo é dividido em chunks
4. chunks são indexados
5. busca textual seleciona trechos relevantes
6. trechos são enviados ao modelo

---

# Memória

Localização:

base/profile/

Arquivos:

base_memory.json  
overlay_memory.json  
history.json

A memória pode ser editada manualmente.

---

# Segurança

Comandos shell não são executados automaticamente.

A saída é mostrada antes de ser enviada ao modelo.

---

# Atualização

cd /data/ia
git pull

---

# Backup

tar czf ia-backup.tar.gz base/

---

# Remoção

rm -rf /data/ia

Remover alias editando:

~/.bashrc

---

# Objetivo do projeto

Criar um assistente técnico local capaz de:

- operar no terminal
- consultar documentação local
- manter memória persistente
- auxiliar operações técnicas complexas
