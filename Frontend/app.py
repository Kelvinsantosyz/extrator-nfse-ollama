import streamlit as st
import os
import pandas as pd
from datetime import datetime
import tempfile
import io
import plotly.express as px
import sys

# --- Bloco de Importação do Backend ---
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.abspath(os.path.join(DIRETORIO_ATUAL, '..'))
if DIRETORIO_RAIZ not in sys.path:
    sys.path.append(DIRETORIO_RAIZ)

from Backend.processador import processar_documento_com_llm_local, generate_file_hash, clean_and_format_data
from Backend.database import (
    create_connection,
    create_table_if_not_exists,
    get_all_hashes,
    insert_record,
    fetch_all_data_as_dataframe,
    search_data_as_dataframe
)

# ==============================================================================
# ESTILIZAÇÃO CSS (TEMA "DEEP OCEAN")
# ==============================================================================
st.markdown("""
<style>
    /* Cor de fundo principal */
    .stApp {
        background-color: #0d1117; /* Azul-petróleo bem escuro */
        color: #c9d1d9; /* Texto cinza claro */
    }
    /* Títulos */
    h1, h2, h3 {
        color: #58a6ff; /* Azul claro para títulos */
    }
    /* Botões */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #30363d; /* Borda cinza */
        background-color: #21262d; /* Fundo do botão cinza escuro */
        color: #58a6ff; /* Texto do botão azul */
        transition: all 0.2s ease-in-out;
        padding: 8px 20px;
    }
    .stButton>button:hover {
        border-color: #58a6ff;
        background-color: #30363d;
        color: #ffffff;
    }
    /* Abas */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid #30363d;
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: transparent;
        border-bottom: 2px solid transparent;
        padding: 8px;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 2px solid #f778ba; /* Destaque rosa/magenta para aba ativa */
        color: #f778ba;
    }
    /* Métricas */
    .stMetric {
        background-color: #161b22; /* Fundo da métrica */
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #30363d;
    }
    /* Containers e bordas */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        border: 1px solid #30363d;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# CONFIGURAÇÃO GERAL E CABEÇALHOS
# ==============================================================================
HEADERS = [
    'hash', 'arquivo', 'data_processamento', 'numero_nota', 'data_hora_emissao', 'codigo_verificacao',
    'prestador_cnpj', 'prestador_razao_social', 'prestador_inscricao_municipal',
    'prestador_logradouro', 'prestador_bairro', 'prestador_cep', 'prestador_cidade', 'prestador_uf',
    'tomador_cpf', 'tomador_razao_social', 'tomador_email',
    'tomador_logradouro', 'tomador_bairro', 'tomador_cep', 'tomador_cidade', 'tomador_uf',
    'discriminacao_servicos', 'servico_codigo', 'servico_descricao',
    'valor_total_servico', 'base_calculo', 'aliquota', 'valor_iss',
    'valor_total_impostos', 'categoria'
]

# ==============================================================================
# FUNÇÕES DE APOIO DA INTERFACE
# ==============================================================================
def iniciar_processamento(conn, lista_de_arquivos, modo_pasta=False):
    """Processa uma lista de arquivos e armazena os resultados na sessão."""
    existing_hashes = get_all_hashes(conn)
    novos_dados = []
    status_bar = st.progress(0, text="Aguardando início...")
    for i, arquivo in enumerate(lista_de_arquivos):
        progresso_atual = (i + 1) / len(lista_de_arquivos)
        if modo_pasta:
            filepath, filename = arquivo, os.path.basename(arquivo)
        else:
            filename = arquivo.name
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
                tmp_file.write(arquivo.getvalue()); filepath = tmp_file.name
        
        status_bar.progress(progresso_atual, text=f"Analisando: '{filename}' ({i+1}/{len(lista_de_arquivos)})")
        current_hash = generate_file_hash(filepath)

        if current_hash in existing_hashes:
            st.warning(f"O arquivo '{filename}' já foi processado e será ignorado.")
            if not modo_pasta: os.remove(filepath)
            continue

        dados_brutos = processar_documento_com_llm_local(filepath)
        if not modo_pasta: os.remove(filepath)

        if not dados_brutos:
            st.error(f"Falha ao extrair dados de '{filename}'.")
            continue
        
        dados_achatados = {
            "numero_nota": dados_brutos.get("numero_nota"), "data_hora_emissao": dados_brutos.get("data_hora_emissao"),
            "codigo_verificacao": dados_brutos.get("codigo_verificacao"), "prestador_cnpj": dados_brutos.get("prestador", {}).get("cnpj"),
            "prestador_razao_social": dados_brutos.get("prestador", {}).get("razao_social"), "prestador_inscricao_municipal": dados_brutos.get("prestador", {}).get("inscricao_municipal"),
            "prestador_logradouro": dados_brutos.get("prestador", {}).get("endereco", {}).get("logradouro"), "prestador_bairro": dados_brutos.get("prestador", {}).get("endereco", {}).get("bairro"),
            "prestador_cep": dados_brutos.get("prestador", {}).get("endereco", {}).get("cep"), "prestador_cidade": dados_brutos.get("prestador", {}).get("endereco", {}).get("cidade"),
            "prestador_uf": dados_brutos.get("prestador", {}).get("endereco", {}).get("uf"), "tomador_cpf": dados_brutos.get("tomador", {}).get("cpf"),
            "tomador_razao_social": dados_brutos.get("tomador", {}).get("razao_social"), "tomador_email": dados_brutos.get("tomador", {}).get("email"),
            "tomador_logradouro": dados_brutos.get("tomador", {}).get("endereco", {}).get("logradouro"), "tomador_bairro": dados_brutos.get("tomador", {}).get("endereco", {}).get("bairro"),
            "tomador_cep": dados_brutos.get("tomador", {}).get("endereco", {}).get("cep"), "tomador_cidade": dados_brutos.get("tomador", {}).get("endereco", {}).get("cidade"),
            "tomador_uf": dados_brutos.get("tomador", {}).get("endereco", {}).get("uf"), "discriminacao_servicos": dados_brutos.get("servico", {}).get("discriminacao"),
            "servico_codigo": dados_brutos.get("servico", {}).get("codigo"), "servico_descricao": dados_brutos.get("servico", {}).get("descricao"),
            "valor_total_servico": dados_brutos.get("valores", {}).get("total_servico"), "base_calculo": dados_brutos.get("valores", {}).get("base_calculo"),
            "aliquota": dados_brutos.get("valores", {}).get("aliquota"), "valor_iss": dados_brutos.get("valores", {}).get("valor_iss"),
            "valor_total_impostos": dados_brutos.get("valor_total_impostos"), 
            "categoria": dados_brutos.get("categoria")
        }
        dados_finais = clean_and_format_data(dados_achatados)
        dados_finais.update({'hash': current_hash, 'arquivo': filename, 'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        novos_dados.append(dados_finais)
        
    status_bar.empty()
    if novos_dados:
        st.success("Extração concluída! Valide os dados novos abaixo.")
        st.session_state['dados_processados'] = pd.DataFrame(novos_dados)
    else:
        st.info("Nenhum arquivo novo para processar.")

def finalizar_lote(conn, dados_editados_df):
    """Salva os dados no banco, prepara o resumo e o armazena na sessão."""
    total_validado = len(dados_editados_df)
    if total_validado > 0:
        for index, row in dados_editados_df.iterrows():
            insert_record(conn, row.to_dict(), HEADERS)
    
    valor_total = pd.to_numeric(dados_editados_df['valor_total_servico'], errors='coerce').sum()
    iss_total = pd.to_numeric(dados_editados_df['valor_iss'], errors='coerce').sum()

    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
        dados_editados_df.to_excel(writer, index=False, sheet_name='DadosNFS', columns=HEADERS)
    csv_data = dados_editados_df.to_csv(index=False, columns=HEADERS).encode('utf-8')
    
    st.session_state['resumo_lote_salvo'] = {
        "total_validado": total_validado, "valor_total": valor_total, "iss_total": iss_total,
        "excel_data": output_excel.getvalue(), "csv_data": csv_data
    }
    st.session_state['dados_processados'] = None
    st.balloons()

# ==============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ==============================================================================

st.set_page_config(layout="wide", page_title="Extrator de Dados de NFS-e")

if 'dados_processados' not in st.session_state:
    st.session_state['dados_processados'] = None
if 'resumo_lote_salvo' not in st.session_state:
    st.session_state['resumo_lote_salvo'] = None

st.title("🤖 Extrator e Gerenciador Inteligente de Notas Fiscais")

conn = create_connection()
if conn:
    create_table_if_not_exists(conn)
else:
    st.error("Falha ao conectar ao banco de dados MySQL. Verifique as credenciais no .env e se o serviço está rodando.")
    st.stop()

# ==============================================================================
# LAYOUT DA PÁGINA
# ==============================================================================

if st.session_state['resumo_lote_salvo'] is not None:
    with st.container(border=True):
        resumo = st.session_state['resumo_lote_salvo']
        st.subheader("📊 Resumo do Último Lote Salvo")
        c1, c2, c3 = st.columns(3)
        c1.metric("Notas Validadas", f"{resumo['total_validado']}")
        c2.metric("Valor Total do Lote", f"R$ {resumo['valor_total']:,.2f}")
        c3.metric("Total de ISS do Lote", f"R$ {resumo['iss_total']:,.2f}")
        dl_col1, dl_col2, _ = st.columns([1,1,2])
        dl_col1.download_button("📥 Baixar Lote (.xlsx)", resumo['excel_data'], f"lote_{datetime.now().strftime('%Y%m%d')}.xlsx")
        dl_col2.download_button("📄 Baixar Lote (.csv)", resumo['csv_data'], f"lote_{datetime.now().strftime('%Y%m%d')}.csv")
        st.success("Dados salvos no banco de dados com sucesso!")
        if st.button("✔️ OK, Ocultar Resumo"):
            st.session_state['resumo_lote_salvo'] = None
            st.rerun()
    st.markdown("---")

tab1, tab2, tab3 = st.tabs([ "➕ Processar Documentos", "🔍 Consultar Dados", "📊 Dashboard Financeiro" ])

with tab1:
    st.header("Adicionar novos documentos")
    sub_tab1, sub_tab2 = st.tabs(["📤 Upload Manual", "📁 Processar Pasta"])
    with sub_tab1:
        uploaded_files = st.file_uploader("Selecione os arquivos:", accept_multiple_files=True, key="uploader")
        if uploaded_files and st.button("▶️ Iniciar Processamento dos Arquivos"):
            iniciar_processamento(conn, uploaded_files)
    with sub_tab2:
        caminho_da_pasta = st.text_input("Caminho da pasta no servidor:", value=r'H:\projeto2\Documentos')
        if st.button("🔍 Analisar e Processar Pasta"):
            if os.path.isdir(caminho_da_pasta):
                arquivos = [os.path.join(caminho_da_pasta, f) for f in os.listdir(caminho_da_pasta) if f.lower().endswith(('.png','.jpg','.jpeg','.pdf'))]
                if not arquivos: st.warning("Nenhum arquivo compatível encontrado.")
                else: iniciar_processamento(conn, arquivos, modo_pasta=True)
            else: st.error("Caminho inválido.")

    if st.session_state['dados_processados'] is not None and not st.session_state['dados_processados'].empty:
        st.markdown("---")
        st.subheader("📝 Valide e Edite os Dados Extraídos")
        st.info("Clique duas vezes em uma célula para editar. A 'categoria' é uma sugestão da IA.")
        dados_editados_df = st.data_editor(st.session_state['dados_processados'], num_rows="dynamic", height=300)
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("✅ Salvar no Banco de Dados"):
            with st.spinner('Salvando...'):
                finalizar_lote(conn, dados_editados_df)
                st.rerun()
        if col_btn2.button("❌ Cancelar"):
            st.session_state['dados_processados'] = None
            st.rerun()

with tab2:
    st.header("Consultar e Analisar o Banco de Dados")
    
    st.subheader("Pesquisa Rápida")
    col_search1, col_search2 = st.columns([1, 2])
    search_field = col_search1.selectbox("Pesquisar por:", ["CNPJ do Prestador", "Razão Social", "Número da Nota"])
    search_term = col_search2.text_input("Digite o termo para buscar:", key="search_box_specific")

    if st.button("🔎 Pesquisar"):
        df_completo = search_data_as_dataframe(conn, search_term, search_field)
    else:
        df_completo = fetch_all_data_as_dataframe(conn)

    if not df_completo.empty:
        # --- SEÇÃO DE RESUMO FINANCEIRO ATUALIZADA ---
        st.markdown("---")
        st.subheader("Resumo Financeiro da Seleção Atual")
        total_servicos_selecao = pd.to_numeric(df_completo['valor_total_servico'], errors='coerce').sum()
        total_iss_selecao = pd.to_numeric(df_completo['valor_iss'], errors='coerce').sum()
        
        sum_col1, sum_col2 = st.columns(2)
        sum_col1.metric("Soma Valor Total", f"R$ {total_servicos_selecao:,.2f}")
        sum_col2.metric("Soma ISS", f"R$ {total_iss_selecao:,.2f}")
        st.markdown("---")
        # --- FIM DA SEÇÃO ---

        st.metric("Total de Notas na Seleção", f"{len(df_completo)}")
        st.dataframe(df_completo)
        
        csv_export = df_completo.to_csv(index=False).encode('utf-8')
        st.download_button("📄 Baixar resultado da consulta (.csv)", csv_export, "consulta.csv", "text/csv")
    else:
        st.info("Nenhum registro encontrado para os critérios de busca.")

with tab3:
    st.header("📊 Dashboard Financeiro")
    df_dashboard = fetch_all_data_as_dataframe(conn)
    if not df_dashboard.empty and 'data_hora_emissao' in df_dashboard.columns:
        numeric_cols = ['valor_total_servico', 'valor_iss', 'base_calculo', 'aliquota', 'valor_total_impostos']
        for col in numeric_cols:
            if col in df_dashboard.columns:
                df_dashboard[col] = pd.to_numeric(df_dashboard[col], errors='coerce')
        
        df_dashboard['data_hora_emissao'] = pd.to_datetime(df_dashboard['data_hora_emissao'], errors='coerce')
        df_dashboard.dropna(subset=['data_hora_emissao', 'valor_total_servico'], inplace=True)
        
        st.subheader("Visão Geral")
        total_servicos = df_dashboard['valor_total_servico'].sum()
        total_iss = df_dashboard['valor_iss'].sum()
        carga_tributaria = (total_iss) / total_servicos if total_servicos > 0 else 0
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Valor Total em Notas", f"R$ {total_servicos:,.2f}")
        metric_col2.metric("Total de ISS Pago", f"R$ {total_iss:,.2f}")
        metric_col3.metric("Carga Tributária Média (ISS)", f"{carga_tributaria:.2%}")
        st.markdown("---")

        df_dashboard['mes_ano'] = df_dashboard['data_hora_emissao'].dt.to_period('M').astype(str)
        
        st.subheader("Evolução Mensal")
        df_evolucao = df_dashboard.groupby('mes_ano').agg(
            valor_total_servico=('valor_total_servico', 'sum'),
            valor_iss=('valor_iss', 'sum')
        ).reset_index().sort_values('mes_ano')
        
        fig_evolucao = px.bar(df_evolucao, x='mes_ano', y=['valor_total_servico', 'valor_iss'], 
                              title="Valor Total de Serviços vs. Imposto (ISS) por Mês", 
                              labels={'value': 'Valor (R$)', 'mes_ano': 'Mês'}, barmode='group')
        st.plotly_chart(fig_evolucao, use_container_width=True)

        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top 5 Prestadores por Valor Total")
            top_prestadores = df_dashboard.groupby('prestador_razao_social')['valor_total_servico'].sum().nlargest(5).reset_index()
            fig_prestadores = px.bar(top_prestadores, y='prestador_razao_social', x='valor_total_servico', 
                                     orientation='h', title="Maiores Fornecedores")
            fig_prestadores.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Valor Total (R$)", yaxis_title="Prestador")
            st.plotly_chart(fig_prestadores, use_container_width=True)
        
        with col2:
            st.subheader("Distribuição de Despesas por Categoria")
            df_categoria = df_dashboard.dropna(subset=['categoria'])
            df_categoria = df_categoria[df_categoria['categoria'].str.strip() != '']
            if not df_categoria.empty:
                fig_categoria = px.pie(df_categoria, names='categoria', values='valor_total_servico', 
                                       title="Percentual de Gastos por Categoria", hole=.3)
                st.plotly_chart(fig_categoria, use_container_width=True)
            else:
                st.info("Não há notas categorizadas para exibir este gráfico.")
    else:
        st.info("Não há dados suficientes no banco para gerar o dashboard.")

