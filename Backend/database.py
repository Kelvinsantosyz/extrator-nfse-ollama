import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
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
        print("Erro: Credenciais do banco de dados não foram definidas no arquivo .env")
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
    """Cria a tabela 'notas_fiscais' e adiciona novas colunas se necessário."""
    try:
        cursor = conn.cursor()
        # Query principal para criar a tabela com todos os campos, incluindo o novo 'valor_inss'
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
            valor_total_impostos DECIMAL(10, 2),
            valor_inss DECIMAL(10, 2),
            categoria VARCHAR(100)
        );
        """
        cursor.execute(create_table_query)
        
        # Bloco de verificação para garantir que as colunas existem em tabelas antigas
        cursor.execute("SHOW COLUMNS FROM notas_fiscais LIKE 'categoria'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE notas_fiscais ADD COLUMN categoria VARCHAR(100)")
            
        cursor.execute("SHOW COLUMNS FROM notas_fiscais LIKE 'valor_inss'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE notas_fiscais ADD COLUMN valor_inss DECIMAL(10, 2)")
            
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Erro ao criar/alterar a tabela: {e}")

def get_all_hashes(conn):
    """Busca todos os hashes de arquivos já processados no banco de dados."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT hash FROM notas_fiscais")
        return {row[0] for row in cursor.fetchall()}
    except mysql.connector.Error as e:
        print(f"Erro ao buscar hashes: {e}")
        return set()

def insert_record(conn, data_dict, headers):
    """Insere ou atualiza um registro na tabela 'notas_fiscais'."""
    try:
        cursor = conn.cursor()
        cols_to_insert = [h for h in headers if h in data_dict and data_dict.get(h) is not None]
        
        cols_str = ', '.join([f"`{h}`" for h in cols_to_insert])
        placeholders = ', '.join(['%s'] * len(cols_to_insert))
        updates = ', '.join([f"`{h}`=VALUES(`{h}`)" for h in cols_to_insert if h != 'hash'])
        
        sql = f"INSERT INTO notas_fiscais ({cols_str}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"
        
        values = tuple([data_dict.get(h) for h in cols_to_insert])
        
        cursor.execute(sql, values)
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Erro ao inserir registro: {e}")

def fetch_all_data_as_dataframe(conn):
    """Busca todos os dados da tabela e retorna como um DataFrame do Pandas."""
    try:
        return pd.read_sql("SELECT * FROM notas_fiscais ORDER BY data_hora_emissao DESC", conn)
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return pd.DataFrame()

def search_data_as_dataframe(conn, search_term, search_field):
    """
    Busca dados na tabela filtrando por um termo em um campo específico.
    É mais eficiente do que filtrar no app.
    """
    if not search_term or not search_field:
        return fetch_all_data_as_dataframe(conn)
        
    # Mapeia os campos da interface para as colunas do banco
    valid_fields = {
        "CNPJ do Prestador": "prestador_cnpj",
        "Razão Social": "prestador_razao_social",
        "Número da Nota": "numero_nota"
    }
    
    column_to_search = valid_fields.get(search_field)
    
    if not column_to_search:
        return pd.DataFrame() # Retorna vazio se o campo for inválido

    try:
        query = f"SELECT * FROM notas_fiscais WHERE {column_to_search} LIKE %s ORDER BY data_hora_emissao DESC"
        like_term = f"%{search_term}%"
        df = pd.read_sql(query, conn, params=(like_term,))
        return df
    except Exception as e:
        print(f"Erro ao buscar dados filtrados: {e}")
        return pd.DataFrame()

