---

# 🤖 Extrator e Gestor Inteligente de Notas Fiscais com IA Local

Este projeto foi desenvolvido para a disciplina de **PROJETO EM COMPUTAÇÃO APLICADA** da **UNINOVE (Universidade Nove de Julho)**, sob orientação do **Prof. Luis Carlos dos Santos Junior**.

## 📘 Visão Geral

O **Extrator Inteligente de Notas Fiscais** é uma aplicação web completa, desenvolvida em **Python com Streamlit**, que automatiza o processo de extração de dados de documentos fiscais (NFS-e).
A solução utiliza um modelo de **linguagem e visão (multimodal)** rodando **100% localmente com Ollama** para analisar imagens e PDFs, extrair informações estruturadas e armazená-las numa base de dados **MySQL** para análise e gestão financeira.

A aplicação conta com um **sistema de autenticação robusto**, gestão de utilizadores com diferentes níveis de permissão e um **dashboard financeiro interativo** para visualização de métricas e tendências.

---

## 🧱 Arquitetura do Projeto

O projeto é modularizado numa estrutura **Frontend** e **Backend** para uma melhor organização e manutenção:

* **Frontend/**: Construído com **Streamlit**, contém toda a lógica da interface do utilizador, dashboards e interação.
* **Backend/**: O "motor" da aplicação, responsável por:

  * **Processamento de IA**: Comunicação com o Ollama para usar o modelo **LLaVA** na extração de dados.
  * **Gestão da Base de Dados**: Interação com **MySQL** para armazenar e consultar notas fiscais e utilizadores.
  * **Gestão de Autenticação**: Lógica de login, perfis e permissões.

---

## ⚙️ Funcionalidades Principais

### 🔍 Extração de Dados com IA

* **Processamento Multimodal:** Lê ficheiros de imagem (.png, .jpg) e PDFs.
* **IA 100% Local:** Utiliza o modelo **LLaVA** via **Ollama**, garantindo privacidade e custo zero.
* **Sugestão de Categoria:** A IA sugere uma categoria de despesa com base na descrição dos serviços.

### 🗄️ Base de Dados e Persistência

* **Backend MySQL:** Todos os dados são guardados numa base de dados MySQL.
* **Prevenção de Duplicatas:** Cada ficheiro tem um hash MD5 único, impedindo reprocessamento.

### 🔐 Sistema de Autenticação e Gestão de Utilizadores

* **Login Seguro:** Sistema de autenticação protegido com hash **bcrypt**.
* **Níveis de Permissão:**

  * **Utilizador Padrão:** Processa documentos e visualiza dados.
  * **Administrador:** Gere utilizadores, permissões e o sistema.
* **Painel de Administrador:**

  * Visualização e exportação de utilizadores.
  * Criação e eliminação de contas.
  * Forçar alteração de senha.
* **Gestão de Perfil:**

  * Alteração de senha no primeiro login e a qualquer momento.

### 📊 Interface e Análise Financeira

* **Upload Flexível:** Suporta múltiplos ficheiros ou pastas inteiras.
* **Validação de Dados:** Tabela editável antes do armazenamento definitivo.
* **Consulta Avançada:** Busca por CNPJ, Razão Social ou Número da Nota.
* **Dashboard Interativo:**

  * Métricas gerais (Valor Total, ISS, Carga Tributária).
  * Gráficos de evolução mensal e categorias.
  * Top 5 fornecedores.

---

## 🧠 Tecnologias Utilizadas

* **Linguagem:** Python 3.8+
* **Interface:** Streamlit
* **IA Local:** Ollama + Modelo LLaVA (13b)
* **Base de Dados:** MySQL
* **Conexão BD:** SQLAlchemy e mysql-connector-python
* **Manipulação de Dados:** Pandas
* **Autenticação:** Streamlit Authenticator + Bcrypt
* **Visualização:** Plotly e Streamlit Charts

---

## 🧩 Dependências



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



## 🚀 Como Executar

### 1️⃣ Pré-requisitos

* **Python 3.8+** → [https://www.python.org](https://www.python.org)
* **Ollama** → [https://ollama.com](https://ollama.com)
* **Modelo LLaVA** → Após instalar o Ollama, execute:

  ```bash
  ollama pull llava:13b
  ```
* **Servidor MySQL** (local ou remoto).

---

### 2️⃣ Configuração do Projeto

Clone o repositório:

```bash
git clone https://github.com/Kelvinsantosyz/extrator-nfse-ollama.git
cd extrator-nfse-ollama
```

Crie e ative o ambiente virtual:

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie o ficheiro `.env` na raiz:

```env
DB_HOST=localhost
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=nfse_db
```

Crie o primeiro utilizador administrador:

```bash
python create_admin.py
```

---

### 3️⃣ Execução

Certifique-se de que **Ollama** e **MySQL** estão em execução, depois rode:

```bash
streamlit run Frontend/app.py
```

A aplicação abrirá automaticamente no navegador.
Faça login com o utilizador administrador criado.

---
