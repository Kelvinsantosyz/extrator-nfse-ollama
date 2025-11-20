# 🤖 Extrator Inteligente de NFS-e com OCR e LLM

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql)
![Ollama](https://img.shields.io/badge/AI-Ollama-black?style=for-the-badge)

Este projeto utiliza tecnologias de **Reconhecimento Óptico de Caracteres (OCR)** e **Modelos de Linguagem Grandes (LLMs)** — locais (via Ollama) ou na nuvem (Azure) — para extrair dados estruturados de Notas Fiscais de Serviço eletrônicas (NFS-e) brasileiras, armazenando-os numa base de dados MySQL.

Uma interface web intuitiva, construída com Streamlit, permite o upload, processamento, visualização, edição e gestão completa dos dados e utilizadores.

---

> [!IMPORTANT]
> **Nota Sobre Precisão**
>
> Nenhum sistema de OCR ou LLM é 100% perfeito. A precisão depende da qualidade do documento e do layout.
> * **OCR:** Pode confundir caracteres (ex: "5" com "S").
> * **LLM:** Pode alucinar campos ou gerar JSON inválido se o texto base for ruim.
>
> **A validação humana é indispensável.** Utilize a interface de edição do sistema para conferir os dados antes de salvá-los.

---

## 🎬 Demonstração

Clique nas imagens abaixo para assistir aos vídeos de demonstração:

| Demonstração do Software | Apresentação do Projeto |
| :---: | :---: |
| [![Demonstração](https://img.youtube.com/vi/nK4gICMGSW0/0.jpg)](https://www.youtube.com/watch?v=nK4gICMGSW0) | [![Apresentação](https://img.youtube.com/vi/prbXoetvZEo/0.jpg)](https://youtu.be/prbXoetvZEo?si=IY6x6sCBYeFALBuQ) |

---

## ✨ Funcionalidades

* 📂 **Upload Flexível:** Suporte para PDF, PNG, JPG, JPEG e WEBP (ficheiros individuais ou processamento em lote/pasta).
* 🧠 **OCR Híbrido:** Escolha entre a precisão da nuvem ou a privacidade local:
    * **Azure Computer Vision:** Alta precisão (Nuvem).
    * **EasyOCR:** Alta velocidade (Local).
    * **Ollama LMM:** Multimodalidade (Local).
* 🤖 **Extração Inteligente:** Uso de LLMs (ex: `phi3`) para estruturar dados brutos em JSON.
* ✏️ **Validação Interativa:** Interface `st.data_editor` para correção manual antes da persistência.
* 🗄️ **Banco de Dados:** Armazenamento seguro em MySQL.
* 📊 **Dashboard & Exportação:** Gráficos financeiros e exportação para CSV/Excel.
* 🔐 **Segurança:** Sistema de login e gestão de utilizadores (Admin).
* 🎓 **Preparado para Fine-Tuning:** Exportação de dataset `.jsonl` para treino de modelos futuros.

---

## 🛠️ Arquitetura e Tecnologias



* **Core:** Python 3.10+
* **Frontend:** Streamlit, Plotly Express.
* **AI & OCR:** Ollama, Azure Computer Vision SDK, EasyOCR (PyTorch).
* **Dados:** MySQL, SQLAlchemy, Pandas.
* **Segurança:** Bcrypt, Streamlit-Authenticator.
* **Utilitários:** PyMuPDF (PDFs), Pillow (Imagens), Python-dotenv.

---

## 🚀 Instalação

### 1. Pré-requisitos
Antes de começar, certifique-se de ter instalado:
* **Python 3.10+**
* **MySQL Server** (com uma base de dados criada)
* **Ollama** (Se for utilizar processamento local)

### 2. Clone e Ambiente Virtual

```bash
git clone <url_do_seu_repositorio>
cd projeto-nfse

# Criação do ambiente virtual
python -m venv venv

# Ativar (Windows)
.\venv\Scripts\activate
# Ativar (Linux/macOS)
source venv/bin/activate
