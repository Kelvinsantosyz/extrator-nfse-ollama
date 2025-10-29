import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv
# NOVAS IMPORTAÇÕES para corrigir o UserWarning do Pandas
from sqlalchemy import create_engine, text
import traceback # Para depuração

# Carrega as variáveis de ambiente do ficheiro .env
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
# MOTOR SQLAlchemy (para Pandas)
# ==============================================================================
_engine = None

def get_sqlalchemy_engine():
    """Cria e retorna um motor SQLAlchemy para a conexão com a base de dados."""
    global _engine
    if _engine is None:
        if not all([DB_CONFIG['user'], DB_CONFIG['password'], DB_CONFIG['database'], DB_CONFIG['host']]):
            print("Erro: Credenciais da base de dados não definidas no .env para SQLAlchemy.")
            return None
        try:
            # pymysql é recomendado para SQLAlchemy com MySQL
            db_uri = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
            _engine = create_engine(db_uri)
            # Testa a conexão
            with _engine.connect() as connection:
                print("Conexão SQLAlchemy estabelecida com sucesso.")
        except ImportError:
             print("Erro: A biblioteca 'pymysql' não está instalada. Execute: pip install pymysql")
             return None
        except Exception as e:
            print(f"Erro ao criar o motor SQLAlchemy: {e}")
            _engine = None # Garante que não tentaremos usar um motor inválido
    return _engine

# ==============================================================================
# DEFINIÇÃO DOS CABEÇALHOS DA TABELA (para uso interno neste módulo)
# ==============================================================================
# CORREÇÃO: Definindo HEADERS_DB aqui para que as funções tenham acesso
HEADERS_DB = [
    'hash', 'arquivo', 'data_processamento',
    'ocr_numero', 'ocr_emissao_datahora', 'ocr_codigo_verificacao',
    'ocr_prestador_nome', 'ocr_prestador_cpf_cnpj', 'ocr_prestador_inscricao_municipal',
    'ocr_prestador_endereco', 'ocr_prestador_municipio', 'ocr_prestador_uf',
    'ocr_tomador_nome', 'ocr_tomador_cpf_cnpj', 'ocr_tomador_endereco',
    'ocr_tomador_inscricao_municipal', 'ocr_tomador_municipio', 'ocr_tomador_uf', 'ocr_tomador_email',
    'ocr_discriminacao', 'ocr_codigo_servico',
    'ocr_valor_total', 'ocr_valor_base_calculo', 'ocr_valor_aliquota', 'ocr_valor_iss',
    'ocr_valor_deducoes', 'ocr_valor_pis_pasep', 'ocr_valor_cofins', 'ocr_valor_csll',
    'ocr_valor_irrf', 'ocr_valor_inss', 'ocr_valor_credito',
    'ocr_valor_tributos_fonte', 'ocr_valor_tributos_fonte_percentual',
    'ocr_municipio_prestacao_servico', 'ocr_intermediario_nome', 'ocr_intermediario_cpf_cnpj',
    'ocr_outras_informacoes', 'ocr_numero_inscricao_obra', 'alogo_visivel',
    'categoria' # Adicionado 'categoria' se fizer parte do schema final
]


# ==============================================================================
# FUNÇÕES DE CONEXÃO E TABELAS (usando mysql.connector para DDL)
# ==============================================================================
def create_connection():
    """Cria e retorna uma conexão mysql.connector."""
    if not all([DB_CONFIG['user'], DB_CONFIG['password'], DB_CONFIG['database']]):
        print("Erro: Credenciais da base de dados não definidas no .env")
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
        print("Conexão mysql.connector estabelecida com sucesso.")
        return conn
    except mysql.connector.Error as e:
        print(f"Erro ao conectar ao MySQL via mysql.connector: {e}")
        return None

def _add_column_if_not_exists(cursor, table_name, column_name, column_definition):
    """Verifica se uma coluna existe e a adiciona caso contrário."""
    try:
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = '{DB_CONFIG['database']}'
            AND TABLE_NAME = '{table_name}'
            AND COLUMN_NAME = '{column_name}'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_definition}")
            print(f"Coluna '{column_name}' adicionada à tabela '{table_name}'.")
    except mysql.connector.Error as e:
        print(f"Erro ao verificar/adicionar coluna '{column_name}' em '{table_name}': {e}")


