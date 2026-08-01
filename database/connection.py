# ==============================================================================
# PROJETO: MyGym
# MÓDULO: database/connection.py
# DATA DE CRIAÇÃO: 31/07/26
# TÍTULO: Conexão com o Banco de Dados
# FUNÇÃO: Ler as credenciais de segurança do arquivo .env e fornecer uma conexão 
#         padronizada com o banco de dados MySQL para o motor principal.
#
# HISTÓRICO DE ALTERAÇÕES:
# 31/07/26: Criação do módulo de conexão isolada usando variáveis de ambiente.
# 31/07/26: Suporte inteligente a socket local e fallback TCP/IP para estabilidade total.
# ==============================================================================

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env localizado na raiz do projeto para a memória
load_dotenv()

def get_connection():
    """
    Estabelece e retorna uma conexão com o banco de dados MySQL utilizando 
    o socket local do Linux ou fallback por TCP/IP com base no .env.
    
    Retorna:
        connection: Objeto de conexão ativa do MySQL se bem-sucedido.
        None: Em caso de falha na conexão.
    """
    # 1. Tenta conectar via socket local do Linux (mais seguro e direto no Ubuntu)
    if os.path.exists('/var/run/mysqld/mysqld.sock'):
        try:
            connection = mysql.connector.connect(
                unix_socket='/var/run/mysqld/mysqld.sock',
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
            )
            if connection.is_connected():
                return connection
        except Error:
            pass  # Se falhar o socket, prossegue para a tentativa TCP/IP

    # 2. Tenta conectar via TCP/IP padrão (localhost / 127.0.0.1)
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        if connection.is_connected():
            return connection
            
    except Error as e:
        print(f"Erro de conexão com o banco de dados MyGym: {e}")
        return None