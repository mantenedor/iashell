#!/bin/bash
# IA Shell Assistant - Script de instalação e desinstalação
# Repositório: https://github.com/mantenedor/iashell.git

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações - Instala no home do usuário
INSTALL_DIR="$HOME/iashell"
REPO_URL="https://github.com/mantenedor/iashell.git"
PYTHON_CMD="python3"
PIP_CMD="pip3"

# Função para exibir ajuda
show_help() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                             ║${NC}"
    echo -e "${BLUE}║${NC}         🚀  IA SHELL ASSISTANT - TERMINAL AI  🚀          ${BLUE}║${NC}"
    echo -e "${BLUE}║                                                             ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}DESCRIÇÃO:${NC}"
    echo "  Assistente de linha de comando com memória persistente, RAG local"
    echo "  e execução de shell, projetado para operar diretamente no terminal."
    echo ""
    echo -e "${YELLOW}FUNCIONALIDADES:${NC}"
    echo "  • Memória de contexto persistente"
    echo "  • Indexação automática de documentos (PDF, HTML, TXT, CSV, Excel, Imagens)"
    echo "  • Consulta a documentação local antes de responder"
    echo "  • Execução de comandos shell com confirmação"
    echo "  • RAG (Retrieval-Augmented Generation) com chunks inteligentes"
    echo ""
    echo -e "${YELLOW}REPOSITÓRIO:${NC}"
    echo "  $REPO_URL"
    echo ""
    echo -e "${YELLOW}USO:${NC}"
    echo "  $0 [-i] [-d]"
    echo ""
    echo -e "${YELLOW}OPÇÕES:${NC}"
    echo -e "  ${GREEN}-i${NC}    Instala o assistente no sistema"
    echo -e "         • Cria diretórios em $INSTALL_DIR"
    echo -e "         • Instala dependências Python"
    echo -e "         • Configura alias 'ia' no ~/.bashrc"
    echo -e "         • Ajusta permissões (755 para diretórios, 644 para arquivos)"
    echo ""
    echo -e "  ${RED}-d${NC}    Remove completamente o ambiente"
    echo -e "         • Remove alias do ~/.bashrc"
    echo -e "         • Remove diretório $INSTALL_DIR"
    echo -e "         • Pergunta se deseja limpar caches Python"
    echo ""
    echo -e "  ${YELLOW}sem parâmetros${NC}  Exibe esta mensagem de ajuda"
    echo ""
    echo -e "${YELLOW}EXEMPLOS:${NC}"
    echo "  curl -fsSL $REPO_URL/raw/main/setup.sh | bash -s -- -i    # Instalar"
    echo "  curl -fsSL $REPO_URL/raw/main/setup.sh | bash -s -- -d    # Destruir"
    echo ""
    echo -e "${YELLOW}APÓS A INSTALAÇÃO:${NC}"
    echo "  1. Recarregue seu bashrc: source ~/.bashrc"
    echo "  2. Configure sua chave OpenAI: vim $INSTALL_DIR/conf/.env"
    echo "  3. Execute: ia"
    echo ""
}