def create_notas_fiscais_table_if_not_exists(conn):
    """Cria a tabela de notas fiscais e adiciona novas colunas se necessário."""
    if not conn or not conn.is_connected():
        print("Erro: Conexão inválida para criar/alterar tabela notas_fiscais.")
        return
    try:
        cursor = conn.cursor()
        # Query inicial simplificada, colunas serão adicionadas/verificadas abaixo
        create_table_query = """
        CREATE TABLE IF NOT EXISTS notas_fiscais (
            hash VARCHAR(32) PRIMARY KEY,
            arquivo VARCHAR(255),
            data_processamento DATETIME
        );
        """
        cursor.execute(create_table_query)

        # Definições das colunas (tipo SQL)
        colunas_defs = {
            'ocr_numero': 'VARCHAR(50) NULL', 'ocr_emissao_datahora': 'DATETIME NULL', 'ocr_codigo_verificacao': 'VARCHAR(50) NULL',
            'ocr_prestador_nome': 'VARCHAR(255) NULL', 'ocr_prestador_cpf_cnpj': 'VARCHAR(20) NULL', 'ocr_prestador_inscricao_municipal': 'VARCHAR(50) NULL',
            'ocr_prestador_endereco': 'TEXT NULL', 'ocr_prestador_municipio': 'VARCHAR(100) NULL', 'ocr_prestador_uf': 'VARCHAR(2) NULL',
            'ocr_tomador_nome': 'VARCHAR(255) NULL', 'ocr_tomador_cpf_cnpj': 'VARCHAR(20) NULL', 'ocr_tomador_endereco': 'TEXT NULL',
            'ocr_tomador_inscricao_municipal': 'VARCHAR(50) NULL', 'ocr_tomador_municipio': 'VARCHAR(100) NULL', 'ocr_tomador_uf': 'VARCHAR(2) NULL', 'ocr_tomador_email': 'VARCHAR(255) NULL',
            'ocr_discriminacao': 'TEXT NULL', 'ocr_codigo_servico': 'VARCHAR(50) NULL',
            'ocr_valor_total': 'DECIMAL(15, 2) NULL', 'ocr_valor_base_calculo': 'DECIMAL(15, 2) NULL', 'ocr_valor_aliquota': 'DECIMAL(7, 4) NULL', 'ocr_valor_iss': 'DECIMAL(15, 2) NULL',
            'ocr_valor_deducoes': 'DECIMAL(15, 2) NULL', 'ocr_valor_pis_pasep': 'DECIMAL(15, 2) NULL', 'ocr_valor_cofins': 'DECIMAL(15, 2) NULL', 'ocr_valor_csll': 'DECIMAL(15, 2) NULL',
            'ocr_valor_irrf': 'DECIMAL(15, 2) NULL', 'ocr_valor_inss': 'DECIMAL(15, 2) NULL', 'ocr_valor_credito': 'DECIMAL(15, 2) NULL',
            'ocr_valor_tributos_fonte': 'DECIMAL(15, 2) NULL', 'ocr_valor_tributos_fonte_percentual': 'VARCHAR(10) NULL',
            'ocr_municipio_prestacao_servico': 'VARCHAR(100) NULL', 'ocr_intermediario_nome': 'VARCHAR(255) NULL', 'ocr_intermediario_cpf_cnpj': 'VARCHAR(20) NULL',
            'ocr_outras_informacoes': 'TEXT NULL', 'ocr_numero_inscricao_obra': 'VARCHAR(50) NULL', 'alogo_visivel': 'VARCHAR(10) NULL',
            'categoria': 'VARCHAR(100) NULL' # Inclui categoria
        }

        # Adiciona/Verifica todas as colunas definidas em HEADERS_DB (exceto as básicas)
        for col_name in HEADERS_DB:
             if col_name not in ['hash', 'arquivo', 'data_processamento']:
                 col_def = colunas_defs.get(col_name)
                 if col_def:
                     _add_column_if_not_exists(cursor, "notas_fiscais", col_name, col_def)
                 else:
                      print(f"AVISO: Definição SQL não encontrada para a coluna '{col_name}' em HEADERS_DB.")


        # Adiciona índices se não existirem (Opcional, mas recomendado)
        try: cursor.execute("CREATE INDEX idx_prestador_cnpj ON notas_fiscais (ocr_prestador_cpf_cnpj);")
        except mysql.connector.Error: pass # Ignora erro se índice já existir
        try: cursor.execute("CREATE INDEX idx_numero_nota ON notas_fiscais (ocr_numero);")
        except mysql.connector.Error: pass
        try: cursor.execute("CREATE INDEX idx_emissao_datahora ON notas_fiscais (ocr_emissao_datahora);")
        except mysql.connector.Error: pass

        conn.commit()
        print("Tabela 'notas_fiscais' verificada/atualizada com sucesso.")
    except mysql.connector.Error as e:
        print(f"Erro ao criar/alterar a tabela notas_fiscais: {e}")
        try:
            conn.rollback() # Tenta reverter alterações em caso de erro
        except Exception as rb_e:
            print(f"Erro durante o rollback: {rb_e}")


