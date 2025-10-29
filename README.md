# 🤖 Extrator Inteligente de NFS-e com OCR e LLM

Este projeto utiliza tecnologias de Reconhecimento Óptico de Caracteres (OCR) e Modelos de Linguagem Grandes (LLMs) locais (via Ollama) ou na nuvem (Azure) para extrair dados estruturados de Notas Fiscais de Serviço eletrônicas (NFS-e) brasileiras, armazenando-os numa base de dados MySQL. Uma interface web construída com Streamlit permite o upload, processamento, visualização, edição e gestão dos dados e utilizadores.

---

**⚠️ Nota Importante sobre Precisão**

Nenhum sistema de OCR ou LLM é 100% perfeito, especialmente com a variedade de layouts e a qualidade variável dos documentos digitalizados (incluindo imagens como PNG, JPEG, WEBP).
* **OCR (Azure, Ollama, EasyOCR):** Pode haver erros na leitura de caracteres (ex: "5" confundido com "S", "1" com "I"), especialmente em imagens de baixa resolução ou com texto sobreposto.
* **Extração LLM (Ollama/Phi3):** O modelo pode, ocasionalmente, interpretar mal o texto do OCR, confundir campos (Prestador vs. Tomador), omitir informações ou gerar um JSON inválido, principalmente se o texto do OCR contiver muitos erros.

**É crucial utilizar a funcionalidade de validação e edição (`st.data_editor`) fornecida na interface para verificar e corrigir os dados extraídos *antes* de os salvar na base de dados.** O objetivo da IA aqui é acelerar o processo, mas a revisão humana continua a ser fundamental para garantir a precisão final dos dados. O fine-tuning do LLM pode *aumentar significativamente* a precisão da extração para os *seus* tipos de documento, mas a validação ainda é recomendada.

---

## ✨ Funcionalidades

* **Upload Flexível:** Carregue ficheiros PDF, PNG, JPG, JPEG ou WEBP individualmente ou processe todos os ficheiros compatíveis numa pasta.
* **Múltiplas Opções de OCR:** Escolha o motor de OCR que melhor se adapta às suas necessidades através de configuração (`.env`):
    * **Azure Computer Vision:** Serviço de OCR na nuvem da Microsoft (requer subscrição Azure). Potencialmente alta precisão.
    * **Ollama LMM (Local):** Utilize modelos de linguagem multimodais (como Llama 3.2 Vision, Llava, Granite) executados localmente via Ollama. Flexível, mas pode ser mais lento e consumir mais recursos.
    * **EasyOCR (Local):** Biblioteca Python especializada em OCR, otimizada para velocidade, especialmente com GPU NVIDIA.
* **Extração com LLM Local:** Utiliza um LLM configurado no Ollama (ex: `phi3:medium`) para analisar o texto extraído pelo OCR e estruturá-lo num formato JSON pré-definido.
* **Validação e Edição:** Interface `st.data_editor` para visualizar e corrigir os dados extraídos antes de salvar.
* **Armazenamento em Base de Dados:** Guarda os dados validados numa base de dados MySQL para consulta e análise.
* **Consulta e Exportação:** Pesquise notas fiscais por diversos campos (CNPJ, Razão Social, etc.) e exporte os resultados para CSV ou Excel.
* **Dashboard Financeiro:** Visualizações básicas (Plotly) sobre totais, evolução mensal, top prestadores e categorias.
* **Gestão de Utilizadores:** Sistema de login seguro (`streamlit-authenticator`) com gestão de utilizadores (criar, excluir, forçar alteração de senha) para administradores.
* **Preparado para Fine-Tuning:** Exporta os pares (Texto OCR Bruto, JSON Extraído Bruto) em formato `.jsonl`, pronto para ser corrigido e usado para treinar um modelo LLM extrator mais preciso.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **Interface Web:** Streamlit
* **LLM (Local):** Ollama (com modelos como `phi3`, `llava`, `granite`, etc.)
* **OCR (Opções):**
    * Azure Computer Vision SDK (`azure-cognitiveservices-vision-computervision`, `msrest`)
    * Ollama (com modelos LMM)
    * EasyOCR (+ `torch`, `torchvision`, `torchaudio`)
* **Manipulação de PDF:** PyMuPDF (`fitz`)
* **Base de Dados:** MySQL
* **Interação com BD:** `mysql-connector-python`, `SQLAlchemy`, `PyMySQL`
* **Autenticação:** `streamlit-authenticator`, `bcrypt`
* **Manipulação de Dados:** Pandas
* **Visualização:** Plotly Express (`plotly`)
* **Configuração:** `python-dotenv`
* **Imagens (Leitura base):** Pillow (geralmente instalada como dependência)

## 📚 Bibliotecas Necessárias

Instale as bibliotecas Python listadas abaixo. É **altamente recomendado** usar um ambiente virtual (`venv`).

