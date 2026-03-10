# IA Local Assistente Técnico



Assistente de linha de comando com **memória persistente**, **RAG local** e **execução de shell**, projetado para operar diretamente no terminal.



O agente:

- mantém memória de contexto persistente

- indexa documentos automaticamente

- consulta documentação antes de responder

- executa comandos locais sob confirmação

- opera inteiramente via terminal



---



## Arquitetura



WORKDIR/

├── conf/

│   └── .env

├── base/

│   ├── profile/

│   │   ├── base_memory.json

│   │   ├── overlay_memory.json

│   │   ├── history.jsonl

│   │   └── .prompt_history

│   ├── tmp/

│   │   └── .raw/

│   ├── knowledge/

│   │   └── .raw/

│   ├── parsed/

│   ├── document_catalog.json

│   └── chunks.jsonl

├── prompt.py

├── memory.py

├── knowledge.py

├── connector.py

├── run-prompt.sh

└── requirements.txt



---



## Dependências



### Python 3.8+ (recomendado 3.10+)



### Pacotes necessários:



# Core

openai

python-dotenv



# PDF Processing

pypdf2

pdfplumber



# HTML Processing

beautifulsoup4

html2text

lxml



# Spreadsheets

openpyxl



# Images

pillow



# Text Processing

tiktoken



# Utilities

requests



### Instalação completa com pip:



pip install openai python-dotenv pypdf2 pdfplumber beautifulsoup4 html2text lxml openpyxl pillow tiktoken requests



---



## Instalação



### 1. Criar diretório



sudo mkdir -p /opt/ia/data

sudo chown $USER:$USER /opt/ia/data

cd /opt/ia/data



### 2. Clonar repositório



git clone https://github.com/mantenedor/iashell.git iashell

cd iashell



### 3. Criar ambiente virtual (opcional, mas recomendado)



python3 -m venv .venv

source .venv/bin/activate



### 4. Instalar dependências



pip install -r requirements.txt



### 5. Criar configuração



mkdir -p conf

cp .env.example conf/.env  # se existir, ou crie manualmente

vim conf/.env



Exemplo de .env:



# OpenAI

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx



# Diretórios base

BASE_DIR=/opt/ia/data/iashell/base



# Diretórios temporários

TMP_DIR=/opt/ia/data/iashell/base/tmp

TMP_RAW_DIR=/opt/ia/data/iashell/base/tmp/.raw



# Diretórios de conhecimento

KNOWLEDGE_DIR=/opt/ia/data/iashell/base/knowledge

KNOWLEDGE_RAW_DIR=/opt/ia/data/iashell/base/knowledge/.raw



# Diretório de arquivos parseados

PARSED_DIR=/opt/ia/data/iashell/base/parsed



# Arquivos de índice

DOCS_INDEX_FILE=/opt/ia/data/iashell/base/document_catalog.json

CHUNKS_FILE=/opt/ia/data/iashell/base/chunks.jsonl



# Arquivos de memória

BASE_MEMORY_FILE=/opt/ia/data/iashell/base/profile/base_memory.json

OVERLAY_MEMORY_FILE=/opt/ia/data/iashell/base/profile/overlay_memory.json

HISTORY_FILE=/opt/ia/data/iashell/base/profile/history.jsonl

PROMPT_HISTORY_FILE=/opt/ia/data/iashell/base/profile/.prompt_history



### 6. Criar estrutura de diretórios com permissões adequadas



# Criar estrutura

mkdir -p base/profile

mkdir -p base/tmp/.raw

mkdir -p base/knowledge/.raw

mkdir -p base/parsed



# Criar arquivos de índice vazios

echo '[]' > base/document_catalog.json

touch base/chunks.jsonl



# Ajustar permissões (usuário atual como dono)

chmod 755 /opt/ia/data/iashell

chmod 755 /opt/ia/data/iashell/base

chmod 750 /opt/ia/data/iashell/base/profile

chmod 750 /opt/ia/data/iashell/base/tmp

chmod 750 /opt/ia/data/iashell/base/tmp/.raw

chmod 750 /opt/ia/data/iashell/base/knowledge

chmod 750 /opt/ia/data/iashell/base/knowledge/.raw

chmod 750 /opt/ia/data/iashell/base/parsed

chmod 640 /opt/ia/data/iashell/base/document_catalog.json

chmod 640 /opt/ia/data/iashell/base/chunks.jsonl



### 7. Criar alias global



# Para usuário atual (recomendado)

echo 'alias ia="/opt/ia/data/iashell/run-prompt.sh"' >> ~/.bashrc

source ~/.bashrc



# OU para todos os usuários (requer sudo)

echo 'alias ia="/opt/ia/data/iashell/run-prompt.sh"' | sudo tee /etc/profile.d/ia.sh

sudo chmod 644 /etc/profile.d/ia.sh



### 8. Configurar memória inicial



# A primeira execução criará a memória base interativamente

ia



Durante a primeira execução, você será perguntado:

- Nome do agente

- Diretrizes

- Estilo de resposta



Exemplo:

Qual o meu nome? Hum