def create_users_table_if_not_exists(conn):
    """Cria a tabela de utilizadores se ela não existir."""
    if not conn or not conn.is_connected():
        print("Erro: Conexão inválida para criar/alterar tabela users.")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username VARCHAR(50) PRIMARY KEY, email VARCHAR(255) UNIQUE, name VARCHAR(100),
                password VARCHAR(255), is_admin BOOLEAN DEFAULT FALSE,
                force_password_change BOOLEAN DEFAULT TRUE
            );
        """)
        # Garante que a coluna existe
        _add_column_if_not_exists(cursor, "users", "force_password_change", "BOOLEAN DEFAULT TRUE")
        conn.commit()
        print("Tabela 'users' verificada/atualizada com sucesso.")
    except mysql.connector.Error as e:
        print(f"Erro ao criar/alterar a tabela de utilizadores: {e}")

# ==============================================================================
# FUNÇÕES CRUD PARA UTILIZADORES (usando mysql.connector)
# ==============================================================================
# ... (Funções add_user, delete_user, get_user_details, get_all_usernames,
#      update_user_password, check_force_password_change, set_password_change_flag
#      permanecem iguais) ...
def fetch_all_users(conn):
    """Busca todos os utilizadores para o streamlit-authenticator."""
    if not conn or not conn.is_connected(): return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username, email, name, password FROM users")
        users = cursor.fetchall()
        credentials = {"usernames": {}}
        for user in users:
            credentials["usernames"][user["username"]] = {
                "email": user["email"], "name": user["name"], "password": user["password"],
            }
        return credentials
    except mysql.connector.Error as e:
        print(f"Erro ao buscar utilizadores: {e}")
        return None

def add_user(conn, username, email, name, hashed_password, is_admin=False, force_change=True):
    """Adiciona um novo utilizador à base de dados."""
    if not conn or not conn.is_connected(): return False
    try:
        cursor = conn.cursor()
        sql = "INSERT INTO users (username, email, name, password, is_admin, force_password_change) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (username, email, name, hashed_password, is_admin, force_change)
        cursor.execute(sql, values)
        conn.commit()
        return True
    except mysql.connector.Error as e:
        print(f"Erro ao adicionar utilizador: {e}")
        return False

def delete_user(conn, username):
    """Exclui um utilizador da base de dados."""
    if not conn or not conn.is_connected(): return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Erro ao excluir utilizador: {e}")
        return False

def get_user_details(conn, username):
    """Busca os detalhes de um utilizador específico."""
    if not conn or not conn.is_connected(): return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username, name, email, is_admin, force_password_change FROM users WHERE username = %s", (username,))
        return cursor.fetchone()
    except mysql.connector.Error as e:
        print(f"Erro ao buscar detalhes do utilizador: {e}")
        return None

def get_all_usernames(conn):
    """Retorna uma lista com o nome de todos os utilizadores."""
    if not conn or not conn.is_connected(): return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users")
        return [item[0] for item in cursor.fetchall()]
    except mysql.connector.Error as e:
        print(f"Erro ao buscar usernames: {e}")
        return []

def update_user_password(conn, username, new_hashed_password):
    """Atualiza a palavra-passe de um utilizador."""
    if not conn or not conn.is_connected(): return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = %s WHERE username = %s", (new_hashed_password, username))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        print(f"Erro ao atualizar palavra-passe: {e}")
        return False

def check_force_password_change(conn, username):
    """Verifica se o utilizador precisa de alterar a palavra-passe."""
    details = get_user_details(conn, username)
    return details.get('force_password_change', False) if details else False

def set_password_change_flag(conn, username, force_change: bool):
    """Define a flag que força a alteração de palavra-passe."""
    if not conn or not conn.is_connected(): return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET force_password_change = %s WHERE username = %s", (force_change, username))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        print(f"Erro ao definir flag de alteração de palavra-passe: {e}")
        return False


def fetch_all_users_for_admin_view(conn):
    """Busca todos os utilizadores para exibição no painel de admin (sem palavra-passe)."""
    engine = get_sqlalchemy_engine()
    if engine is None: return pd.DataFrame() # Retorna DF vazio se o engine falhar
    try:
        query = text("SELECT username, name, email, is_admin, force_password_change FROM users")
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        # Converte booleanos para texto mais legível
        if 'is_admin' in df.columns:
             df['is_admin'] = df['is_admin'].apply(lambda x: 'Sim' if x else 'Não')
        if 'force_password_change' in df.columns:
            df['force_password_change'] = df['force_password_change'].apply(lambda x: 'Sim' if x else 'Não')
        return df
    except Exception as e:
        print(f"Erro ao buscar utilizadores para admin view: {e}")
        return pd.DataFrame() # Retorna DF vazio em caso de erro


# ==============================================================================
# FUNÇÕES DE MANIPULAÇÃO DE NOTAS FISCAIS (usando mysql.connector e SQLAlchemy)
# ==============================================================================
def get_all_hashes(conn):
    """Busca todos os hashes de ficheiros já processados na base de dados."""
    if not conn or not conn.is_connected(): return set()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT hash FROM notas_fiscais")
        return {row[0] for row in cursor.fetchall()}
    except mysql.connector.Error as e:
        print(f"Erro ao buscar hashes: {e}")
        return set()

def insert_record(conn, data_dict):
    """Insere ou atualiza um registo na tabela 'notas_fiscais'."""
    if not conn or not conn.is_connected():
        print("Erro: Conexão inválida para inserir registo.")
        return False
    if not data_dict or 'hash' not in data_dict or not data_dict['hash']: # Verifica se hash existe e não é vazio
        print("Erro: Dados inválidos ou hash ausente/vazio para inserção.")
        return False

    try:
        cursor = conn.cursor()
        # Usa apenas as colunas presentes em data_dict E que existem na tabela (HEADERS_DB)
        # Garante que None seja tratado corretamente (não incluído ou inserido como NULL)
        cols_to_insert = [h for h in HEADERS_DB if h in data_dict] # Inclui colunas com None por enquanto
        cols_str = ', '.join([f"`{h}`" for h in cols_to_insert])
        placeholders = ', '.join(['%s'] * len(cols_to_insert))
        updates = ', '.join([f"`{h}`=VALUES(`{h}`)" for h in cols_to_insert if h != 'hash'])

        if not updates: # Se só o hash está presente, não faz sentido atualizar
             print(f"AVISO: Apenas o hash encontrado para {data_dict['hash']}. Nenhuma atualização realizada.")
             # Pode optar por não fazer nada ou apenas inserir o hash se ele não existir
             # Vamos tentar inserir apenas com os dados disponíveis
             if len(cols_to_insert) == 1 and cols_to_insert[0] == 'hash':
                  # Tenta inserir só o hash se ele ainda não existir (raro, mas possível)
                  sql = f"INSERT IGNORE INTO notas_fiscais (`hash`) VALUES (%s)"
                  values = (data_dict['hash'],)
                  cursor.execute(sql, values)
                  conn.commit()
                  return cursor.rowcount > 0 # Retorna True se inseriu
             else: # Se tem mais colunas mas nenhuma para update, algo está estranho
                  print("AVISO: Nenhuma coluna para atualizar além do hash.")
                  # Mesmo assim, tenta o INSERT .. ON DUPLICATE KEY UPDATE
                  sql = f"INSERT INTO notas_fiscais ({cols_str}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE `hash`=`hash`" # Update dummy
                  values = tuple([data_dict.get(h) for h in cols_to_insert]) # None será convertido para NULL pelo driver
                  cursor.execute(sql, values)
                  conn.commit()
                  return True # Assume sucesso se não deu erro


        sql = f"INSERT INTO notas_fiscais ({cols_str}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"
        values = tuple([data_dict.get(h) for h in cols_to_insert]) # None será convertido para NULL pelo driver

        cursor.execute(sql, values)
        conn.commit()
        return True # Retorna True em caso de sucesso
    except mysql.connector.Error as e:
        print(f"Erro ao inserir/atualizar registo (hash: {data_dict.get('hash', 'N/A')}): {e}")
        try:
            conn.rollback() # Desfaz a transação em caso de erro
        except Exception as rb_e:
             print(f"Erro durante o rollback: {rb_e}")
        return False # Retorna False em caso de erro
    except Exception as ge: # Captura outros erros inesperados
         print(f"Erro geral inesperado ao inserir/atualizar registo (hash: {data_dict.get('hash', 'N/A')}): {ge}")
         traceback.print_exc()
         try:
            conn.rollback()
         except Exception as rb_e:
             print(f"Erro durante o rollback: {rb_e}")
         return False


def fetch_all_data_as_dataframe():
    """Busca todos os dados da tabela de notas e retorna como um DataFrame Pandas."""
    engine = get_sqlalchemy_engine()
    if engine is None: return pd.DataFrame()
    try:
        # Usa a lista HEADERS_DB definida neste módulo
        cols_select = ", ".join([f"`{h}`" for h in HEADERS_DB])
        query = text(f"SELECT {cols_select} FROM notas_fiscais")
        with engine.connect() as connection:
             # Passa explicitamente as colunas esperadas para o read_sql
             # Isso ajuda o Pandas a inferir tipos e lida com colunas potencialmente ausentes no DB
             df = pd.read_sql(query, connection, columns=HEADERS_DB)
        return df
    except Exception as e:
        print(f"Erro ao buscar todos os dados com SQLAlchemy: {e}")
        traceback.print_exc() # Imprime traceback completo
        return pd.DataFrame()

def search_data_as_dataframe(conn, search_term, column_to_search):
    """Busca dados na tabela de notas filtrando por um termo em uma coluna específica (case-insensitive)."""
    engine = get_sqlalchemy_engine()
    if engine is None: return pd.DataFrame()
    if not search_term or not column_to_search:
        print("Termo de pesquisa ou coluna inválidos.")
        # Chama a versão que não precisa de conn
        return fetch_all_data_as_dataframe()

    # Valida se a coluna de busca está na lista permitida (HEADERS_DB definida neste módulo)
    if column_to_search not in HEADERS_DB:
        print(f"Erro: Coluna de pesquisa inválida '{column_to_search}'.")
        return pd.DataFrame()

    try:
        # Usa a lista HEADERS_DB definida neste módulo
        cols_select = ", ".join([f"`{h}`" for h in HEADERS_DB])
        # Usa LOWER() para busca case-insensitive e placeholders seguros
        query = text(f"SELECT {cols_select} FROM notas_fiscais WHERE LOWER(`{column_to_search}`) LIKE LOWER(:term)")
        like_term = f"%{search_term}%"

        with engine.connect() as connection:
            # Passa explicitamente as colunas esperadas
            df = pd.read_sql(query, connection, params={"term": like_term}, columns=HEADERS_DB)
        return df
    except Exception as e:
        print(f"Erro ao buscar dados filtrados com SQLAlchemy (col: {column_to_search}): {e}")
        traceback.print_exc() # Imprime traceback completo
        return pd.DataFrame()

