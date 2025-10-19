<<<<<<< HEAD
🤖 Extrator e Gestor Inteligente de Notas Fiscais com IA Local
=======
# 🤖 Extrator Inteligente de Notas Fiscais com IA Local e Streamlit
>>>>>>> e79d654dd563fd1f74cfaa485b754e2adb361f76

Este projeto foi desenvolvido para a disciplina de PROJETO EM COMPUTAÇÃO APLICADA da UNINOVE (Universidade Nove de Julho), sob orientação do Prof. Luis Carlos dos Santos Junior.

Visão Geral

O Extrator Inteligente de Notas Fiscais é uma aplicação web completa, desenvolvida em Python com Streamlit, que automatiza o processo de extração de dados de documentos fiscais (NFS-e). A solução utiliza um modelo de linguagem e visão (multimodal) rodando 100% localmente com Ollama para analisar imagens e PDFs, extrair informações estruturadas e persisti-las numa base de dados MySQL para análise e gestão financeira.

<<<<<<< HEAD
A aplicação conta com um sistema de autenticação robusto, gestão de utilizadores com diferentes níveis de permissão e um dashboard financeiro interativo para a visualização de métricas e tendências.

Arquitetura do Projeto
=======
Este projeto é uma aplicação web completa, construída com **Streamlit**, que utiliza um **modelo de linguagem e visão (multimodal)** rodando **localmente com Ollama** para extrair, validar e analisar informações de **Notas Fiscais de Serviço Eletrônicas (NFS-e)**.

A ferramenta transforma o processo manual de entrada de dados em um fluxo de trabalho **inteligente, automatizado e interativo**.

💡 A aplicação é **100% local**, garantindo que **nenhum dado sensível** seja enviado para APIs externas, oferecendo **total privacidade e segurança**.

---
>>>>>>> e79d654dd563fd1f74cfaa485b754e2adb361f76

O projeto é modularizado numa estrutura Frontend e Backend para uma melhor organização e manutenibilidade:

<<<<<<< HEAD
Frontend/: Construído com Streamlit, contém toda a lógica da interface do utilizador, dashboards e interação.

Backend/: O "motor" da aplicação, responsável por:

Processamento de IA: Comunica com o Ollama para usar o modelo LLaVA na extração de dados.

Gestão da Base de Dados: Interage com a base de dados MySQL para armazenar e consultar notas fiscais e utilizadores.
=======
A aplicação vai muito além de um simples script, oferecendo um ambiente completo para **gerenciamento e análise de NFS-e**:

* **Interface Web Interativa**
  Interface amigável construída com Streamlit, organizada em abas para diferentes tarefas.

* **Motor de Extração Híbrido**

  * Utiliza o modelo multimodal **LLaVA** para “ler” e extrair dados estruturados de imagens e PDFs.
  * Sistema de **fallback com OCR (Tesseract)** garante a extração de texto mesmo quando a IA não reconhece corretamente.

* **Múltiplos Métodos de Entrada**

  * 📂 **Upload Manual**: Envie múltiplos arquivos (`.png`, `.jpg`, `.pdf`) de uma só vez.
  * 🗂️ **Processamento em Lote**: Analisa automaticamente todos os documentos dentro de uma pasta no servidor.

* **Validação Humana no Fluxo (Human-in-the-loop)**

  * Exibe os dados extraídos em uma **tabela editável** (`st.data_editor`) antes do salvamento, permitindo correções manuais.

* **Dashboard para Análise de Dados**

  * Aba dedicada com **gráficos e métricas interativas**.
  * **Gráfico de Pizza Interativo** (Plotly) mostrando distribuição por estado (UF).
  * **Filtros Dinâmicos** por mês e ano para análise temporal.

* **Consulta e Pesquisa**

  * Pesquise em toda a base de dados com **filtros por qualquer termo**.
  * Exibe **métricas e KPIs** como total de notas e valores acumulados.

* **Gerenciamento de Dados Robusto**

  * 🚫 **Prevenção de Duplicatas**: Identifica arquivos duplicados por **hash MD5**.
  * ✅ **Integridade de Dados**: Garante que não haja entradas repetidas na planilha final.
  * 💾 **Exportação Flexível**: Baixe os dados validados em **Excel (.xlsx)** ou **CSV**.

