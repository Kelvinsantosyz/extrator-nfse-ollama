import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

# ==============================================================================
# CONFIGURAÇÕES DO BANCO DE DADOS (LIDAS DO ARQUIVO .ENV)
# ==============================================================================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# ==============================================================================
# FUNÇÕES DE INTERAÇÃO COM O BANCO DE DADOS
# ==============================================================================

def create_connection():
    """Cria e retorna uma conexão com o banco de dados MySQL."""
    if not all([DB_CONFIG['user'], DB_CONFIG['password'], DB_CONFIG['database']]):
        print("Erro: As credenciais do banco de dados não foram definidas no arquivo .env")
        return None
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        conn.database = DB_CONFIG['database']
        return conn
    except mysql.connector.Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

def create_table_if_not_exists(conn):
    """Cria a tabela 'notas_fiscais' se ela ainda não existir."""
    try:
        cursor = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS notas_fiscais (
            hash VARCHAR(32) PRIMARY KEY,
            arquivo VARCHAR(255),
            data_processamento DATETIME,
            numero_nota VARCHAR(50),
            data_hora_emissao DATETIME NULL,
            codigo_verificacao VARCHAR(50),
            prestador_cnpj VARCHAR(20),
            prestador_razao_social VARCHAR(255),
            prestador_inscricao_municipal VARCHAR(50),
            prestador_logradouro TEXT,
            prestador_bairro VARCHAR(100),
            prestador_cep VARCHAR(10),
            prestador_cidade VARCHAR(100),
            prestador_uf VARCHAR(2),
            tomador_cpf VARCHAR(20),
            tomador_razao_social VARCHAR(255),
            tomador_email VARCHAR(255),
            tomador_logradouro TEXT,
            tomador_bairro VARCHAR(100),
            tomador_cep VARCHAR(10),
            tomador_cidade VARCHAR(100),
            tomador_uf VARCHAR(2),
            discriminacao_servicos TEXT,
            servico_codigo VARCHAR(50),
            servico_descricao TEXT,
            valor_total_servico DECIMAL(10, 2),
            base_calculo DECIMAL(10, 2),
            aliquota DECIMAL(5, 4),
            valor_iss DECIMAL(10, 2),
            valor_total_impostos DECIMAL(10, 2)
        );
        """
        cursor.execute(create_table_query)
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Erro ao criar a tabela: {e}")

def get_all_hashes(conn):
    """Busca todos os hashes de arquivos já processados no banco de dados."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT hash FROM notas_fiscais")
        hashes = {row[0] for row in cursor.fetchall()}
        return hashes
    except mysql.connector.Error as e:
        print(f"Erro ao buscar hashes: {e}")
        return set()

def insert_record(conn, data_dict, headers):
    """Insere ou atualiza um registro na tabela 'notas_fiscais'."""
    try:
        cursor = conn.cursor()
        cols = ', '.join([f"`{h}`" for h in headers if h in data_dict and data_dict[h] is not None])
        placeholders = ', '.join(['%s'] * len([h for h in headers if h in data_dict and data_dict[h] is not None]))
        updates = ', '.join([f"`{h}`=%s" for h in headers if h in data_dict and h != 'hash' and data_dict[h] is not None])
        
        sql = f"INSERT INTO notas_fiscais ({cols}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"
        
        values = [data_dict.get(h) for h in headers if h in data_dict and data_dict[h] is not None]
        update_values = [data_dict.get(h) for h in headers if h in data_dict and h != 'hash' and data_dict[h] is not None]
        
        cursor.execute(sql, tuple(values + update_values))
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Erro ao inserir registro: {e}")

def fetch_all_data_as_dataframe(conn):
    """Busca todos os dados da tabela e retorna como um DataFrame do Pandas."""
    try:
        query = "SELECT * FROM notas_fiscais"
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        print(f"Erro ao buscar dados como DataFrame: {e}")
        return pd.DataFrame()

