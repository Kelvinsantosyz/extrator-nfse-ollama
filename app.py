

import streamlit as st
import os
import pandas as pd
from datetime import datetime
import tempfile
import io
import plotly.express as px

# Importa as funções do seu outro arquivo, o processador.py
from processador import (
    processar_documento_com_llm_local,
    generate_file_hash,
    clean_and_format_data,
    CAMINHO_PLANILHA,
    PASTA_PLANILHA,
    HEADERS
)

# ==============================================================================
# FUNÇÕES DE APOIO
# ==============================================================================
def iniciar_processamento(lista_de_arquivos, modo_pasta=False):
    """Função que processa os arquivos e SALVA os resultados no session_state."""
    try:
        df_existente = pd.read_excel(CAMINHO_PLANILHA)
        existing_hashes = set(df_existente['hash'].astype(str).tolist())
    except FileNotFoundError:
        df_existente = pd.DataFrame(columns=HEADERS)
        existing_hashes = set()
    novos_dados = []
    status_bar = st.progress(0, text="Aguardando início...")
    for i, arquivo in enumerate(lista_de_arquivos):
        progresso_atual = (i + 1) / len(lista_de_arquivos)
        if modo_pasta:
            filepath = arquivo; filename = os.path.basename(filepath)
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
        if "texto_extraido" in dados_brutos:
            dados_finais = {"hash": current_hash, "arquivo": filename, "data_processamento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),"discriminacao_servicos": dados_brutos["texto_extraido"]}
        else:
            dados_achatados = {"numero_nota": dados_brutos.get("numero_nota"),"data_hora_emissao": dados_brutos.get("data_hora_emissao"),"codigo_verificacao": dados_brutos.get("codigo_verificacao"),"prestador_cnpj": dados_brutos.get("prestador", {}).get("cnpj"),"prestador_razao_social": dados_brutos.get("prestador", {}).get("razao_social"),"prestador_inscricao_municipal": dados_brutos.get("prestador", {}).get("inscricao_municipal"),"prestador_logradouro": dados_brutos.get("prestador", {}).get("endereco", {}).get("logradouro"),"prestador_bairro": dados_brutos.get("prestador", {}).get("endereco", {}).get("bairro"),"prestador_cep": dados_brutos.get("prestador", {}).get("endereco", {}).get("cep"),"prestador_cidade": dados_brutos.get("prestador", {}).get("endereco", {}).get("cidade"),"prestador_uf": dados_brutos.get("prestador", {}).get("endereco", {}).get("uf"),"tomador_cpf": dados_brutos.get("tomador", {}).get("cpf"),"tomador_razao_social": dados_brutos.get("tomador", {}).get("razao_social"),"tomador_email": dados_brutos.get("tomador", {}).get("email"),"tomador_logradouro": dados_brutos.get("tomador", {}).get("endereco", {}).get("logradouro"),"tomador_bairro": dados_brutos.get("tomador", {}).get("endereco", {}).get("bairro"),"tomador_cep": dados_brutos.get("tomador", {}).get("endereco", {}).get("cep"),"tomador_cidade": dados_brutos.get("tomador", {}).get("endereco", {}).get("cidade"),"tomador_uf": dados_brutos.get("tomador", {}).get("endereco", {}).get("uf"),"discriminacao_servicos": dados_brutos.get("servico", {}).get("discriminacao"),"servico_codigo": dados_brutos.get("servico", {}).get("codigo"),"servico_descricao": dados_brutos.get("servico", {}).get("descricao"),"valor_total_servico": dados_brutos.get("valores", {}).get("total_servico"),"base_calculo": dados_brutos.get("valores", {}).get("base_calculo"),"aliquota": dados_brutos.get("valores", {}).get("aliquota"),"valor_iss": dados_brutos.get("valores", {}).get("valor_iss"),"valor_total_impostos": dados_brutos.get("valor_total_impostos")}
            dados_finais = clean_and_format_data(dados_achatados)
            dados_finais.update({'hash': current_hash, 'arquivo': filename, 'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        novos_dados.append(dados_finais)
    status_bar.empty()
    if novos_dados:
        st.success("Extração concluída! Valide os dados novos abaixo.")
        st.session_state['dados_processados'] = pd.DataFrame(novos_dados)
    else:
        st.info("Nenhum arquivo novo para processar. Todos os documentos selecionados já constam na base de dados.")

def finalizar_lote(dados_editados_df):
    """Salva os dados, prepara o resumo e o armazena no session_state."""
    try:
        df_existente = pd.read_excel(CAMINHO_PLANILHA)
    except FileNotFoundError:
        df_existente = pd.DataFrame(columns=HEADERS)
    
    total_validado = len(dados_editados_df)
    if 'valor_total_servico' in dados_editados_df.columns: valor_total = pd.to_numeric(dados_editados_df['valor_total_servico'], errors='coerce').sum()
    else: valor_total = 0.0
    if 'valor_iss' in dados_editados_df.columns: iss_total = pd.to_numeric(dados_editados_df['valor_iss'], errors='coerce').sum()
    else: iss_total = 0.0

    df_final = pd.concat([df_existente, dados_editados_df], ignore_index=True)
    df_final.drop_duplicates(subset=['hash'], keep='last', inplace=True)
    
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer: df_final.to_excel(writer, index=False, sheet_name='DadosNFS', columns=HEADERS)
    csv_data = df_final.to_csv(index=False, columns=HEADERS).encode('utf-8')
    
    df_final.to_excel(CAMINHO_PLANILHA, index=False, columns=HEADERS)
    
    st.session_state['resumo_lote_salvo'] = {
        "total_validado": total_validado, "valor_total": valor_total, "iss_total": iss_total,
        "excel_data": output_excel.getvalue(), "csv_data": csv_data
    }
    st.session_state['dados_processados'] = None
    st.balloons()


# --- Configuração da Página e Título ---
st.set_page_config(layout="wide", page_title="Extrator de Dados de NFS-e")
if 'dados_processados' not in st.session_state:
    st.session_state['dados_processados'] = None
if 'resumo_lote_salvo' not in st.session_state:
    st.session_state['resumo_lote_salvo'] = None
st.title("🤖 Extrator e Gerenciador Inteligente de Notas Fiscais")


# ==============================================================================
# SEÇÃO DE RESUMO DO LOTE SALVO (SEMPRE VISÍVEL SE HOUVER DADOS)
# ==============================================================================
if st.session_state['resumo_lote_salvo'] is not None:
    with st.container(border=True):
        resumo = st.session_state['resumo_lote_salvo']
        st.subheader("📊 Resumo do Último Lote Salvo")

        c1, c2, c3 = st.columns(3)
        c1.metric("Notas Validadas no Lote", f"{resumo['total_validado']}")
        c2.metric("Valor Total do Lote", f"R$ {resumo['valor_total']:,.2f}")
        c3.metric("Total de ISS do Lote", f"R$ {resumo['iss_total']:,.2f}")
        
        dl_col1, dl_col2, dl_col3 = st.columns([1,1,2])
        dl_col1.download_button("📥 Baixar Excel (.xlsx)", resumo['excel_data'], f"planilha_{datetime.now().strftime('%Y%m%d')}.xlsx")
        dl_col2.download_button("📄 Baixar CSV (.csv)", resumo['csv_data'], f"planilha_{datetime.now().strftime('%Y%m%d')}.csv")
        
        st.success("Backup da planilha foi salvo com sucesso!")

        if st.button("✔️ OK, Ocultar Resumo"):
            st.session_state['resumo_lote_salvo'] = None
            st.rerun()
    st.markdown("---")


# --- Definição das Abas ---
tab1, tab2, tab3 = st.tabs([
    "➕ Processar Novos Documentos", 
    "🔍 Consultar Planilha",
    "📊 Dashboard de Análise"
])

with tab1:
    st.header("Escolha o método para adicionar novos documentos:")
    sub_tab1, sub_tab2 = st.tabs(["📤 Upload Manual", "📁 Processar Pasta do Servidor"])
    with sub_tab1:
        uploaded_files = st.file_uploader("Selecione os arquivos:", accept_multiple_files=True, key="uploader")
        if uploaded_files:
            if st.button("▶️ Iniciar Processamento dos Arquivos Enviados"):
                iniciar_processamento(uploaded_files, modo_pasta=False)
    with sub_tab2:
        caminho_da_pasta = st.text_input("Caminho da pasta:", value=r'H:\projeto2\Documentos')
        if st.button("🔍 Analisar e Processar Pasta"):
            if caminho_da_pasta and os.path.isdir(caminho_da_pasta):
                arquivos = [os.path.join(caminho_da_pasta, f) for f in os.listdir(caminho_da_pasta) if f.lower().endswith(('.png','.jpg','.jpeg','.pdf'))]
                if not arquivos: 
                    st.warning("Nenhum arquivo compatível encontrado.")
                else: 
                    iniciar_processamento(arquivos, modo_pasta=True)
            else: 
                st.error("O caminho informado não é uma pasta válida.")

    if st.session_state['dados_processados'] is not None and not st.session_state['dados_processados'].empty:
        st.markdown("---")
        st.subheader("📝 Valide e Edite os Dados Extraídos")
        st.info("Clique duas vezes em uma célula para editar.")
        dados_editados_df = st.data_editor(st.session_state['dados_processados'], num_rows="dynamic", height=300)
        
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("✅ Salvar Alterações e Finalizar Lote"):
            with st.spinner('Salvando...'):
                finalizar_lote(dados_editados_df)
                st.rerun()
        if col_btn2.button("❌ Cancelar e Limpar Lote"):
            st.session_state['dados_processados'] = None
            st.rerun()

with tab2:
    st.header("Consultar e Analisar a Planilha Salva")
    try:
        df_completo = pd.read_excel(CAMINHO_PLANILHA)
        st.metric("Total de Notas na Base", f"{len(df_completo)}")
        termo_pesquisa = st.text_input("Digite para filtrar por qualquer coluna:", key="search_box")
        if termo_pesquisa:
            mask = df_completo.apply(lambda row: row.astype(str).str.contains(termo_pesquisa, case=False).any(), axis=1)
            st.dataframe(df_completo[mask])
        else:
            st.dataframe(df_completo)
    except FileNotFoundError:
        st.info("A planilha de dados ainda não foi criada. Processe o primeiro documento para começar.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler a planilha: {e}")

with tab3:
    st.header("Análise de Valor Total por Estado do Prestador")
    try:
        df_dashboard = pd.read_excel(CAMINHO_PLANILHA)
        if 'data_hora_emissao' in df_dashboard.columns:
            df_dashboard['data_hora_emissao'] = pd.to_datetime(df_dashboard['data_hora_emissao'], errors='coerce')
            df_dashboard.dropna(subset=['data_hora_emissao'], inplace=True)
            df_dashboard['mes_ano'] = df_dashboard['data_hora_emissao'].dt.strftime('%Y-%m')
            opcoes_filtro = ["Todos os Meses"] + sorted(df_dashboard['mes_ano'].unique(), reverse=True)
            mes_selecionado = st.selectbox("Selecione o Mês para Análise:", options=opcoes_filtro)
            if mes_selecionado == "Todos os Meses":
                df_filtrado = df_dashboard
            else:
                df_filtrado = df_dashboard[df_dashboard['mes_ano'] == mes_selecionado]
            if 'prestador_uf' in df_filtrado.columns and 'valor_total_servico' in df_filtrado.columns:
                df_chart = df_filtrado.dropna(subset=['prestador_uf', 'valor_total_servico'])
                df_chart = df_chart[df_chart['prestador_uf'].str.strip() != '']
                if not df_chart.empty:
                    valor_por_estado = df_chart.groupby('prestador_uf')['valor_total_servico'].sum()
                    valor_por_estado_df = valor_por_estado.reset_index()
                    st.subheader(f"Distribuição Percentual por Estado ({mes_selecionado})")
                    fig = px.pie(valor_por_estado_df, values='valor_total_servico', names='prestador_uf', title='Proporção do Valor Total de Serviços por Estado')
                    st.plotly_chart(fig, use_container_width=True)
                    st.subheader(f"Dados Agregados ({mes_selecionado})")
                    st.dataframe(valor_por_estado_df.sort_values(by='valor_total_servico', ascending=False))
                else:
                    st.warning(f"Não há dados suficientes para gerar o gráfico para o período '{mes_selecionado}'.")
            else:
                st.warning("A planilha precisa das colunas 'prestador_uf' e 'valor_total_servico' para gerar a análise.")
        else:
            st.warning("A coluna 'data_hora_emissao' é necessária para o filtro de mês.")
    except FileNotFoundError:
        st.info("A planilha de dados ainda não foi criada.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar a análise: {e}")