---

## 🛠️ Tecnologias Utilizadas
---

| Biblioteca                | Principal Uso                                                                 |
| ------------------------- | ----------------------------------------------------------------------------- |
| `streamlit`               | Criação da interface web e dashboards interativos                             |
| `pandas`                  | Manipulação, filtragem e agregação de dados                                   |
| `ollama`                  | Execução local do modelo de linguagem multimodal (LLaVA)                      |
| `pytesseract`             | OCR para fallback em caso de falha do modelo                                  |
| `PyMuPDF`                 | Extração de texto de arquivos PDF                                             |
| `Pillow`                  | Manipulação de imagens para OCR                                               |
| `plotly`                  | Geração de gráficos interativos                                               |
| `openpyxl`, `xlsxwriter`  | Leitura e escrita de planilhas Excel (.xlsx)                                  |
| `mysql-connector-python`  | Conexão e comunicação com o banco de dados MySQL                              |
| `python-dotenv`           | Leitura de variáveis de ambiente a partir do arquivo `.env`                   |
| `streamlit_authenticator` | Sistema de autenticação seguro com login, permissões e gestão de utilizadores |

---

Quer que eu integre essa tabela no seu **README final** na seção de “🧩 Dependências”?

>>>>>>> e79d654dd563fd1f74cfaa485b754e2adb361f76

Gestão de Autenticação: Lida com a lógica de login e permissões.

<<<<<<< HEAD
Funcionalidades Principais

Extração de Dados com IA

Processamento Multimodal: Lê ficheiros de imagem (.png, .jpg) e PDFs diretamente.

IA 100% Local: Utiliza o modelo LLaVA através do Ollama, garantindo total privacidade e zero custos de API.

Sugestão de Categoria: A IA sugere uma categoria de despesa com base na descrição dos serviços.

Base de Dados e Persistência

Backend MySQL: Todos os dados são armazenados numa base de dados MySQL, garantindo escalabilidade e rapidez nas consultas.

Prevenção de Duplicatas: Utiliza um hash MD5 para cada ficheiro, impedindo que o mesmo documento seja processado múltiplas vezes.

Sistema de Autenticação e Gestão de Utilizadores

Tela de Login Segura: O acesso à aplicação é protegido por um sistema de login.
=======
Siga os passos abaixo para configurar e executar a aplicação corretamente.

### 1️⃣ Pré-requisitos

