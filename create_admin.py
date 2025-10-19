import sys
import os
import getpass
import subprocess

# ==============================================================================
# VERIFICADOR E INSTALADOR AUTOMÁTICO DE DEPENDÊNCIAS
# ==============================================================================
def check_and_install(package):
    """Verifica se uma biblioteca está instalada e, caso contrário, instala-a via pip."""
    try:
        __import__(package)
    except ImportError:
        print(f"Biblioteca '{package}' não encontrada. A tentar instalar agora...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Biblioteca '{package}' instalada com sucesso.")
        except Exception as e:
            print(f"--- ERRO CRÍTICO ---")
            print(f"Falha ao instalar '{package}'. Por favor, ative o seu ambiente virtual ('venv') e instale manualmente:")
            print(f"pip install {package}")
            print(f"Erro original: {e}")
            sys.exit(1)

# Verifica as dependências essenciais, incluindo a nova biblioteca 'bcrypt'.
check_and_install('bcrypt')
check_and_install('mysql_connector_python')
check_and_install('python_dotenv')
# ==============================================================================

# Agora que garantimos que as bibliotecas estão instaladas, podemos importá-las.
import bcrypt

# --- CORREÇÃO DE IMPORTAÇÃO ---
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
if DIRETORIO_ATUAL not in sys.path:
    sys.path.append(DIRETORIO_ATUAL)
# -----------------------------

# Importa as funções da base de dados com tratamento de erros
try:
    from Backend.database import create_connection, create_users_table_if_not_exists, add_user
except ImportError:
    print("\n[ERRO FATAL] Não foi possível encontrar o módulo 'Backend.database'.")
    print("Certifique-se de que está a executar este script a partir da pasta raiz do projeto (H:\\projeto2).")
    sys.exit(1)

def setup_initial_admin():
    """Guia o utilizador para criar o primeiro administrador na base de dados."""
    print("--- Configuração do Utilizador Administrador Inicial ---")
    
    print("\nPasso 1: A tentar conectar-se à base de dados...")
    conn = create_connection()
    if not conn:
        print("\n[FALHA] Não foi possível conectar à base de dados. Verifique o seu arquivo .env e se o serviço MySQL está em execução.")
        return
    print("[SUCESSO] Conexão com a base de dados estabelecida.")

    print("\nPasso 2: A verificar/criar a tabela de utilizadores...")
    create_users_table_if_not_exists(conn)
    print("[SUCESSO] Tabela de utilizadores pronta.")

    # Recolhe as informações do novo administrador
    username = input("\nDigite o nome de utilizador para o administrador (ex: admin): ")
    name = input("Digite o nome completo do administrador (ex: Administrador do Sistema): ")
    email = input("Digite o e-mail do administrador: ")
    password = getpass.getpass("Digite a palavra-passe para o administrador: ")
    
    is_admin_input = input("Este utilizador deve ser um administrador? (s/N): ").lower()
    is_admin_flag = True if is_admin_input == 's' else False

    print("\nPasso 3: A gerar o hash da palavra-passe...")
    try:
        # CORREÇÃO DEFINITIVA: Usando 'bcrypt' diretamente para gerar o hash
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password_bytes = bcrypt.hashpw(password_bytes, salt)
        hashed_password = hashed_password_bytes.decode('utf-8')
        print("[SUCESSO] Hash da palavra-passe gerado com segurança.")
        
        print(f"\nPasso 4: A tentar adicionar o utilizador '{username}' à base de dados...")
        if add_user(conn, username, email, name, hashed_password, is_admin_flag):
            print(f"\n[SUCESSO FINAL] Utilizador administrador '{username}' criado com sucesso!")
        else:
            print(f"\n[FALHA] Não foi possível criar o utilizador. Verifique a mensagem de erro acima (pode ser que o nome de utilizador ou e-mail já existam).")

    except Exception as e:
        print(f"\n[ERRO INESPERADO] Ocorreu um erro ao processar a palavra-passe ou ao salvar: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print("\nConexão com a base de dados fechada.")

if __name__ == "__main__":
    setup_initial_admin()