Quais as minha diretrizes? Você é um especialista em EOW

Como gostaria que eu respondesse? objetivamente



---



## Execução



Iniciar o assistente:



ia



Prompt de exemplo:

IA pronta (!comando para shell, :add <arquivo> para indexar, :docs para listar documentos, :diagnose <doc_id> para diagnóstico, q ou quit para sair)



> 



---



## Comandos do Prompt



| Comando | Descrição | Exemplo |

|---------|-----------|---------|

| !<comando> | Executa comando shell | !ls -la |

| :add <caminho> | Indexa documento | :add /tmp/manual.pdf |

| :docs | Lista documentos indexados | :docs |

| :diagnose <doc_id> | Diagnostica documento | :diagnose manual-abc123 |

| q ou quit | Sai do assistente | q |



### Exemplos de uso:



# Executar comando e analisar saída

> !df -h

--- saída do comando ---

Filesystem      Size  Used Avail Use% Mounted on

/dev/sda3        98G   45G   53G  46% /

--- fim ---



Pressione ENTER para enviar à IA ou Ctrl+C para cancelar:



# Indexar documento

> :add /opt/ia/data/iashell/base/knowledge/instalationguide.pdf

Ingerindo /opt/ia/data/iashell/base/knowledge/instalationguide.pdf...

Documento indexado: instalationguide-cda88194f2f6 (pdf)

Chunks gerados: 25

Resumo: Este guia de instalação do EOW versão 2.1...



# Listar documentos

> :docs

Documentos disponíveis (1):

- doc_id: instalationguide-cda88194f2f6

  nome: instalationguide.pdf

  tipo: pdf

  origem: knowledge

  tamanho_bytes: 4995295

  chunks: 25

  resumo: Este guia de instalação do EOW...



# Diagnosticar documento

> :diagnose instalationguide-cda88194f2f6



# Perguntar sobre documento

> do que se trata esse arquivo?



---



## Indexação automática



Arquivos colocados nos diretórios monitorados são detectados automaticamente:



- `base/tmp/` → origem `tmp` (arquivos temporários)

- `base/knowledge/` → origem `knowledge` (base de conhecimento)



A indexação é incremental:

- arquivos novos → indexados

- arquivos alterados → reindexados

- arquivos iguais → ignorados



Para adicionar arquivos manualmente:

cp documento.pdf /opt/ia/data/iashell/base/knowledge/

# O sistema detectará automaticamente na próxima iteração



---



## Formatos suportados



| Tipo | Extensões | Processamento |

|------|-----------|---------------|

| PDF | .pdf | Extração com pdfplumber (fallback PyPDF2) |

| HTML | .htm, .html | Parse com BeautifulSoup + conversão para Markdown |

| Texto | .txt, .md, .log, .json, .yaml, .yml, .ini, .cfg | Leitura direta |

| CSV/TSV | .csv, .tsv | Parse com detecção de delimitador |

| Planilhas | .xlsx, .xlsm | Leitura com openpyxl |

| Imagens | .png, .jpg, .jpeg, .webp, .bmp, .gif | Extração de metadados + sidecar files |



---



## Funcionamento do RAG



1. **Ingestão**: arquivo é copiado para `.raw/`

2. **Parsing**: conteúdo é extraído conforme o tipo

3. **Chunking**: texto é dividido em chunks de ~1800 tokens com sobreposição

4. **Indexação**: chunks são salvos com metadados e keywords

5. **Busca**: consultas buscam chunks relevantes por similaridade de termos

6. **Contexto**: chunks relevantes são enviados ao modelo junto com a pergunta



---



## Diagnóstico



O comando `:diagnose <doc_id>` fornece informações detalhadas:



============================================================

DIAGNÓSTICO DO DOCUMENTO: instalationguide-cda88194f2f6

============================================================



📋 METADADOS:

  Nome: instalationguide.pdf

  Tipo: pdf

  Tamanho: 4995295 bytes

  Chunks: 25

  Status: parsed

  Resumo: Este guia de instalação do EOW versão 2.1...



📄 ARQUIVO RAW: /opt/ia/data/iashell/base/knowledge/.raw/instalationguide-cda88194f2f6.pdf

  Tamanho: 4995295 bytes



📄 ARQUIVO PARSED: /opt/ia/data/iashell/base/parsed/instalationguide-cda88194f2f6.json

  Tamanho: 154320 bytes

  Páginas: 25

  Página 1 (primeiras 200 chars): # Enterprise Open Workspace Installation Guide...



🔍 CHUNKS: 25 encontrados

  Chunks com conteúdo real: 25



---



## Memória Persistente



Localização: `base/profile/`



Arquivos:

- `base_memory.json` → memória base imutável

- `overlay_memory.json` → ajustes incrementais

- `history.jsonl` → histórico de conversas

- `.prompt_history` → histórico de comandos (readline)



A memória pode ser editada manualmente para ajustar comportamento.



Exemplo de `base_memory.json`:

{

  "identidade": {

    "nome_agente": "Hum"

  },

  "diretrizes": {

    "texto": "Você é um especialista na solução Enterprise Open Workspace (EOW)..."

  },

  "resposta": {

    "estilo": "objetivamente"

  },

  "controles": {

    "base_imutavel": true

  }

}



---



## Segurança



- Comandos shell **não são executados automaticamente**

- A saída é mostrada antes de ser enviada ao modelo

- Confirmação explícita necessária para cada comando

- Documentos são armazenados localmente

- API key da OpenAI armazenada apenas no `.env` (não versionado)

- Permissões restritivas nos diretórios (750/640)



### Permissões recomendadas:



# Diretórios (acesso apenas para o dono e grupo)

find /opt/ia/data/iashell/base -type d -exec chmod 750 {} \;



# Arquivos (leitura/escrita apenas para o dono)

find /opt/ia/data/iashell/base -type f -exec chmod 640 {} \;



# Scripts executáveis

chmod 750 /opt/ia/data/iashell/*.sh

chmod 750 /opt/ia/data/iashell/*.py



---



## Solução de Problemas



### Erro: `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`



**Causa**: Python < 3.10 não suporta sintaxe `str | None`



**Solução**:

sed -i '1i from typing import Optional' /opt/ia/data/iashell/prompt.py

sed -i 's/str | None/Optional[str]/g' /opt/ia/data/iashell/prompt.py



### PDF sem texto extraível



**Causa**: PDF pode ser baseado em imagens ou protegido



**Solução**: Instalar pdfplumber para melhor extração

pip install pdfplumber



### Erro de permissão



**Causa**: Diretórios sem permissão de escrita



**Solução**:

# Verificar dono atual

ls -la /opt/ia/data/iashell/base/



# Ajustar dono (substitua $USER pelo seu usuário)

sudo chown -R $USER:$USER /opt/ia/data/iashell/base



# Aplicar permissões corretas

find /opt/ia/data/iashell/base -type d -exec chmod 750 {} \;

find /opt/ia/data/iashell/base -type f -exec chmod 640 {} \;

chmod 750 /opt/ia/data/iashell/base/tmp/.raw

chmod 750 /opt/ia/data/iashell/base/knowledge/.raw



### Arquivo não aparece no catálogo



**Causa**: Arquivo pode estar em diretório não monitorado



**Solução**:

# Mover para diretório correto

mv /caminho/arquivo.pdf /opt/ia/data/iashell/base/knowledge/



# Forçar sincronização manual

:add /opt/ia/data/iashell/base/knowledge/arquivo.pdf



---



## Manutenção



### Atualizar código



cd /opt/ia/data/iashell

git pull

pip install -r requirements.txt --upgrade



### Backup



cd /opt/ia/data

tar czf ia-backup-$(date +%Y%m%d-%H%M%S).tar.gz iashell/base/



### Restaurar backup



cd /opt/ia/data

tar xzf ia-backup-20250310-153000.tar.gz



### Reset completo (mantendo configurações)



# Backup primeiro!

cd /opt/ia/data/iashell

rm -rf base/*

mkdir -p base/profile base/tmp/.raw base/knowledge/.raw base/parsed

echo '[]' > base/document_catalog.json

touch base/chunks.jsonl

find base -type d -exec chmod 750 {} \;

find base -type f -exec chmod 640 {} \;



### Remoção completa



# Backup primeiro!

rm -rf /opt/ia/data/iashell



# Remover alias (editar arquivo)

vim ~/.bashrc  # ou /etc/profile.d/ia.sh



---



## Logs e Depuração



### Verificar logs de erro



# Executar com debug

python3 -m trace --trace /opt/ia/data/iashell/prompt.py 2>&1 | tee debug.log



# Verificar últimos erros

tail -f /var/log/syslog | grep ia



### Verificar integridade dos dados



# Listar documentos

python3 -c "from knowledge import list_documents; print(list_documents())"



# Verificar chunks

python3 -c "from knowledge import load_all_chunks; print(len(load_all_chunks()))"



---



## Contribuição



1. Fork o repositório

2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)

3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)

4. Push para a branch (`git push origin feature/nova-funcionalidade`)

5. Abra um Pull Request



### Padrões de código



- Seguir PEP 8

- Adicionar docstrings para funções públicas

- Atualizar README quando necessário

- Adicionar testes quando possível



---



## Licença



Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.



---



## Autor



Mantenedor - [@mantenedor](https://github.com/mantenedor)



---



## Agradecimentos



- OpenAI pela API

- Comunidade open source pelas bibliotecas utilizadas

- Contribuidores do projeto



---



## Changelog



### v1.0.0 (2024-03-10)

- Suporte inicial a PDF, TXT, CSV, Excel, Imagens

- RAG com chunks e busca por keywords

- Memória persistente

- Execução de comandos shell



### v1.1.0 (2024-03-10)

- Suporte a HTML com BeautifulSoup

- Diagnóstico de documentos

- Melhorias na extração de PDF com pdfplumber

- Permissões corrigidas



---



**Nota**: Este assistente foi projetado para ambientes Linux/Unix. Adaptações podem ser necessárias para outros sistemas operacionais.
