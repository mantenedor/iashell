# IA Local Assistente Técnico

Assistente de linha de comando com memória persistente, RAG local e execução de shell, projetado para operar diretamente no terminal.

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
├── setup.sh
├── .env.example
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

### Método Rápido (Recomendado)

curl -fsSL https://raw.githubusercontent.com/mantenedor/iashell/main/setup.sh | bash -s -- -i

Este comando:
- Instala tudo em ~/iashell (sem precisar de sudo)
- Cria a estrutura de diretórios automaticamente
- Instala todas as dependências Python
- Configura o alias 'ia' no seu shell
- Cria o arquivo conf/.env de configuração

### Desinstalação

# Remover o ambiente (mantém caches Python)
curl -fsSL https://raw.githubusercontent.com/mantenedor/iashell/main/setup.sh | bash -s -- -d

# Remover completamente (inclui caches Python)
curl -fsSL https://raw.githubusercontent.com/mantenedor/iashell/main/setup.sh | bash -s -- -d
# Será solicitada a confirmação com a palavra "DESTRUIR"

### Configuração da Chave OpenAI

Após a instalação, configure sua chave da OpenAI:

vim ~/iashell/conf/.env

Adicione sua chave no formato:
OPENAI_API_KEY=sk-...

Para obter uma chave: https://platform.openai.com/api-keys

### Pré-requisitos

- Python 3.8+ e pip
- Git
- Acesso à internet

### O que o script faz

1. Verifica os pré-requisitos (Python, pip, git)
2. Clona o repositório para ~/iashell
3. Instala dependências Python
4. Cria estrutura de diretórios (base/, tmp/, knowledge/, etc.)
5. Cria diretório conf/ e arquivo .env a partir do template
6. Configura alias 'ia' no shell (detecta bash/zsh automaticamente)
7. Ajusta permissões (755 para diretórios, 644 para arquivos)

---

## Execução

Iniciar o assistente:

ia

Prompt de exemplo:
IA pronta (!comando para shell, :add <arquivo> para indexar, :docs para listar documentos, :diagnose <doc_id> para diagnóstico, q ou quit para sair)

> 

---

## Comandos do Prompt

Comando: !<comando>
Descrição: Executa comando shell
Exemplo: !ls -la

Comando: :add <caminho>
Descrição: Indexa documento
Exemplo: :add /tmp/manual.pdf

Comando: :docs
Descrição: Lista documentos indexados
Exemplo: :docs

Comando: :diagnose <doc_id>
Descrição: Diagnostica documento
Exemplo: :diagnose manual-abc123

Comando: q ou quit
Descrição: Sai do assistente
Exemplo: q

### Exemplos de uso:

# Executar comando e analisar saída
> !df -h
--- saída do comando ---
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda3        98G   45G   53G  46% /
--- fim ---

Pressione ENTER para enviar à IA ou Ctrl+C para cancelar:

# Indexar documento
> :add ~/documentos/manual.pdf
Ingerindo /home/usuario/documentos/manual.pdf...
Documento indexado: manual-abc123 (pdf)
Chunks gerados: 25
Resumo: Manual de instalação versão 2.1...

# Listar documentos
> :docs
Documentos disponíveis (1):
- doc_id: manual-abc123
  nome: manual.pdf
  tipo: pdf
  origem: manual
  tamanho_bytes: 4995295
  chunks: 25
  resumo: Manual de instalação versão 2.1...

# Diagnosticar documento
> :diagnose manual-abc123

# Perguntar sobre documento
> do que se trata esse arquivo?

---

## Indexação automática

Arquivos colocados nos diretórios monitorados são detectados automaticamente:

- ~/iashell/base/tmp/ -> origem 'tmp' (arquivos temporários)
- ~/iashell/base/knowledge/ -> origem 'knowledge' (base de conhecimento)

A indexação é incremental:
- arquivos novos -> indexados
- arquivos alterados -> reindexados
- arquivos iguais -> ignorados

Para adicionar arquivos manualmente:
cp documento.pdf ~/iashell/base/knowledge/
# O sistema detectará automaticamente na próxima iteração

---

## Formatos suportados

Tipo: PDF
Extensões: .pdf
Processamento: Extração com pdfplumber (fallback PyPDF2)

Tipo: HTML
Extensões: .htm, .html
Processamento: Parse com BeautifulSoup + conversão para Markdown

Tipo: Texto
Extensões: .txt, .md, .log, .json, .yaml, .yml, .ini, .cfg
Processamento: Leitura direta

Tipo: CSV/TSV
Extensões: .csv, .tsv
Processamento: Parse com detecção de delimitador

Tipo: Planilhas
Extensões: .xlsx, .xlsm
Processamento: Leitura com openpyxl

Tipo: Imagens
Extensões: .png, .jpg, .jpeg, .webp, .bmp, .gif
Processamento: Extração de metadados + sidecar files

---

## Funcionamento do RAG

1. Ingestão: arquivo é copiado para .raw/
2. Parsing: conteúdo é extraído conforme o tipo
3. Chunking: texto é dividido em chunks de ~1800 tokens com sobreposição
4. Indexação: chunks são salvos com metadados e keywords
5. Busca: consultas buscam chunks relevantes por similaridade de termos
6. Contexto: chunks relevantes são enviados ao modelo junto com a pergunta

---

## Diagnóstico

O comando ':diagnose <doc_id>' fornece informações detalhadas:

============================================================
DIAGNÓSTICO DO DOCUMENTO: manual-abc123
============================================================

📋 METADADOS:
  Nome: manual.pdf
  Tipo: pdf
  Tamanho: 4995295 bytes
  Chunks: 25
  Status: parsed
  Resumo: Manual de instalação versão 2.1...

