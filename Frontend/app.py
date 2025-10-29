import streamlit as st
import os
import pandas as pd
from datetime import datetime
import tempfile
import io
import plotly.express as px
import sys
import bcrypt
import streamlit_authenticator as stauth
import traceback # Para depuração de erros
import json # Adicionado para exibir JSON

# --- Bloco de Importação do Backend ---
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.abspath(os.path.join(DIRETORIO_ATUAL, '..'))
if DIRETORIO_RAIZ not in sys.path:
    sys.path.append(DIRETORIO_RAIZ)

# Adicionado para depuração - Verifique o output no seu terminal
print("--- Debug sys.path ---")
print("Diretório Atual (app.py):", DIRETORIO_ATUAL)
print("Diretório Raiz (calculado):", DIRETORIO_RAIZ)
print("sys.path:", sys.path)
print("--- Fim Debug sys.path ---")


# Certifique-se que o nome do arquivo no Backend é 'processador.py'
try:
    # Esta linha assume que o ficheiro se chama 'processador.py' dentro da pasta 'Backend'
    # e que existe um ficheiro '__init__.py' na pasta 'Backend'.
    from Backend.processador import processar_documento_com_llm_local, generate_file_hash, clean_and_format_data
except ImportError as e:
    st.error(f"Erro ao importar 'Backend.processador': {e}. Verifique o nome do arquivo ('processador.py'), se ele existe em 'Backend/', e se 'Backend/__init__.py' existe.")
    st.stop()

from Backend.database import (
    create_connection, create_notas_fiscais_table_if_not_exists, create_users_table_if_not_exists, get_all_hashes,
    insert_record, fetch_all_data_as_dataframe, search_data_as_dataframe,
    add_user, delete_user, get_all_usernames, update_user_password, set_password_change_flag,
    fetch_all_users_for_admin_view, fetch_all_users
)
# Assumindo que user_management.py também está em Backend/
try:
    from Backend.user_management import initialize_authenticator, is_admin, check_force_password_change
except ImportError as e:
     st.error(f"Erro ao importar 'Backend.user_management': {e}. Verifique o nome do arquivo e o caminho.")
     st.stop()


