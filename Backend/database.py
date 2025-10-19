import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# CONFIGURAÇÕES DA BASE DE DADOS
# ==============================================================================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# ==============================================================================
# FUNÇÕES DE CONEXÃO E TABELAS
# ==============================================================================
def create_connection():
    """Cria e retorna uma conexão com a base de dados MySQL."""
    if not all([DB_CONFIG['user'], DB_CONFIG['password'], DB_CONFIG['database']]):
        print("Erro: Credenciais da base de dados não definidas no ficheiro .env")
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

def create_notas_fiscais_table_if_not_exists(conn):
    """Cria a tabela de notas fiscais se ela não existir."""
    try:
        cursor = conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS notas_fiscais (
            hash VARCHAR(32) PRIMARY KEY, arquivo VARCHAR(255), data_processamento DATETIME,
            numero_nota VARCHAR(50), data_hora_emissao DATETIME NULL, codigo_verificacao VARCHAR(50),
            prestador_cnpj VARCHAR(20), prestador_razao_social VARCHAR(255), prestador_inscricao_municipal VARCHAR(50),
            prestador_logradouro TEXT, prestador_bairro VARCHAR(100), prestador_cep VARCHAR(10),
            prestador_cidade VARCHAR(100), prestador_uf VARCHAR(2),
            tomador_cpf VARCHAR(20), tomador_razao_social VARCHAR(255), tomador_email VARCHAR(255),
            tomador_logradouro TEXT, tomador_bairro VARCHAR(100), tomador_cep VARCHAR(10),
            tomador_cidade VARCHAR(100), tomador_uf VARCHAR(2),
            discriminacao_servicos TEXT, servico_codigo VARCHAR(50), servico_descricao TEXT,
            valor_total_servico DECIMAL(10, 2), base_calculo DECIMAL(10, 2), aliquota DECIMAL(5, 4),
            valor_iss DECIMAL(10, 2), valor_total_impostos DECIMAL(10, 2), categoria VARCHAR(100)
        );
        """
        cursor.execute(create_table_query)
        cursor.execute("SHOW COLUMNS FROM notas_fiscais LIKE 'categoria'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE notas_fiscais ADD COLUMN categoria VARCHAR(100)")
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Erro ao criar/alterar a tabela notas_fiscais: {e}")

def create_users_table_if_not_exists(conn):
    """Cria a tabela de utilizadores com a coluna de alteração de palavra-passe."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(50) PRIMARY KEY,
                email VARCHAR(255) UNIQUE,
                name VARCHAR(100),
                password VARCHAR(255),
                is_admin BOOLEAN DEFAULT FALSE,
                force_password_change BOOLEAN DEFAULT TRUE
            );
        """)
        cursor.execute("SHOW COLUMNS FROM users LIKE 'force_password_change'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN force_password_change BOOLEAN DEFAULT TRUE")
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Erro ao criar a tabela de utilizadores: {e}")

# ==============================================================================
# FUNÇÕES CRUD PARA UTILIZADORES
# ==============================================================================
def fetch_all_users(conn):
    """Procura todos os utilizadores para o streamlit-authenticator."""
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username, email, name, password FROM users")
        users = cursor.fetchall()
        
        credentials = {"usernames": {}}
        for user in users:
            credentials["usernames"][user["username"]] = {
                "email": user["email"],
                "name": user["name"],
                "password": user["password"],
            }
        return credentials
    except mysql.connector.Error as e:
        print(f"Erro ao procurar utilizadores: {e}")
        return None

def fetch_all_users_for_admin_view(conn):
    """Procura todos os utilizadores para exibição no painel de admin (sem palavras-passe)."""
    try:
        return pd.read_sql("SELECT username, name, email, is_admin FROM users", conn)
    except Exception as e:
        print(f"Erro ao procurar dados de utilizadores para admin: {e}")
        return pd.DataFrame()

def add_user(conn, username, email, name, hashed_password, is_admin=False):
    """Adiciona um novo utilizador, que por defeito precisará de alterar a palavra-passe."""
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO users (username, email, name, password, is_admin, force_password_change) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (username, email, name, hashed_password, is_admin, True)
        cursor.execute(sql, values)
        conn.commit()
        return True
    except mysql.connector.Error as e:
        print(f"Erro ao adicionar utilizador: {e}")
        return False

def get_user_details(conn, username):
    """Procura os detalhes de um utilizador específico."""
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username, name, email, is_admin, force_password_change FROM users WHERE username = %s", (username,))
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Erro ao procurar detalhes do utilizador: {e}")
        return None

def set_password_change_flag(conn, username, force_change: bool):
    """Define o estado da flag de alteração forçada de palavra-passe."""
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET force_password_change = %s WHERE username = %s", (force_change, username))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        print(f"Erro ao definir a flag de alteração de palavra-passe: {e}")
        return False
        
def delete_user(conn, username):
    """Elimina um utilizador da base de dados."""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        print(f"Erro ao eliminar utilizador: {e}")
        return False

def get_all_usernames(conn):
    """Retorna uma lista com o nome de todos os utilizadores."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users")
        return [item[0] for item in cursor.fetchall()]
    except mysql.connector.Error as e:
        print(f"Erro ao procurar nomes de utilizador: {e}")
        return []

def update_user_password(conn, username, new_hashed_password):
    """Atualiza a palavra-passe de um utilizador."""
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (new_hashed_password, username))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        print(f"Erro ao atualizar a palavra-passe: {e}")
        return False

# ==============================================================================
# FUNÇÕES DE MANIPULAÇÃO DE NOTAS FISCAIS (sem alterações)
# ==============================================================================
def get_all_hashes(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT hash FROM notas_fiscais")
        return {row[0] for row in cursor.fetchall()}
    except mysql.connector.Error as e:
        print(f"Erro ao procurar hashes: {e}")
        return set()

def insert_record(conn, data_dict, headers):
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
        print(f"Erro ao inserir registo: {e}")

def fetch_all_data_as_dataframe(conn):
    try:
        return pd.read_sql("SELECT * FROM notas_fiscais", conn)
    except Exception as e:
        print(f"Erro ao procurar dados: {e}")
        return pd.DataFrame()

def search_data_as_dataframe(conn, search_term, search_field):
    if not search_term:
        return fetch_all_data_as_dataframe(conn)
    field_map = {
        "CNPJ do Prestador": "prestador_cnpj",
        "Razão Social": "prestador_razao_social",
        "Número da Nota": "numero_nota"
    }
    column_to_search = field_map.get(search_field, "prestador_razao_social")
    try:
        query = f"SELECT * FROM notas_fiscais WHERE {column_to_search} LIKE %s"
        like_term = f"%{search_term}%"
        params = [like_term]
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        print(f"Erro ao procurar dados filtrados: {e}")
        return pd.DataFrame()