* **Python 3.8+** → [python.org](https://www.python.org/downloads/)
* **Ollama** → [ollama.com](https://ollama.com/)
* **Google Tesseract OCR** → [Instruções de instalação](https://github.com/tesseract-ocr/tessdoc/blob/main/Installation.md)

Após instalar o Ollama, baixe o modelo multimodal:

```bash
# Você pode escolher um modelo menor (ex: llava:7b) se preferir desempenho
ollama pull llava:13b
```

> ⚠️ Lembre-se de adicionar o Tesseract à variável de ambiente **PATH** no Windows.

---

### 2️⃣ Configuração do Projeto

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/Kelvinsantosyz/extrator-nfse-ollama.git
   cd extrator-nfse-ollama
   ```

2. **Crie e ative um ambiente virtual:**

   ```bash
   python -m venv venv
   # Ativar no Windows (PowerShell)
   .\venv\Scripts\Activate.ps1
   # ou no Linux/Mac
   source venv/bin/activate
   ```

3. **Instale as dependências:**

   ```bash
   python -m pip install -r requirements.txt
   ```

4. **Crie as pastas necessárias (se não existirem):**

   ```bash
   mkdir Documentos Planilha
   ```

   * `Documentos/` → pasta usada para o processamento em lote
   * `Planilha/` → onde o Excel será salvo

---

### 3️⃣ Execução

Inicie o aplicativo a partir do terminal (com o ambiente virtual ativo):

```bash
python -m streamlit run app.py
```

O Streamlit abrirá automaticamente uma aba no navegador com a aplicação em execução.

---
>>>>>>> e79d654dd563fd1f74cfaa485b754e2adb361f76

Palavras-passe Criptografadas: As palavras-passe são armazenadas de forma segura na base de dados usando hash bcrypt.

<<<<<<< HEAD
Níveis de Permissão:

Utilizador Padrão: Pode processar documentos e visualizar os dados.

Administrador: Tem acesso a um painel exclusivo para gerir o sistema.

Painel de Administrador:

Visualização de todos os utilizadores registados.

Criação de novos utilizadores (padrão ou administradores).

Opção para forçar a alteração de palavra-passe de um utilizador.

Eliminação de contas de utilizador.

Exportação da lista de utilizadores para CSV.

Gestão de Perfil:

Os utilizadores são forçados a alterar a palavra-passe no primeiro login.

Qualquer utilizador pode alterar a sua própria palavra-passe a qualquer momento através do seu perfil.

Interface e Análise Financeira

Upload Flexível: Permite o envio de múltiplos ficheiros ou o processamento de uma pasta inteira no servidor.

Validação de Dados: Exibe os dados extraídos numa tabela editável antes de os salvar permanentemente, permitindo correções manuais.

Consulta e Filtro Avançados: Uma aba dedicada para pesquisar na base de dados por CNPJ, Razão Social ou Número da Nota, com resumo financeiro dos resultados filtrados.

Dashboard Financeiro Interativo:

Métricas gerais (Valor Total, Total de ISS, Carga Tributária Média).

Gráfico de evolução mensal de despesas e impostos.

Gráfico com o Top 5 de fornecedores (prestadores).

Gráfico de pizza com a distribuição de despesas por categoria.

Tecnologias Utilizadas

Linguagem: Python 3.8+

Interface: Streamlit

Processamento de IA: Ollama com o modelo LLaVA (13b)

Base de Dados: MySQL

Conexão com a BD: SQLAlchemy e mysql-connector-python

Manipulação de Dados: Pandas

Autenticação: Streamlit-Authenticator e Bcrypt

Como Executar

Siga os passos abaixo para configurar e executar o projeto.

1. Pré-requisitos

Python 3.8+: python.org

Ollama: ollama.com

Modelo LLaVA: Após instalar o Ollama, execute no terminal: ollama pull llava:13b

Servidor MySQL: Tenha um servidor MySQL em execução (local ou remoto).

2. Configuração do Projeto

Clone o repositório:

git clone [https://github.com/Kelvinsantosyz/extrator-nfse-ollama.git](https://github.com/Kelvinsantosyz/extrator-nfse-ollama.git)
cd extrator-nfse-ollama


Crie e ative um ambiente virtual:

python -m venv venv
.\venv\Scripts\Activate.ps1


Instale as dependências:

pip install -r requirements.txt


Configure as credenciais:

Crie um ficheiro chamado .env na raiz do projeto.

Preencha-o com as suas credenciais da base de dados:

DB_HOST=localhost
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=nfse_db


Crie o primeiro utilizador administrador:

Execute o script de configuração a partir da raiz do projeto:

python create_admin.py


Siga as instruções no terminal para criar a sua conta de administrador.

3. Execução

Certifique-se de que o Ollama e o seu servidor MySQL estão em execução.

A partir da raiz do projeto, execute o comando:

streamlit run Frontend/app.py


A aplicação será aberta automaticamente no seu navegador. Faça login com o utilizador administrador que acabou de criar.
=======
**Kelvin Santos**
📧 [kelvinsantosyz@gmail.com](mailto:kelvinsantosyz@gmail.com)
💻 [GitHub](https://github.com/Kelvinsantosyz) • [LinkedIn](https://www.linkedin.com/in/kelvin-felipe-dos-santos/)

---

## 🏫 Créditos

Universidade Nove de Julho – **UNINOVE**
Orientador: **Prof. Luis Carlos dos Santos Junior**

---

## ⚖️ Licença

Este projeto está licenciado sob a **MIT License** — veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---
>>>>>>> e79d654dd563fd1f74cfaa485b754e2adb361f76