# ==============================================================================
# ESTILIZAÇÃO CSS
# ==============================================================================
st.markdown("""
<style>
    /* ... (Seu código CSS 'Deep Ocean' aqui) ... */
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    h1, h2, h3 { color: #58a6ff; }
    h3 { margin-top: 1.5rem; margin-bottom: 0.5rem; font-size: 1.1rem; font-weight: bold;}
    .stButton>button { border-radius: 8px; border: 1px solid #30363d; background-color: #21262d; color: #58a6ff; }
    .stButton>button:hover { border-color: #58a6ff; background-color: #30363d; color: #ffffff; }
    .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid #30363d; gap: 8px; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #f778ba; color: #f778ba; }
    .stMetric { background-color: #161b22; padding: 10px 16px; border-radius: 8px; border: 1px solid #30363d; text-align: center; }
    .dashboard-section {
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #161b22;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    hr {
        margin-top: 1rem;
        margin-bottom: 1rem;
        border-top: 1px solid #30363d;
    }
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        border: none;
        padding: 0;
    }
    /* Estilo para exibir JSON de forma mais compacta */
    .json-output {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 5px;
        padding: 10px;
        font-size: 0.9em;
        max-height: 300px;
        overflow-y: auto;
        white-space: pre-wrap; /* Garante quebra de linha */
        word-wrap: break-word;
    }

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO E AUTENTICAÇÃO
# ==============================================================================
st.set_page_config(layout="wide", page_title="Extrator de Dados de NFS-e")

# @st.cache_resource # Cache da conexão pode causar problemas se a conexão expirar
def get_db_connection():
    return create_connection()

conn = get_db_connection() # Usa a função para obter a conexão

if conn:
    create_notas_fiscais_table_if_not_exists(conn)
    create_users_table_if_not_exists(conn)
else:
    st.error("Falha fatal ao conectar à base de dados MySQL. Verifique as credenciais no .env e se o serviço está em execução.")
    st.stop()

# @st.cache_resource # Cache do authenticator pode ser problemático com alterações de senha
def init_auth(_conn):
     return initialize_authenticator(_conn)

authenticator = init_auth(conn) # Usa a função para inicializar

if authenticator is None:
    st.error("Erro ao carregar o sistema de autenticação.")
    st.stop()

authenticator.login()

# ==============================================================================
# LÓGICA PRINCIPAL DA APLICAÇÃO
# ==============================================================================
if st.session_state["authentication_status"]:

    if check_force_password_change(conn, st.session_state["username"]):
        st.warning("Este é o seu primeiro login ou a sua palavra-passe foi redefinida. Por segurança, por favor, crie uma nova palavra-passe.")
        with st.form("change_password_form"):
            st.subheader("Alterar a sua Palavra-passe")
            new_password = st.text_input("Nova Palavra-passe", type="password")
            confirm_password = st.text_input("Confirme a Nova Palavra-passe", type="password")
            submitted = st.form_submit_button("Alterar Palavra-passe")
            if submitted:
                if new_password and new_password == confirm_password:
                    password_bytes = new_password.encode('utf-8')
                    salt = bcrypt.gensalt()
                    hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
                    if update_user_password(conn, st.session_state["username"], hashed_password):
                        set_password_change_flag(conn, st.session_state["username"], False)
                        st.success("Palavra-passe alterada com sucesso! A página será recarregada.")
                        st.rerun()
                    else: st.error("Ocorreu um erro ao alterar a sua palavra-passe.")
                else: st.error("As palavras-passe não coincidem ou estão vazias.")

    else:
        with st.sidebar:
            st.write(f'Bem-vindo(a), **{st.session_state["name"]}**')
            authenticator.logout('Logout', 'main', key='unique_key')
            with st.expander("Meu Perfil e Segurança"):
                if st.button("Alterar Minha Palavra-passe"): st.session_state['show_change_password_form'] = True

            if st.session_state.get('show_change_password_form', False):
                 with st.form("user_change_password_form", clear_on_submit=True):
                    st.subheader("Alterar Minha Palavra-passe")
                    current_password = st.text_input("Palavra-passe Atual", type="password")
                    new_password = st.text_input("Nova Palavra-passe", type="password")
                    confirm_password = st.text_input("Confirme a Nova Palavra-passe", type="password")
                    submitted_change = st.form_submit_button("Confirmar Alteração")
                    if submitted_change:
                        current_credentials = fetch_all_users(conn)
                        if current_credentials and current_credentials.get("usernames"):
                            password_correct = False
                            try:
                                username_data = current_credentials['usernames'].get(st.session_state["username"])
                                if username_data:
                                     try:
                                         # Tenta verificar com Hasher (mais moderno do stauth)
                                         password_correct = stauth.Hasher([current_password]).check_pw(username_data['password'])[0]
                                     except Exception as hasher_e:
                                         print(f"Erro ao verificar senha com stauth.Hasher.check_pw: {hasher_e}. Tentando bcrypt...")
                                         # Fallback para bcrypt (se senhas antigas existirem)
                                         try:
                                             password_correct = bcrypt.checkpw(current_password.encode('utf-8'), username_data['password'].encode('utf-8'))
                                         except Exception as bcrypt_e:
                                             print(f"Erro ao verificar senha com bcrypt: {bcrypt_e}")
                            except Exception as e:
                                print(f"Erro geral ao buscar dados do utilizador ou verificar senha: {e}")

                            if password_correct:
                                if new_password and new_password == confirm_password:
                                    # Usa Hasher para gerar a nova senha hash
                                    hashed_password = stauth.Hasher([new_password]).generate()[0]
                                    # password_bytes = new_password.encode('utf-8')
                                    # salt = bcrypt.gensalt()
                                    # hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
                                    if update_user_password(conn, st.session_state["username"], hashed_password):
                                        st.success("Palavra-passe alterada com sucesso!")
                                        st.session_state['show_change_password_form'] = False
                                        st.session_state['authentication_status'] = None # Força novo login
                                        st.session_state['logout'] = True
                                        st.rerun()
                                    else: st.error("Erro ao salvar a nova palavra-passe.")
                                else: st.error("As novas palavras-passe não coincidem ou estão vazias.")
                            else: st.error("A palavra-passe atual está incorreta.")
                        else:
                             st.error("Não foi possível verificar a palavra-passe atual. Tente novamente mais tarde.")

        # --- Definição dos Cabeçalhos para DataFrame e DB ---
        HEADERS_OCR = [
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
            'categoria' # Adicionado categoria se for esperado do OCR/LLM
        ]
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
            'categoria' # Adicionado categoria se for esperado do OCR/LLM ou calculado
        ]

        # --- Funções de Processamento e Finalização ---
        def iniciar_processamento(conn, lista_de_arquivos, modo_pasta=False):
            # Obtém conexão fresca para esta operação
            current_conn = get_db_connection()
            if not current_conn:
                st.error("Não foi possível obter conexão com a base de dados para processamento.")
                return

            existing_hashes = get_all_hashes(current_conn) # Passa a conexão
            dados_para_validacao = [] # Lista para guardar os JSONs brutos extraídos
            dados_brutos_completos = [] # Lista para guardar os dicionários completos (texto+json)
            status_bar = st.progress(0, text="Aguardando início...")

            # Limpa dados anteriores antes de processar novos
            st.session_state['dados_processados_para_editor'] = None
            st.session_state['erros_processamento'] = [] # Lista para guardar todos os erros
            st.session_state['dados_brutos_completos_para_treino'] = None # Limpa dados de treino também

            for i, arquivo in enumerate(lista_de_arquivos):
                progresso_atual = (i + 1) / len(lista_de_arquivos)
                filepath = None # Inicializa filepath
                filename = "N/A" # Inicializa filename
                current_hash = None # Inicializa hash
                try:
                    if modo_pasta:
                        filepath, filename = arquivo, os.path.basename(arquivo)
                    else:
                        filename = arquivo.name
                        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
                            tmp_file.write(arquivo.getvalue())
                            filepath = tmp_file.name

                    status_bar.progress(progresso_atual, text=f"Analisando: '{filename}' ({i+1}/{len(lista_de_arquivos)})")

                    if filepath:
                        current_hash = generate_file_hash(filepath)
                        # Verifica hash apenas se for válido
                        if current_hash and current_hash in existing_hashes:
                            st.warning(f"O ficheiro '{filename}' (hash: {current_hash[:7]}...) já foi processado e será ignorado.")
                            continue
                        elif not current_hash:
                            st.error(f"Não foi possível gerar o hash para '{filename}'. Ficheiro ignorado.")
                            continue

                        # Chama a função que retorna {"texto_bruto_ocr": ..., "json_bruto_llm": ...}
                        dados_para_treino = processar_documento_com_llm_local(filepath)

                        # Guarda sempre o resultado completo (mesmo com erro) para treino/debug
                        if isinstance(dados_para_treino, dict):
                             dados_brutos_completos.append({
                                 "filename": filename, "hash": current_hash, **dados_para_treino
                             })
                        else:
                             st.error(f"Resultado inesperado do processamento para '{filename}'. Tipo: {type(dados_para_treino)}")
                             dados_brutos_completos.append({
                                 "filename": filename, "hash": current_hash,
                                 "texto_bruto_ocr": "Erro no retorno do processador", "json_bruto_llm": None,
                                 "resposta_llm_com_erro": f"Tipo de retorno inválido: {type(dados_para_treino)}"
                             })
                             dados_para_treino = {} # Define como dict vazio para evitar erros abaixo

                        # Se a extração do JSON foi bem-sucedida, prepara para o editor
                        if dados_para_treino.get("json_bruto_llm"):
                            dados_extraidos_raw = dados_para_treino["json_bruto_llm"]
                            dados_extraidos_raw['hash'] = current_hash
                            dados_extraidos_raw['arquivo'] = filename
                            dados_extraidos_raw['data_processamento'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            dados_para_validacao.append(dados_extraidos_raw)
                        else: # Se houve erro na extração do JSON ou retorno inválido
                             erro_msg = f"Falha ao extrair JSON de '{filename}'. Verifique os logs e a resposta abaixo."
                             st.error(erro_msg)
                             erro_info = {
                                 "filename": filename,
                                 "texto_bruto": dados_para_treino.get("texto_bruto_ocr", "N/A"),
                                 "erro_msg": dados_para_treino.get("resposta_llm_com_erro", "Erro desconhecido na extração JSON.")
                             }
                             st.session_state['erros_processamento'].append(erro_info) # Adiciona à lista de erros

                             # Exibe a resposta bruta do LLM que causou o erro AQUI
                             st.subheader(f"Resposta com Erro do LLM para '{filename}'")
                             st.text_area("Resposta Bruta", erro_info['erro_msg'], height=150, key=f"error_ta_{filename}_{i}")
                    else:
                         st.error(f"Não foi possível criar/aceder ao ficheiro temporário para '{filename}'.")

                except Exception as e:
                    st.error(f"Erro fatal ao processar '{filename}': {e}")
                    traceback.print_exc()
                    if filename != "N/A": # Adiciona erro à lista se possível
                        erro_info_fatal = {
                            "filename": filename, "hash": current_hash or "ERRO_HASH",
                            "texto_bruto": "Erro fatal durante processamento", "json_bruto_llm": None,
                            "resposta_llm_com_erro": f"Exceção: {e}"
                        }
                        dados_brutos_completos.append(erro_info_fatal)
                        st.session_state['erros_processamento'].append(erro_info_fatal)


                finally:
                    # Garante a remoção do ficheiro temporário
                    if filepath and not modo_pasta and os.path.exists(filepath):
                        try: os.remove(filepath)
                        except Exception as e: st.warning(f"Não foi possível remover o ficheiro temporário {filepath}: {e}")

            status_bar.empty()
            # Fecha a conexão obtida no início da função
            if current_conn and current_conn.is_connected():
                current_conn.close()
                print("Conexão (iniciar_processamento) fechada.")


            # Processa os resultados após o loop
            if dados_para_validacao: # Se pelo menos um JSON foi extraído com sucesso
                st.success("Extração concluída! Valide os dados brutos extraídos abaixo.")
                df_para_editor = pd.DataFrame(dados_para_validacao)
                cols_para_editor = ['hash', 'arquivo', 'data_processamento'] + HEADERS_OCR
                for col in cols_para_editor:
                   if col not in df_para_editor.columns: df_para_editor[col] = ""
                st.session_state['dados_processados_para_editor'] = df_para_editor[cols_para_editor]

            elif dados_brutos_completos: # Se houve processamento mas nenhum JSON válido
                st.warning("Nenhum JSON válido foi extraído dos ficheiros processados. Verifique os erros exibidos ou os logs do terminal.")
                st.session_state['dados_processados_para_editor'] = None
            else: # Nenhum ficheiro processado ou todos já existiam
                st.info("Nenhum ficheiro novo para processar ou todos já existiam na base de dados.")
                st.session_state['dados_processados_para_editor'] = None

            # Guarda os dados completos (incluindo erros) para o botão de treino
            if dados_brutos_completos: st.session_state['dados_brutos_completos_para_treino'] = dados_brutos_completos
            else: st.session_state['dados_brutos_completos_para_treino'] = None


        def finalizar_lote(df_editado_do_editor):
            # Obtém conexão fresca para esta operação
            current_conn = get_db_connection()
            if not current_conn:
                st.error("Não foi possível obter conexão com a base de dados para salvar.")
                return

            total_validado = len(df_editado_do_editor)
            dados_limpos_lista = []
            sucesso_geral = True

            if total_validado > 0:
                with st.spinner('Limpando e Salvando dados...'):
                    for index, row_editada in df_editado_do_editor.iterrows():
                        dados_brutos_editados = row_editada.to_dict()
                        current_hash = dados_brutos_editados.get('hash', '')
                        filename = dados_brutos_editados.get('arquivo', f'linha_{index}')

                        try:
                            # Chama clean_and_format_data com os dados JÁ EDITADOS
                            dados_limpos = clean_and_format_data(dados_brutos_editados)

                            # Adiciona/Atualiza hash, arquivo, data_processamento
                            dados_limpos['hash'] = current_hash
                            dados_limpos['arquivo'] = filename
                            dados_limpos['data_processamento'] = dados_brutos_editados.get('data_processamento', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

                            # Prepara dados para DB, garantindo todas as colunas
                            row_data_para_db = {}
                            for col_db in HEADERS_DB:
                                row_data_para_db[col_db] = dados_limpos.get(col_db) # Pega o valor limpo
                                if pd.isna(row_data_para_db[col_db]): row_data_para_db[col_db] = None
                                numeric_db_cols = ['ocr_valor_total', 'ocr_valor_base_calculo', 'ocr_valor_aliquota', 'ocr_valor_iss',
                                                    'ocr_valor_deducoes', 'ocr_valor_pis_pasep', 'ocr_valor_cofins', 'ocr_valor_csll',
                                                    'ocr_valor_irrf', 'ocr_valor_inss', 'ocr_valor_credito', 'ocr_valor_tributos_fonte']
                                if col_db in numeric_db_cols and row_data_para_db[col_db] is not None:
                                     try: row_data_para_db[col_db] = float(row_data_para_db[col_db])
                                     except (ValueError, TypeError):
                                          st.warning(f"Valor inválido '{dados_limpos.get(col_db)}' para campo numérico '{col_db}' no ficheiro '{filename}'. Será salvo como NULO.")
                                          row_data_para_db[col_db] = None

                            # Insere no DB (passa a conexão atual)
                            if insert_record(current_conn, row_data_para_db):
                                dados_limpos_lista.append(dados_limpos)
                            else:
                                st.error(f"Erro ao salvar dados do ficheiro '{filename}' no banco de dados.")
                                sucesso_geral = False

                        except Exception as e:
                            st.error(f"Erro ao limpar/processar dados do ficheiro '{filename}' para salvar: {e}")
                            traceback.print_exc()
                            sucesso_geral = False

                # Geração do resumo e ficheiros de exportação
                if sucesso_geral and dados_limpos_lista:
                    df_dados_limpos = pd.DataFrame(dados_limpos_lista)
                    df_dados_limpos = df_dados_limpos.reindex(columns=[col for col in HEADERS_DB if col in df_dados_limpos.columns])

                    valor_total = pd.to_numeric(df_dados_limpos['ocr_valor_total'], errors='coerce').sum()
                    iss_total = pd.to_numeric(df_dados_limpos['ocr_valor_iss'], errors='coerce').sum()
                    inss_total = pd.to_numeric(df_dados_limpos.get('ocr_valor_inss', 0), errors='coerce').sum()

                    output_excel = io.BytesIO()
                    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                        df_dados_limpos.to_excel(writer, index=False, sheet_name='DadosNFS')
                    csv_data = df_dados_limpos.to_csv(index=False).encode('utf-8')

                    st.session_state['resumo_lote_salvo'] = {
                        "total_validado": len(dados_limpos_lista), "valor_total": valor_total,
                        "iss_total": iss_total, "inss_total": inss_total,
                        "excel_data": output_excel.getvalue(), "csv_data": csv_data
                    }
                    st.balloons()
                elif sucesso_geral:
                     st.warning("Nenhum dado foi efetivamente salvo após a limpeza/processamento.")
                else:
                    st.error("Ocorreram erros durante a limpeza ou salvamento. Verifique as mensagens acima.")

                # Limpa o estado para permitir novo processamento
                st.session_state['dados_processados_para_editor'] = None
                st.session_state['dados_brutos_completos_para_treino'] = None

            # Fecha a conexão obtida no início da função
            if current_conn and current_conn.is_connected():
                current_conn.close()
                print("Conexão (finalizar_lote) fechada.")


        # --- Interface Principal ---
        st.title("🤖 Extrator e Gestor Inteligente de Notas Fiscais")

        # Inicializa estados se não existirem
        if 'dados_processados_para_editor' not in st.session_state: st.session_state['dados_processados_para_editor'] = None
        if 'resumo_lote_salvo' not in st.session_state: st.session_state['resumo_lote_salvo'] = None
        if 'dados_brutos_completos_para_treino' not in st.session_state: st.session_state['dados_brutos_completos_para_treino'] = None
        if 'erros_processamento' not in st.session_state: st.session_state['erros_processamento'] = [] # Inicializa lista de erros


        if st.session_state['resumo_lote_salvo'] is not None:
            with st.container(border=True):
                resumo = st.session_state['resumo_lote_salvo']
                st.subheader("📊 Resumo do Último Lote Salvo")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Notas Validadas", f"{resumo['total_validado']}")
                c2.metric("Valor Total", f"R$ {resumo['valor_total']:,.2f}")
                c3.metric("Total ISS", f"R$ {resumo['iss_total']:,.2f}")
                c4.metric("Total INSS", f"R$ {resumo.get('inss_total', 0.0):,.2f}")
                dl_col1, dl_col2, _ = st.columns([1,1,2])
                dl_col1.download_button("📥 Baixar Lote (.xlsx)", resumo['excel_data'], f"lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                dl_col2.download_button("📄 Baixar Lote (.csv)", resumo['csv_data'], f"lote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                st.success("Dados salvos na base de dados com sucesso!")
                if st.button("✔️ OK, Ocultar Resumo"):
                    st.session_state['resumo_lote_salvo'] = None
                    st.rerun()
            st.markdown("---")

        tabs_list = ["➕ Processar Documentos", "🔍 Consultar Dados", "📊 Dashboard Financeiro"]
        if is_admin(conn, st.session_state["username"]):
            tabs_list.append("⚙️ Gerir Utilizadores")

        tabs = st.tabs(tabs_list)

        with tabs[0]: # ABA 1: PROCESSAR
            st.header("Adicionar novos documentos")
            sub_tab1, sub_tab2 = st.tabs(["📤 Upload Manual", "📁 Processar Pasta"])
            with sub_tab1:
                uploaded_files = st.file_uploader("Selecione os ficheiros:", accept_multiple_files=True, type=['pdf', 'png', 'jpg', 'jpeg', 'webp'], key="uploader")
                if uploaded_files:
                     if st.button("▶️ Iniciar Processamento dos Ficheiros Selecionados"):
                         iniciar_processamento(conn, uploaded_files)
                         st.rerun() # Adicionado rerun para atualizar a UI após o processamento

            with sub_tab2:
                caminho_da_pasta = st.text_input("Caminho da pasta no servidor:", value=r'H:\projeto2\Documentos', key="pasta_input")
                if st.button("🔍 Analisar e Processar Pasta", key="processar_pasta_btn"):
                    if os.path.isdir(caminho_da_pasta):
                        try:
                             arquivos_na_pasta = [os.path.join(caminho_da_pasta, f) for f in os.listdir(caminho_da_pasta)
                                                  if os.path.isfile(os.path.join(caminho_da_pasta, f)) and
                                                     f.lower().endswith(('.png','.jpg','.jpeg','.pdf', '.webp'))]
                             if not arquivos_na_pasta:
                                 st.warning("Nenhum ficheiro compatível (.png, .jpg, .jpeg, .pdf, .webp) encontrado na pasta.")
                             else:
                                 iniciar_processamento(conn, arquivos_na_pasta, modo_pasta=True)
                                 st.rerun() # Adicionado rerun para atualizar a UI
                        except Exception as e:
                            st.error(f"Erro ao listar ficheiros na pasta: {e}")
                    else:
                        st.error("Caminho da pasta inválido ou inacessível.")

            # --- Secção de Validação e Edição ---
            # Verifica se 'dados_processados_para_editor' existe e não está vazio
            if st.session_state.get('dados_processados_para_editor') is not None and not st.session_state['dados_processados_para_editor'].empty:
                st.markdown("---")
                st.subheader("📝 Valide e Edite os Dados Extraídos (Brutos)")
                st.info("Estes são os dados brutos extraídos pelo LLM. Clique duas vezes numa célula para editar antes de salvar.")

                df_para_editar = st.session_state['dados_processados_para_editor']

                # --- Exibição do JSON Bruto ---
                # Mostra o JSON bruto do PRIMEIRO ficheiro processado neste lote
                dados_brutos_completos = st.session_state.get('dados_brutos_completos_para_treino', [])
                if dados_brutos_completos:
                    # Encontra o primeiro item que teve sucesso na extração JSON
                    primeiro_item_sucesso = next((item for item in dados_brutos_completos if item.get("json_bruto_llm")), None)
                    if primeiro_item_sucesso:
                        st.subheader(f"JSON Bruto Recebido do LLM para '{primeiro_item_sucesso.get('filename', 'N/A')}' (Exemplo)")
                        json_para_mostrar = primeiro_item_sucesso.get('json_bruto_llm', {})
                        try:
                            st.code(json.dumps(json_para_mostrar, indent=2, ensure_ascii=False), language='json')
                        except Exception as e:
                            st.warning(f"Não foi possível exibir o JSON bruto: {e}")
                    elif dados_brutos_completos: # Se nenhum teve sucesso, mostra o erro do primeiro
                         primeiro_item_erro = dados_brutos_completos[0]
                         st.subheader(f"JSON Bruto Recebido do LLM para '{primeiro_item_erro.get('filename', 'N/A')}' (Exemplo)")
                         st.warning("A extração do JSON falhou para este ficheiro. Exibindo resposta bruta:")
                         st.text_area("Resposta Bruta", primeiro_item_erro.get('resposta_llm_com_erro', 'N/A'), height=150, key=f"error_ta_{primeiro_item_erro.get('filename', 'unknown')}_display")

                # --- Editor ---
                dados_editados_df = st.data_editor(
                    df_para_editar,
                    #num_rows="dynamic", # Remover se não quiser adicionar/remover linhas
                    height=400,
                    key="data_editor",
                    use_container_width=True,
                    # Opcional: Configurar colunas específicas se necessário
                    # column_config={ ... }
                 )

                # --- Botões de Ação ---
                col_btn1, col_btn2, col_btn3 = st.columns([1,1,2])

                if col_btn1.button("✅ Salvar Dados Limpos na Base de Dados"):
                     finalizar_lote(dados_editados_df) # Passa só o DF, a func obtém conn
                     st.rerun() # Rerun APÓS finalizar_lote

                if col_btn2.button("❌ Cancelar Edição"):
                    st.session_state['dados_processados_para_editor'] = None
                    st.session_state['dados_brutos_completos_para_treino'] = None
                    st.rerun()

                # --- Botão para Exportar Dados de Treino ---
                if st.session_state.get('dados_brutos_completos_para_treino'):
                    try:
                        jsonl_data = ""
                        for item in st.session_state['dados_brutos_completos_para_treino']:
                            # Cria o par prompt/completion (JSON bruto do LLM)
                            if item.get("json_bruto_llm"):
                                training_pair = {
                                    "prompt": item.get("texto_bruto_ocr", ""),
                                    "completion": json.dumps(item["json_bruto_llm"], ensure_ascii=False)
                                }
                                jsonl_data += json.dumps(training_pair, ensure_ascii=False) + "\n"
                            # Opcional: Incluir erros no ficheiro de treino
                            elif item.get("resposta_llm_com_erro"):
                                error_pair = {
                                     "prompt": item.get("texto_bruto_ocr", ""),
                                     "completion_error": item.get("resposta_llm_com_erro")
                                }
                                jsonl_data += json.dumps(error_pair, ensure_ascii=False) + "\n"

                        if jsonl_data:
                            col_btn3.download_button(
                                label="🧬 Baixar Dados para Treino (.jsonl)",
                                data=jsonl_data.encode('utf-8'),
                                file_name=f"dados_treino_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl",
                                mime="application/jsonl",
                                help="Este ficheiro contém o texto OCR e o JSON bruto extraído pelo LLM. CORRIJA o JSON manualmente antes de usar para treinar."
                            )
                    except Exception as e:
                        col_btn3.warning(f"Erro ao gerar dados de treino: {e}")

            # Exibe mensagem se houve erro durante o processamento (e não há dados válidos)
            elif st.session_state.get('erros_processamento'): # Usa a lista de erros
                 st.info("Nenhum dado válido extraído para edição devido a erros no processamento. Verifique as mensagens de erro acima.")
                 pass


        with tabs[1]: # ABA 2: CONSULTAR
            st.header("Consultar e Analisar a Base de Dados")
            st.subheader("Pesquisa Rápida")
            col_search1, col_search2 = st.columns([1, 2])

            search_field_map = {
                "CNPJ do Prestador": "ocr_prestador_cpf_cnpj",
                "Razão Social (Prestador)": "ocr_prestador_nome",
                "Número da Nota": "ocr_numero",
                "Razão Social (Tomador)": "ocr_tomador_nome",
                "Categoria": "categoria" # Descomentar se a coluna existir e for útil
            }
            search_field_display = col_search1.selectbox("Pesquisar por:", list(search_field_map.keys()))
            search_column_db = search_field_map[search_field_display]
            search_term = col_search2.text_input("Digite o termo para procurar:", key="search_box_specific")

            # Busca inicial ao carregar a aba ou após limpar pesquisa
            if 'df_consulta' not in st.session_state or not search_term:
                 st.session_state.df_consulta = fetch_all_data_as_dataframe()

            if st.button("🔎 Pesquisar", key="pesquisar_btn"):
                if search_term:
                    # Passa conn para search_data_as_dataframe
                    st.session_state.df_consulta = search_data_as_dataframe(conn, search_term, search_column_db)
                else:
                    # Já busca tudo se o termo estiver vazio
                    st.session_state.df_consulta = fetch_all_data_as_dataframe()
                    st.info("Nenhum termo inserido. Exibindo todos os dados.")
                st.rerun() # Atualiza a exibição com os resultados

            df_completo = st.session_state.get('df_consulta') # Pega o DataFrame do estado

            if df_completo is not None and not df_completo.empty:
                st.markdown("---")
                st.subheader("Resumo Financeiro da Seleção Atual")
                numeric_cols_db = ['ocr_valor_total', 'ocr_valor_iss', 'ocr_valor_inss', 'ocr_valor_pis_pasep',
                                   'ocr_valor_cofins', 'ocr_valor_csll', 'ocr_valor_irrf']
                for col in numeric_cols_db:
                    if col in df_completo.columns:
                         df_completo[col] = pd.to_numeric(df_completo[col], errors='coerce').fillna(0.0)
                    else: df_completo[col] = 0.0

                total_servicos_selecao = df_completo['ocr_valor_total'].sum()
                total_iss_selecao = df_completo['ocr_valor_iss'].sum()
                total_inss_selecao = df_completo['ocr_valor_inss'].sum()
                total_pis_selecao = df_completo['ocr_valor_pis_pasep'].sum()
                total_cofins_selecao = df_completo['ocr_valor_cofins'].sum()
                total_csll_selecao = df_completo['ocr_valor_csll'].sum()
                total_ir_selecao = df_completo['ocr_valor_irrf'].sum()
                total_retido_selecao = total_iss_selecao + total_inss_selecao + total_pis_selecao + total_cofins_selecao + total_csll_selecao + total_ir_selecao

                sum_col1, sum_col2, sum_col3 = st.columns(3)
                sum_col1.metric("Soma Valor Total", f"R$ {total_servicos_selecao:,.2f}")
                sum_col2.metric("Soma ISS", f"R$ {total_iss_selecao:,.2f}")
                sum_col3.metric("Soma Total Retido", f"R$ {total_retido_selecao:,.2f}")

                st.markdown("---")
                st.metric("Total de Notas na Seleção", f"{len(df_completo)}")
                # Define a ordem das colunas para exibição (baseado em HEADERS_DB)
                cols_display_consulta = [col for col in HEADERS_DB if col in df_completo.columns]
                st.dataframe(df_completo[cols_display_consulta], use_container_width=True)
                csv_export = df_completo[cols_display_consulta].to_csv(index=False).encode('utf-8')
                st.download_button("📄 Baixar resultado da consulta (.csv)", csv_export, "consulta.csv", "text/csv")
            elif df_completo is not None:
                st.info("Nenhum registo encontrado para os critérios de pesquisa.")
            else:
                 st.error("Erro ao buscar dados no banco de dados.")

        with tabs[2]: # ABA 3: DASHBOARD FINANCEIRO
            st.header("📊 Dashboard Financeiro")
            # Chama sem 'conn'
            df_dashboard = fetch_all_data_as_dataframe()

            if df_dashboard is not None and not df_dashboard.empty and 'ocr_emissao_datahora' in df_dashboard.columns:
                try:
                    numeric_cols_dash = [
                        'ocr_valor_total', 'ocr_valor_iss', 'ocr_valor_base_calculo', 'ocr_valor_aliquota',
                        'ocr_valor_pis_pasep', 'ocr_valor_cofins', 'ocr_valor_csll', 'ocr_valor_irrf', 'ocr_valor_inss'
                    ]
                    for col in numeric_cols_dash:
                        if col in df_dashboard.columns:
                            df_dashboard[col] = pd.to_numeric(df_dashboard[col], errors='coerce').fillna(0.0)
                        else: df_dashboard[col] = 0.0

                    df_dashboard['ocr_emissao_datahora'] = pd.to_datetime(df_dashboard['ocr_emissao_datahora'], errors='coerce')
                    df_dashboard.dropna(subset=['ocr_emissao_datahora'], inplace=True)

                    if 'ocr_valor_total' in df_dashboard.columns:
                         df_dashboard = df_dashboard[df_dashboard['ocr_valor_total'].notna() & (df_dashboard['ocr_valor_total'] > 0)]

                    if not df_dashboard.empty:
                        df_dashboard['mes_ano'] = df_dashboard['ocr_emissao_datahora'].dt.to_period('M').astype(str)

                        st.subheader("Indicadores Chave (Período Completo)")
                        total_servicos = df_dashboard['ocr_valor_total'].sum()
                        total_iss = df_dashboard['ocr_valor_iss'].sum()
                        total_inss = df_dashboard['ocr_valor_inss'].sum()
                        total_pis = df_dashboard['ocr_valor_pis_pasep'].sum()
                        total_cofins = df_dashboard['ocr_valor_cofins'].sum()
                        total_csll = df_dashboard['ocr_valor_csll'].sum()
                        total_ir = df_dashboard['ocr_valor_irrf'].sum()
                        total_retido = total_iss + total_inss + total_pis + total_cofins + total_csll + total_ir
                        num_notas = len(df_dashboard)
                        valor_medio_nota = total_servicos / num_notas if num_notas > 0 else 0
                        carga_tributaria_retida = total_retido / total_servicos if total_servicos > 0 else 0

                        kpi_cols = st.columns(4)
                        kpi_cols[0].metric("Valor Total Serviços", f"R$ {total_servicos:,.2f}")
                        kpi_cols[1].metric("Total Impostos Retidos", f"R$ {total_retido:,.2f}")
                        kpi_cols[2].metric("Carga Tributária Média", f"{carga_tributaria_retida:.2%}", help="Percentagem do valor total que corresponde a impostos retidos.")
                        kpi_cols[3].metric("Valor Médio por Nota", f"R$ {valor_medio_nota:,.2f}", help="Custo médio de cada serviço registado.")
                        st.markdown("<hr/>", unsafe_allow_html=True)

                        st.subheader("📈 Evolução Mensal")
                        agg_dict_dash = {
                            'ocr_valor_total': ('ocr_valor_total', 'sum'),
                            'ocr_valor_iss': ('ocr_valor_iss', 'sum'),
                            'ocr_valor_inss': ('ocr_valor_inss', 'sum'),
                            'ocr_valor_pis_pasep': ('ocr_valor_pis_pasep', 'sum'),
                            'ocr_valor_cofins': ('ocr_valor_cofins', 'sum'),
                            'ocr_valor_csll': ('ocr_valor_csll', 'sum'),
                            'ocr_valor_irrf': ('ocr_valor_irrf', 'sum'),
                        }
                        df_evolucao = df_dashboard.groupby('mes_ano').agg(**agg_dict_dash).reset_index()

                        if len(df_evolucao['mes_ano'].unique()) > 1:
                            try:
                                df_evolucao['mes_ano_dt'] = pd.to_datetime(df_evolucao['mes_ano'])
                                date_range_index = pd.period_range(start=df_evolucao['mes_ano_dt'].min().to_period('M'),
                                                                  end=df_evolucao['mes_ano_dt'].max().to_period('M'),
                                                                  freq='M').strftime('%Y-%m')
                                df_evolucao = df_evolucao.set_index('mes_ano').reindex(date_range_index, fill_value=0).reset_index().rename(columns={'index': 'mes_ano'})
                                df_evolucao.drop(columns=['mes_ano_dt'], inplace=True, errors='ignore')
                            except Exception as e:
                                st.warning(f"Erro ao criar intervalo de datas contínuo: {e}")

                        df_evolucao['total_retido'] = df_evolucao[['ocr_valor_iss', 'ocr_valor_inss', 'ocr_valor_pis_pasep', 'ocr_valor_cofins', 'ocr_valor_csll', 'ocr_valor_irrf']].sum(axis=1)
                        df_evolucao = df_evolucao.sort_values('mes_ano')

                        if not df_evolucao.empty and len(df_evolucao) > 0:
                            fig_evolucao = px.bar(df_evolucao, x='mes_ano', y=['ocr_valor_total', 'total_retido'],
                                                  title="Valor Total vs. Impostos Retidos por Mês",
                                                  labels={'value': 'Valor (R$)', 'mes_ano': 'Mês', 'variable': 'Métrica'},
                                                  barmode='group',
                                                  color_discrete_map={'ocr_valor_total': '#58a6ff', 'total_retido': '#f778ba'}
                                                  )
                            fig_evolucao.update_layout(legend_title_text='')
                            st.plotly_chart(fig_evolucao, use_container_width=True, config={'displaylogo': False})
                        else:
                            st.info("Não há dados mensais suficientes ou válidos para o gráfico de evolução.")
                        st.markdown("<hr/>", unsafe_allow_html=True)

                        col1, col2 = st.columns(2)
                        with col1:
                            with st.container(border=True):
                                st.subheader("👥 Análise de Prestadores")
                                if 'ocr_prestador_nome' in df_dashboard.columns:
                                    df_dashboard['prestador_display'] = df_dashboard['ocr_prestador_nome'].fillna('N/A').str.strip()
                                    df_dashboard.loc[df_dashboard['prestador_display'] == '', 'prestador_display'] = 'N/A'

                                    top_prestadores = df_dashboard.groupby('prestador_display')['ocr_valor_total'].sum().nlargest(5).reset_index()
                                    if not top_prestadores.empty and not (len(top_prestadores)==1 and top_prestadores.iloc[0]['prestador_display']=='N/A'):
                                        fig_prestadores = px.bar(top_prestadores, y='prestador_display', x='ocr_valor_total',
                                                                 orientation='h', title="Top 5 Maiores Fornecedores")
                                        fig_prestadores.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Valor Total (R$)", yaxis_title="")
                                        st.plotly_chart(fig_prestadores, use_container_width=True, config={'displaylogo': False})
                                        percent_top5 = top_prestadores['ocr_valor_total'].sum() / total_servicos if total_servicos > 0 else 0
                                        st.metric("Concentração nos Top 5", f"{percent_top5:.1%}",
                                                  help="Percentual do valor total gasto com os 5 maiores fornecedores. Valores altos podem indicar dependência excessiva e risco. Considere diversificar.")
                                    else:
                                        st.info("Não há dados suficientes (ex: diferentes prestadores válidos) para o gráfico de Top Prestadores.")
                                else:
                                    st.warning("Coluna 'ocr_prestador_nome' não encontrada.")

                        with col2:
                            with st.container(border=True):
                                st.subheader("🏷️ Análise por Categoria (Se disponível)")
                                # Assumindo que 'categoria' é adicionada em clean_and_format_data ou pelo LLM
                                if 'categoria' in df_dashboard.columns:
                                    df_categoria = df_dashboard.dropna(subset=['categoria'])
                                    df_categoria = df_categoria[df_categoria['categoria'].astype(str).str.strip().fillna('') != ''] # Converte para str antes
                                    if not df_categoria.empty:
                                        df_categoria_agg = df_categoria.groupby('categoria')['ocr_valor_total'].sum().reset_index().sort_values(by='ocr_valor_total', ascending=True)
                                        if not df_categoria_agg.empty:
                                            fig_categoria = px.bar(df_categoria_agg, x='ocr_valor_total', y='categoria',
                                                                   orientation='h', title="Distribuição de Gastos por Categoria")
                                            fig_categoria.update_layout(xaxis_title="Valor Total (R$)", yaxis_title="")
                                            st.plotly_chart(fig_categoria, use_container_width=True, config={'displaylogo': False})
                                            categoria_max = df_categoria_agg.iloc[-1]
                                            st.metric(f"Principal Categoria: {categoria_max['categoria']}",
                                                      f"R$ {categoria_max['ocr_valor_total']:,.2f}",
                                                      help="Categoria com o maior valor total. Analise se os gastos nesta área estão alinhados com os objetivos.")
                                        else: st.info("Não há categorias válidas após agregação.")
                                    else: st.info("Não há notas categorizadas (ou categorias válidas) para exibir este gráfico.")
                                else: st.info("Coluna 'categoria' não encontrada ou não preenchida nos dados para análise por categoria.")
                        st.markdown("<hr/>", unsafe_allow_html=True)

                        with st.container(border=True):
                            st.subheader("💸 Maiores Notas Fiscais Registadas (Top 5)")
                            cols_maiores_notas = ['ocr_emissao_datahora', 'ocr_prestador_nome', 'ocr_discriminacao', 'ocr_valor_total']
                            if 'categoria' in df_dashboard.columns: cols_maiores_notas.append('categoria')
                            cols_presentes = [col for col in cols_maiores_notas if col in df_dashboard.columns]

                            if 'ocr_valor_total' in df_dashboard.columns and 'ocr_emissao_datahora' in df_dashboard.columns:
                                maiores_notas = df_dashboard.nlargest(5, 'ocr_valor_total')[cols_presentes]
                                maiores_notas_display = maiores_notas.copy()
                                maiores_notas_display['ocr_emissao_datahora'] = pd.to_datetime(maiores_notas_display['ocr_emissao_datahora']).dt.strftime('%d/%m/%Y')
                                st.dataframe(maiores_notas_display, use_container_width=True, hide_index=True)
                            else: st.warning("Faltam colunas essenciais ('ocr_valor_total', 'ocr_emissao_datahora') para exibir as maiores notas.")
                    else: st.info("Não há dados válidos após a limpeza para gerar o dashboard.")
                except Exception as e:
                    st.error(f"Erro ao gerar o dashboard: {e}")
                    traceback.print_exc()
            elif df_dashboard is not None:
                st.info("Não há dados na base de dados para gerar o dashboard.")
            else:
                 st.error("Erro ao buscar dados do banco de dados para o dashboard.")

        if is_admin(conn, st.session_state["username"]):
            try:
                with tabs[3]: # ABA 4: GERIR UTILIZADORES
                    st.header("⚙️ Painel de Gestão de Utilizadores")
                    st.subheader("Lista de Utilizadores")
                    users_df = fetch_all_users_for_admin_view(conn)
                    if users_df is not None:
                        st.dataframe(users_df, use_container_width=True)
                        csv_users = users_df.to_csv(index=False).encode('utf-8')
                        st.download_button("📄 Baixar Lista de Utilizadores (.csv)", csv_users, "lista_utilizadores.csv", "text/csv")
                    else: st.error("Erro ao carregar lista de utilizadores.")

                    st.markdown("---")
                    with st.expander("➕ Criar Novo Utilizador"):
                        with st.form("create_user_form", clear_on_submit=True):
                            new_username = st.text_input("Nome de Utilizador (Username)")
                            new_name = st.text_input("Nome Completo")
                            new_email = st.text_input("E-mail")
                            new_password = st.text_input("Palavra-passe Temporária", type="password")
                            is_admin_checkbox = st.checkbox("Este utilizador é um administrador?")
                            submitted_create = st.form_submit_button("Criar Utilizador")
                            if submitted_create:
                                if new_username and new_name and new_email and new_password:
                                    # Usa Hasher para gerar hash da senha
                                    hashed_password = stauth.Hasher([new_password]).generate()[0]
                                    # password_bytes = new_password.encode('utf-8')
                                    # salt = bcrypt.gensalt()
                                    # hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
                                    if add_user(conn, new_username, new_email, new_name, hashed_password, is_admin_checkbox, force_change=True):
                                        st.success(f"Utilizador '{new_username}' criado com sucesso! Terá de alterar a palavra-passe no primeiro login.")
                                        st.rerun()
                                    else: st.error("Erro ao criar utilizador. O nome de utilizador ou e-mail pode já existir.")
                                else: st.warning("Por favor, preencha todos os campos.")

                    st.subheader("Gerir Utilizadores Existentes")
                    all_usernames = get_all_usernames(conn)
                    if all_usernames:
                        user_to_manage = st.selectbox("Selecione um utilizador para gerir:", options=[u for u in all_usernames if u != st.session_state["username"]], key="manage_user_select", index=None, placeholder="Escolha um utilizador...") # Impede auto-exclusão na seleção
                        if user_to_manage:
                            col_manage1, col_manage2 = st.columns(2)
                            with col_manage1:
                                if st.button(f"Forçar alteração de palavra-passe para '{user_to_manage}'", key=f"force_pw_{user_to_manage}"):
                                    if set_password_change_flag(conn, user_to_manage, True):
                                        st.success(f"O utilizador '{user_to_manage}' terá de alterar a sua palavra-passe no próximo login.")
                                    else: st.error("Ocorreu um erro.")
                            with col_manage2:
                                # A verificação if user_to_manage == st.session_state["username"] é redundante
                                if st.button(f"🗑️ Excluir Utilizador '{user_to_manage}'", type="primary", key=f"delete_user_{user_to_manage}"):
                                     # Adiciona confirmação explícita
                                     st.session_state[f'confirm_delete_{user_to_manage}'] = True

                            # Lógica de confirmação de exclusão
                            if st.session_state.get(f'confirm_delete_{user_to_manage}', False):
                                st.warning(f"Tem a certeza que deseja excluir o utilizador '{user_to_manage}'? Esta ação é irreversível.")
                                confirm_col1, confirm_col2 = st.columns(2)
                                if confirm_col1.button("Sim, excluir", key=f"confirm_yes_{user_to_manage}"):
                                    if delete_user(conn, user_to_manage):
                                        st.success(f"Utilizador '{user_to_manage}' excluído com sucesso!")
                                        st.session_state[f'confirm_delete_{user_to_manage}'] = False # Reseta confirmação
                                        st.rerun() # Atualiza a lista
                                    else: st.error("Erro ao excluir o utilizador.")
                                if confirm_col2.button("Não, cancelar", key=f"confirm_no_{user_to_manage}"):
                                    st.session_state[f'confirm_delete_{user_to_manage}'] = False # Reseta confirmação
                                    st.rerun() # Apenas para limpar os botões de confirmação

            except Exception as e:
                 st.error(f"Erro ao carregar a aba de gestão de utilizadores: {e}")
                 traceback.print_exc()


# --- Lógica de Login/Erro ---
elif st.session_state["authentication_status"] is False:
    st.error('Nome de utilizador/palavra-passe incorretos')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, insira o seu nome de utilizador e palavra-passe')

