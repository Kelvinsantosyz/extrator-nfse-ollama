import streamlit_authenticator as stauth
from .database import fetch_all_users, get_user_details

def initialize_authenticator(conn):
    """Carrega as credenciais da base de dados e inicializa o objeto de autenticação."""
    if not conn:
        return None
    try:
        credentials = fetch_all_users(conn)
        if not credentials or not credentials.get("usernames"):
            credentials = {'usernames': {}}

        authenticator = stauth.Authenticate(
            credentials,
            'cookie_nfse_app',
            'key_assinatura_secreta',
            cookie_expiry_days=30
        )
        return authenticator
    except Exception as e:
        print(f"Erro ao inicializar o autenticador: {e}")
        return None

def is_admin(conn, username):
    """Verifica se um utilizador tem permissões de administrador."""
    user_details = get_user_details(conn, username)
    return bool(user_details and user_details.get('is_admin'))

def check_force_password_change(conn, username):
    """Verifica se um utilizador precisa de alterar a sua palavra-passe."""
    user_details = get_user_details(conn, username)
    return bool(user_details and user_details.get('force_password_change'))

