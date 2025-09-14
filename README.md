# Extrator Inteligente de Notas Fiscais com IA Local e Streamlit

*Este projeto foi desenvolvido para a disciplina de **PROJETO EM COMPUTAÇÃO APLICADA** da **UNINOVE (Universidade Nove de Julho)**, sob orientação do **Prof. Luis Carlos dos Santos Junior.***

---

## 📜 Introdução

Este projeto é uma aplicação web completa, construída com Streamlit, que utiliza um modelo de linguagem e visão (multimodal) rodando localmente com Ollama para extrair, validar e analisar informações de Notas Fiscais de Serviço Eletrônicas (NFS-e). A ferramenta transforma o processo manual de entrada de dados em um fluxo de trabalho inteligente e interativo.

A aplicação é 100% local, garantindo que nenhum dado sensível seja enviado para APIs externas, oferecendo total privacidade e segurança.

## ✨ Funcionalidades Principais

A aplicação vai muito além de um simples script, oferecendo um ambiente completo para gerenciamento de NFS-e:

-   **Interface Web Interativa**: Uma interface amigável e intuitiva construída com Streamlit, organizada em abas para diferentes tarefas.
-   **Motor de Extração Híbrido**:
    -   Usa o modelo multimodal **LLaVA** para "ler" e extrair dados estruturados diretamente de imagens e PDFs.
    -   Possui um sistema de **fallback para OCR** (Tesseract) para garantir a extração de texto mesmo que a análise da IA falhe.
-   **Múltiplos Métodos de Entrada**:
    -   **Upload Manual**: Permite ao usuário subir múltiplos arquivos (`.png`, `.jpg`, `.pdf`) de uma vez.
    -   **Processamento em Lote**: Processa automaticamente todos os documentos dentro de uma pasta especificada no servidor.
-   **Validação Humana no Fluxo (Human-in-the-loop)**:
    -   Apresenta os dados extraídos em uma **tabela editável** (`st.data_editor`), permitindo que o usuário corrija qualquer imprecisão da IA antes de salvar.
-   **Dashboard para Análise de Dados**:
    -   Uma aba de "Dashboard" que gera visualizações a partir dos dados salvos.
    -   **Gráfico de Pizza Interativo** (com Plotly) para analisar a distribuição de valores por estado (UF).
    -   **Filtro Dinâmico por Mês/Ano** para analisar a performance em diferentes períodos.
-   **Consulta e Pesquisa**:
    -   Uma aba para visualizar e **pesquisar em toda a base de dados** salva, com filtros por qualquer termo.
    -   Exibe métricas e KPIs (Indicadores) do total de notas e valores acumulados.
-   **Gerenciamento de Dados Robusto**:
    -   **Prevenção de Duplicatas**: Utiliza hash MD5 para identificar e ignorar arquivos já processados.
    -   **Integridade de Dados**: Garante que não haja entradas duplicadas na planilha final.
    -   **Exportação Flexível**: Permite o download dos dados validados nos formatos **Excel (.xlsx)** e **CSV**.

## 🛠️ Tecnologias Utilizadas

| Biblioteca | Principal Uso |
| :--- | :--- |
| `streamlit` | Criação da interface web interativa e do dashboard. |
| `pandas` | Manipulação, limpeza, filtragem e agregação dos dados. |
| `ollama` | Execução local do modelo de linguagem multimodal (LLaVA). |
| `pytesseract` | OCR (Reconhecimento Óptico de Caracteres) para o sistema de fallback. |
| `PyMuPDF` | Extração de texto de arquivos PDF para o OCR. |
| `Pillow` | Manipulação de imagens para o OCR. |
| `plotly` | Geração de gráficos interativos (pizza). |
| `openpyxl`, `xlsxwriter`| Leitura e escrita de arquivos Excel (.xlsx). |

## 🚀 Como Executar o Projeto

Siga os passos abaixo para configurar e executar a aplicação.

### 1. Pré-requisitos

-   **Python 3.8+**: [python.org](https://www.python.org/downloads/)
-   **Ollama**: Siga as instruções de instalação em [ollama.com](https://ollama.com/).
-   **Modelo LLaVA**: Após instalar o Ollama, abra um terminal e execute:
    ```bash
    # Você pode escolher um modelo menor e mais rápido, como 'llava:7b'
    ollama pull llava:13b
    ```
-   **Google Tesseract OCR**: Para o sistema de fallback funcionar, instale o Tesseract seguindo as [instruções para Windows](https://github.com/tesseract-ocr/tessdoc/blob/main/Installation.md) (lembre-se de adicionar o local da instalação à variável de ambiente PATH).

### 2. Configuração do Projeto

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/Kelvinsantosyz/extrator-nfse-ollama.git](https://github.com/Kelvinsantosyz/extrator-nfse-ollama.git)
    cd extrator-nfse-ollama
    ```
2.  **Crie e ative um ambiente virtual**:
    ```bash
    # Criar
    python -m venv venv
    # Ativar no Windows (PowerShell)
    .\venv\Scripts\Activate.ps1
    ```
3.  **Instale as bibliotecas Python**:
    ```bash
    # Use o comando mais robusto para garantir que o pip do venv seja usado
    python -m pip install -r requirements.txt
    ```
4.  **Crie as pastas necessárias** na raiz do projeto, se não existirem:
    - `/Documentos/` (para o processamento em lote)
    - `/Planilha/` (onde o arquivo Excel será salvo)

### 3. Execução

1.  **Inicie o aplicativo Streamlit** a partir do seu terminal (com o ambiente virtual ativado):
    ```bash
    python -m streamlit run app.py
    ```
2.  **Abra o navegador**: O Streamlit abrirá uma aba no seu navegador com a aplicação rodando. Agora você pode usar a interface para processar seus documentos.

## 📸 Screenshots da Aplicação

*(Sugestão: Adicione aqui alguns prints da sua aplicação em funcionamento!)*

- *Tela de Processamento de Documentos*
- *Tela do Dashboard com o Gráfico*
- *Tela de Consulta com a Pesquisa*

## 👨‍💻 Desenvolvedor

-   **Kelvin Santos**