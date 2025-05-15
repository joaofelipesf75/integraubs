#!/bin/bash

# Script de inicialização para o Render
echo "Configurando o ambiente Sistema Integra UBS..."

# Verificar variáveis de ambiente
if [ -z "$DATABASE_URL" ]; then
    echo "AVISO: DATABASE_URL não encontrada. Usando SQLite (não recomendado para produção)."
else
    echo "Usando PostgreSQL para banco de dados."
fi

# Executar o db_scripts para configurar tudo automaticamente
echo "Configurando banco de dados..."
python db_scripts.py

# Verificar se a configuração foi bem-sucedida
if [ $? -ne 0 ]; then
    echo "ERRO: Falha na configuração do banco de dados."
    echo "Tentando verificar a conexão..."
    python db_scripts.py check_connection
    exit 1
fi

# Iniciar o aplicativo
echo "Iniciando o aplicativo Sistema Integra UBS..."
exec gunicorn --bind 0.0.0.0:$PORT --workers=2 --threads=4 main:app