📄 ARQUIVO RAW: /home/usuario/iashell/base/knowledge/.raw/manual-abc123.pdf
  Tamanho: 4995295 bytes

📄 ARQUIVO PARSED: /home/usuario/iashell/base/parsed/manual-abc123.json
  Tamanho: 154320 bytes
  Páginas: 25
  Página 1 (primeiras 200 chars): # Manual de Instalação...

🔍 CHUNKS: 25 encontrados
  Chunks com conteúdo real: 25

---

## Memória Persistente

Localização: ~/iashell/base/profile/

Arquivos:
- base_memory.json -> memória base imutável
- overlay_memory.json -> ajustes incrementais
- history.jsonl -> histórico de conversas
- .prompt_history -> histórico de comandos (readline)

A memória pode ser editada manualmente para ajustar comportamento.

Exemplo de base_memory.json:
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

- Comandos shell não são executados automaticamente
- A saída é mostrada antes de ser enviada ao modelo
- Confirmação explícita necessária para cada comando
- Documentos são armazenados localmente
- API key da OpenAI armazenada apenas no .env (não versionado)
- Permissões restritivas nos diretórios (750/640)

### Permissões recomendadas:

# Diretórios (acesso apenas para o dono e grupo)
find ~/iashell/base -type d -exec chmod 750 {} \;

# Arquivos (leitura/escrita apenas para o dono)
find ~/iashell/base -type f -exec chmod 640 {} \;

# Scripts executáveis
chmod 750 ~/iashell/*.sh
chmod 750 ~/iashell/*.py

---

## Solução de Problemas

### Erro: TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'

Causa: Python < 3.10 não suporta sintaxe 'str | None'

Solução:
sed -i '1i from typing import Optional' ~/iashell/prompt.py
sed -i 's/str | None/Optional[str]/g' ~/iashell/prompt.py

### PDF sem texto extraível

Causa: PDF pode ser baseado em imagens ou protegido

Solução: Instalar pdfplumber para melhor extração
pip install pdfplumber

### Erro de permissão

Causa: Diretórios sem permissão de escrita

Solução:
# Verificar dono atual
ls -la ~/iashell/base/

# Aplicar permissões corretas
find ~/iashell/base -type d -exec chmod 750 {} \;
find ~/iashell/base -type f -exec chmod 640 {} \;

### Arquivo não aparece no catálogo

Causa: Arquivo pode estar em diretório não monitorado

Solução:
# Mover para diretório correto
mv /caminho/arquivo.pdf ~/iashell/base/knowledge/

# Forçar sincronização manual
:add ~/iashell/base/knowledge/arquivo.pdf

### Erro 401 - Invalid API Key

Causa: Chave da OpenAI inválida ou expirada

Solução:
1. Acesse https://platform.openai.com/api-keys
2. Gere uma nova chave
3. Atualize em ~/iashell/conf/.env

---

## Manutenção

### Atualizar código

cd ~/iashell
git pull
pip install -r requirements.txt --upgrade

### Backup

cd ~
tar czf ia-backup-$(date +%Y%m%d-%H%M%S).tar.gz iashell/base/

### Restaurar backup

cd ~
tar xzf ia-backup-20250310-153000.tar.gz

### Reset completo (mantendo configurações)

# Backup primeiro!
cd ~/iashell
rm -rf base/*
mkdir -p base/profile base/tmp/.raw base/knowledge/.raw base/parsed
echo '[]' > base/document_catalog.json
touch base/chunks.jsonl
find base -type d -exec chmod 750 {} \;
find base -type f -exec chmod 640 {} \;

### Remoção completa

# Backup primeiro!
rm -rf ~/iashell

# Remover alias (editar arquivo)
vim ~/.bashrc

---

## Logs e Depuração

### Verificar logs de erro

# Executar com debug
python3 -m trace --trace ~/iashell/prompt.py 2>&1 | tee debug.log

### Verificar integridade dos dados

# Listar documentos
python3 -c "from knowledge import list_documents; print(list_documents())"

# Verificar chunks
python3 -c "from knowledge import load_all_chunks; print(len(load_all_chunks()))"

---

## Contribuição

1. Fork o repositório
2. Crie uma branch (git checkout -b feature/nova-funcionalidade)
3. Commit suas mudanças (git commit -am 'Adiciona nova funcionalidade')
4. Push para a branch (git push origin feature/nova-funcionalidade)
5. Abra um Pull Request

### Padrões de código

- Seguir PEP 8
- Adicionar docstrings para funções públicas
- Atualizar README quando necessário

---

## Licença

Este projeto está licenciado sob a Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).

### Você tem permissão para:

- Compartilhar - copiar e redistribuir o material em qualquer suporte ou formato
- Adaptar - remixar, transformar, e criar a partir do material

### Sob as seguintes condições:

- Atribuição - Você deve dar o crédito apropriado, prover um link para a licença e indicar se mudanças foram feitas.
- Não Comercial - Você não pode usar o material para fins comerciais.

### Restrições:

- Sem restrições adicionais - Você não pode aplicar termos jurídicos ou medidas tecnológicas que restrinjam legalmente outros de fazerem algo que a licença permita.

Veja o arquivo LICENSE para mais detalhes.

---

**Resumo**: Você pode usar, modificar e compartilhar este código livremente, desde que não seja para fins comerciais e que dê os devidos créditos ao autor original.

---

## Autor

Mantenedor - @mantenedor

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
- Instalação automatizada com setup.sh
- Correção de permissões e paths

---

**Nota**: Este assistente foi projetado para ambientes Linux/Unix. Adaptações podem ser necessárias para outros sistemas operacionais.
EOF