# Função de instalação
install() {
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║      INICIANDO INSTALAÇÃO...              ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    echo ""

    # 1. Verificar pré-requisitos
    echo -e "${BLUE}[1/7]${NC} Verificando pré-requisitos..."
    
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo -e "${RED}❌ Python3 não encontrado. Instale o Python 3.8+ primeiro.${NC}"
        exit 1
    fi
    echo -e "  ✅ Python3 encontrado: $($PYTHON_CMD --version)"
    
    if ! command -v $PIP_CMD &> /dev/null; then
        echo -e "${RED}❌ Pip3 não encontrado. Instale o python3-pip primeiro.${NC}"
        exit 1
    fi
    echo -e "  ✅ Pip3 encontrado"
    
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git não encontrado. Instale o git primeiro.${NC}"
        exit 1
    fi
    echo -e "  ✅ Git encontrado: $(git --version)"

    # 2. Clonar repositório
    echo -e "${BLUE}[2/7]${NC} Clonando repositório..."
    
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "  ⚠️  Diretório $INSTALL_DIR já existe. Atualizando..."
        cd $INSTALL_DIR
        git pull
    else
        git clone $REPO_URL $INSTALL_DIR
        cd $INSTALL_DIR
    fi
    echo -e "  ✅ Repositório clonado em $INSTALL_DIR"

    # 3. Instalar dependências
    echo -e "${BLUE}[3/7]${NC} Instalando dependências Python..."
    $PIP_CMD install --upgrade pip > /dev/null 2>&1
    $PIP_CMD install -r requirements.txt
    echo -e "  ✅ Dependências instaladas"

    # 4. Criar estrutura de diretórios
    echo -e "${BLUE}[4/7]${NC} Criando estrutura de diretórios..."
    mkdir -p base/profile
    mkdir -p base/tmp/.raw
    mkdir -p base/knowledge/.raw
    mkdir -p base/parsed
    echo '[]' > base/document_catalog.json
    touch base/chunks.jsonl
    echo -e "  ✅ Estrutura criada"

    # 5. Configurar permissões (no home do usuário)
    echo -e "${BLUE}[5/7]${NC} Ajustando permissões..."
    find base -type d -exec chmod 755 {} \;
    find base -type f -exec chmod 644 {} \;
    chmod 755 *.py *.sh
    echo -e "  ✅ Permissões configuradas (755/644)"

    # 6. Configurar .env
    echo -e "${BLUE}[6/7]${NC} Configurando ambiente..."
    mkdir -p conf
    if [ ! -f "conf/.env" ]; then
        if [ -f "conf/.env.example" ]; then
            cp conf/.env.example conf/.env
            echo -e "  ⚠️  Arquivo conf/.env criado a partir do exemplo"
            echo -e "  ⚠️  Edite-o para adicionar sua OPENAI_API_KEY"
        else
            echo -e "  ⚠️  Arquivo .env.example não encontrado"
        fi
    else
        echo -e "  ✅ Arquivo conf/.env já existe"
    fi

    # 7. Configurar alias
    echo -e "${BLUE}[7/7]${NC} Configurando alias 'ia'..."
    ALIAS_COMMAND="alias ia='$INSTALL_DIR/run-prompt.sh'"
    
    # Verifica qual shell está sendo usado
    SHELL_CONFIG="$HOME/.bashrc"
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        SHELL_CONFIG="$HOME/.bash_profile"
    fi
    
    if ! grep -q "alias ia=" "$SHELL_CONFIG"; then
        echo "$ALIAS_COMMAND" >> "$SHELL_CONFIG"
        echo -e "  ✅ Alias adicionado ao $SHELL_CONFIG"
    else
        echo -e "  ⚠️  Alias 'ia' já existe em $SHELL_CONFIG"
    fi

    # Concluído
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║      INSTALAÇÃO CONCLUÍDA COM SUCESSO!    ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}📝 PRÓXIMOS PASSOS:${NC}"
    echo "  1. Recarregue seu shell: source $SHELL_CONFIG"
    echo "  2. Configure sua chave da OpenAI: vim $INSTALL_DIR/conf/.env"
    echo "  3. Execute o assistente: ia"
    echo ""
    echo -e "${BLUE}📚 Documentação: $INSTALL_DIR/README.md${NC}"
    echo -e "${BLUE}📂 Arquivos instalados em: $INSTALL_DIR${NC}"
}

# Função de destruição
destroy() {
    echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║      DESTRUINDO AMBIENTE...               ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
    echo ""

    # Confirmar destruição
    echo -e "${YELLOW}⚠️  ATENÇÃO: Isso removerá permanentemente:${NC}"
    echo "  • Diretório $INSTALL_DIR"
    echo "  • Alias do shell"
    echo "  • Caches Python (opcional)"
    echo ""
    read -p "Tem certeza? (digite 'DESTRUIR' para confirmar): " confirm
    if [ "$confirm" != "DESTRUIR" ]; then
        echo -e "${GREEN}❌ Operação cancelada.${NC}"
        exit 0
    fi

    # 1. Remover alias
    echo -e "${BLUE}[1/3]${NC} Removendo alias do shell..."
    
    SHELL_CONFIG="$HOME/.bashrc"
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        SHELL_CONFIG="$HOME/.bash_profile"
    fi
    
    # Faz backup do arquivo antes de modificar
    cp "$SHELL_CONFIG" "$SHELL_CONFIG.bak.$(date +%Y%m%d_%H%M%S)"
    
    # Remove a linha do alias
    sed -i '/alias ia=\/home\/.*\/iashell\/run-prompt.sh/d' "$SHELL_CONFIG"
    echo -e "  ✅ Alias removido de $SHELL_CONFIG"
    echo -e "  💾 Backup criado: $SHELL_CONFIG.bak.*"

    # 2. Remover diretório de instalação
    echo -e "${BLUE}[2/3]${NC} Removendo diretório de instalação..."
    if [ -d "$INSTALL_DIR" ]; then
        rm -rf "$INSTALL_DIR"
        echo -e "  ✅ Diretório $INSTALL_DIR removido"
    else
        echo -e "  ⚠️  Diretório $INSTALL_DIR não encontrado"
    fi

    # 3. Perguntar sobre caches Python
    echo -e "${BLUE}[3/3]${NC} Limpando caches Python..."
    read -p "Deseja limpar os caches do Python? (s/N): " clean_cache
    if [[ "$clean_cache" =~ ^[Ss]$ ]]; then
        rm -rf ~/.cache/pip 2>/dev/null || true
        echo -e "  ✅ Caches Python limpos"
    else
        echo -e "  ⚠️  Caches Python mantidos"
    fi

    # Concluído
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║      AMBIENTE DESTRUÍDO COM SUCESSO!      ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}ℹ️  Recarregue seu shell: source $SHELL_CONFIG${NC}"
    echo -e "${YELLOW}ℹ️  Backup do shell config salvo em: $SHELL_CONFIG.bak.*${NC}"
}

# Main - processar argumentos
case "$1" in
    -i)
        install
        ;;
    -d)
        destroy
        ;;
    "")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Opção inválida: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