**Bibliotecas Base:**
```bash
pip install streamlit pandas plotly mysql-connector-python streamlit-authenticator bcrypt python-dotenv sqlalchemy pymysql ollama PyMuPDF Pillow openpyxl xlsxwriter
````

*(Nota: `openpyxl` e `xlsxwriter` são necessários para exportar para Excel)*

**Dependências Específicas de OCR (instale APENAS as que for usar):**

  * **Para Azure Computer Vision (`OCR_METHOD=AZURE`):**

    ```bash
    pip install azure-cognitiveservices-vision-computervision msrest
    ```

  * **Para EasyOCR (`OCR_METHOD=EASYOCR`):**

      * **Com Suporte GPU NVIDIA (Recomendado):**
        ```bash
        # Instale PyTorch com suporte CUDA (ajuste 'cu121' para sua versão CUDA se necessário)
        pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu121](https://download.pytorch.org/whl/cu121)
        pip install easyocr
        ```
      * **Apenas CPU:**
        ```bash
        pip install torch torchvision torchaudio # Pode usar a versão padrão da CPU
        pip install easyocr
        ```
        *(Nota: EasyOCR sem GPU será consideravelmente mais lento)*

  * **Para Ollama LMM (`OCR_METHOD=OLLAMA`):** Nenhuma biblioteca Python extra *além do `ollama`* (já na lista base) é necessária, mas você precisa ter o [Ollama](https://ollama.com/) instalado e a correr no seu sistema, com os modelos LMM desejados (ex: `ollama pull llava-llama3`) já baixados.

## ⚙️ Configuração

1.  **Base de Dados MySQL:** Certifique-se de ter um servidor MySQL a correr e crie uma base de dados para este projeto.

2.  **Ficheiro `.env`:** Crie um ficheiro chamado `.env` na pasta raiz do projeto (`H:\projeto2`) e adicione as seguintes variáveis, substituindo pelos seus valores:

    ```dotenv
    # --- Credenciais do Banco de Dados MySQL ---
    DB_HOST=localhost
    DB_USER=seu_usuario_mysql
    DB_PASSWORD=sua_senha_mysql
    DB_NAME=seu_banco_de_dados_mysql

    # --- Escolha do Método OCR ---
    # Opções válidas: AZURE, OLLAMA, EASYOCR
    # (Se omitido ou inválido, o padrão será AZURE se as credenciais estiverem disponíveis, senão tentará Ollama/EasyOCR se disponíveis)
    OCR_METHOD=AZURE

    # --- Configurações para OCR_METHOD=OLLAMA ---
    # Escolha o modelo LMM que você baixou no Ollama (ex: llava-llama3, granite3.2-vision, llava:13b)
    MODELO_LMM_OCR=llava-llama3

    # --- Credenciais Azure (Necessário APENAS se OCR_METHOD=AZURE) ---
    # Descomente e preencha se for usar Azure e se NÃO estiverem hardcoded no processador.py
    # AZURE_CV_KEY="sua_chave_azure_aqui"
    # AZURE_CV_ENDPOINT="seu_endpoint_azure_aqui"

    # --- (Opcional) Chave Secreta para Cookies de Autenticação ---
    # Gere uma chave aleatória longa (ex: openssl rand -hex 32)
    # AUTH_SECRET_KEY="sua_chave_secreta_aqui"
    ```

      * **Importante:** Verifique o ficheiro `Backend/processador.py` para confirmar se as credenciais Azure estão hardcoded ou se dependem do `.env`. Se dependerem do `.env`, descomente e preencha `AZURE_CV_KEY` e `AZURE_CV_ENDPOINT`.
      * Se `OCR_METHOD` for `OLLAMA`, certifique-se que o `MODELO_LMM_OCR` corresponde a um modelo que você baixou (`ollama pull nome_do_modelo`).
      * Se `OCR_METHOD` for `EASYOCR`, certifique-se que instalou as bibliotecas corretamente.

3.  **Ollama (Se usar OCR\_METHOD=OLLAMA ou para Extração LLM):**

      * Instale o [Ollama](https://ollama.com/) no seu sistema.
      * Baixe os modelos necessários:
        ```bash
        # Modelo para extração JSON (ex: phi3)
        ollama pull phi3:medium

        # Modelo LMM para OCR (se OCR_METHOD=OLLAMA, ex: llava-llama3)
        ollama pull llava-llama3 # Ou o modelo definido em MODELO_LMM_OCR
        ```
      * Certifique-se que o serviço Ollama está a correr antes de iniciar a aplicação Streamlit.

## 🚀 Instalação e Execução

1.  **Clone o Repositório:**
    ```bash
    git clone <url_do_seu_repositorio>
    cd <nome_da_pasta_do_projeto> # Ex: cd projeto2
    ```
2.  **Crie e Ative um Ambiente Virtual (Recomendado):**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/macOS
    source venv/bin/activate
    ```
3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt # (Se você criar um ficheiro requirements.txt com as bibliotecas listadas acima)
    # Ou instale manualmente as bibliotecas necessárias listadas na seção "Bibliotecas"
    ```
4.  **Configure o `.env`:** Crie e preencha o ficheiro `.env` na raiz do projeto, como descrito na seção "Configuração".
5.  **Execute a Aplicação Streamlit:**
      * Certifique-se que o serviço Ollama está a correr (se aplicável).
      * Navegue até à pasta `Frontend`:
        ```bash
        cd Frontend
        ```
      * Execute o Streamlit:
        ```bash
        streamlit run app.py
        ```
6.  **Primeiro Login:** A aplicação criará as tabelas na base de dados automaticamente. O primeiro utilizador pode precisar de ser criado manualmente ou através de um script inicial (não incluído). Utilize as credenciais definidas para fazer login. Se for administrador, poderá criar outros utilizadores na aba "Gerir Utilizadores".

## 📖 Uso

1.  **Login:** Aceda à aplicação e faça login com as suas credenciais.
2.  **Processar Documentos:**
      * Na aba "➕ Processar Documentos", escolha "Upload Manual" para carregar ficheiros individuais ou "Processar Pasta" para indicar um diretório no servidor.
      * Clique no botão "Iniciar Processamento". A aplicação usará o método OCR configurado no `.env` para ler o texto e o LLM local (Ollama) para extrair os dados.
      * Os dados extraídos (brutos) serão exibidos num editor de tabela (`st.data_editor`). Se a extração falhar, a "Resposta Bruta" do LLM será exibida.
      * **Valide e Corrija:** Verifique os dados na tabela e faça as correções necessárias clicando duas vezes nas células.
      * **Salvar:** Clique em "✅ Salvar Dados Limpos na Base de Dados". Os dados serão limpos (formatação de números, datas) e guardados no MySQL.
      * **Cancelar:** Clique em "❌ Cancelar Edição" para descartar os dados extraídos sem salvar.
      * **Baixar Dados para Treino:** Clique em "🧬 Baixar Dados para Treino (.jsonl)" para exportar o texto OCR bruto e o JSON bruto extraído pelo LLM (antes da edição). Este ficheiro é útil para fine-tuning.
3.  **Consultar Dados:**
      * Na aba "🔍 Consultar Dados", utilize a barra de pesquisa para filtrar as notas fiscais por diferentes campos.
      * Visualize os resultados e baixe a consulta em formato CSV.
4.  **Dashboard Financeiro:**
      * A aba "📊 Dashboard Financeiro" apresenta gráficos sobre a evolução mensal, top prestadores, categorias e maiores notas.
5.  **Gerir Utilizadores (Admin):**
      * Se for administrador, a aba "⚙️ Gerir Utilizadores" permite visualizar, criar, excluir e forçar a alteração de senha de outros utilizadores.

## 💡 Opções de OCR: Prós e Contras

  * **`OCR_METHOD=AZURE`**
      * **Prós:** Potencialmente a maior precisão, mantido pela Microsoft, bom com layouts variados.
      * **Contras:** Requer subscrição Azure (custo associado), depende de conexão à internet, pode ser mais lento que EasyOCR devido à latência da rede e processamento na nuvem.
  * **`OCR_METHOD=OLLAMA`**
      * **Prós:** Flexibilidade (pode testar vários modelos LMM locais - Llava, Granite, etc.), processamento totalmente local (privacidade), pode ser bom com imagens complexas onde o contexto ajuda.
      * **Contras:** **Geralmente o mais lento**, consome muitos recursos locais (RAM, VRAM), a precisão depende muito do modelo LMM escolhido (`MODELO_LMM_OCR` no `.env`).
  * **`OCR_METHOD=EASYOCR`**
      * **Prós:** **Geralmente o mais rápido**, especialmente com GPU NVIDIA. Boa precisão para documentos padrão. Processamento local.
      * **Contras:** Pode ter menor precisão que Azure/LMMs em layouts muito complexos, texto degradado ou manuscrito (menos relevante para NFS-e). A instalação do PyTorch com CUDA pode ser complexa.

## 🚀 Melhorias Futuras (Fine-Tuning)

A precisão da *extração* (transformar texto OCR em JSON) pode ser significativamente melhorada através do **fine-tuning** de um modelo LLM (como `phi3:mini` ou `phi3:medium`).

1.  Processe um lote de documentos usando a aplicação.
2.  Clique em "🧬 Baixar Dados para Treino (.jsonl)".
3.  **Manualmente, corrija** o campo `"completion"` (que contém o JSON bruto extraído) em cada linha do ficheiro `.jsonl` para que fique 100% correto.
4.  Use este ficheiro `.jsonl` corrigido para fazer o fine-tuning de um modelo LLM (usando ferramentas como `unsloth`, `axolotl`, `LLaMA Factory`, etc.).
5.  Importe o seu modelo treinado para o Ollama (ex: `ollama create meu_extrator_nfse -f SeuModelfile`).
6.  Atualize a variável `modelo_usado` no ficheiro `Backend/processador.py` para usar o nome do seu modelo treinado (ex: `modelo_usado = 'meu_extrator_nfse:latest'`).
