# Extrator de Dados de Notas Fiscais com IA Local (Ollama)

*Este projeto está sendo desenvolvido para a disciplina de **PROJETO EM COMPUTAÇÃO APLICADA** da **UNINOVE (Universidade Nove de Julho)**, sob orientação do **Prof. Luis Carlos dos Santos Junior.***

---

Este projeto utiliza um modelo de linguagem e visão (multimodal) rodando localmente com Ollama para extrair informações de imagens de Notas Fiscais de Serviço Eletrônicas (NFS-e) e salvá-las em uma planilha Excel.

## Funcionalidades

-   **Processamento de Imagens e PDFs**: Lê arquivos nos formatos `.png`, `.jpg`, `.jpeg`.
-   **Extração com IA Multimodal**: Usa o modelo LLaVA para "ver" e "ler" os documentos, extraindo dados diretamente da imagem com alta precisão.
-   **Operação 100% Local**: Nenhuma chamada a APIs externas. Todos os dados permanecem na sua máquina, garantindo total privacidade.
-   **Prevenção de Duplicatas**: Calcula um hash MD5 para cada arquivo para evitar que o mesmo documento seja processado mais de uma vez.
-   **Limpeza de Dados**: Formata valores monetários e datas para um padrão consistente.
-   **Saída Estruturada**: Salva todos os dados extraídos em uma planilha Excel (`.xlsx`) bem organizada.

## Como Usar

Siga os passos abaixo para configurar e executar o projeto.

### 1. Pré-requisitos

Você precisará ter o Python, o Ollama e o modelo LLaVA instalados no seu computador.

-   **Python 3.8+**: [python.org](https://www.python.org/downloads/)
-   **Ollama**: Siga as instruções de instalação em [ollama.com](https://ollama.com/).
-   **Modelo LLaVA**: Após instalar o Ollama, abra um terminal e execute o seguinte comando para baixar o modelo (pode levar um tempo e exige um bom computador):
    ```bash
    ollama pull llava:13b
    ```

### 2. Configuração do Projeto

1.  **Clone ou baixe este repositório.**
2.  **Crie a estrutura de pastas** na raiz do projeto:
    ```
    /projeto-extrator-nf/
    |
    +--- /Documentos/
    |    +--- nota_fiscal_01.png
    |    +--- nota_fiscal_02.jpg
    |
    +--- /Planilha/
    |    (aqui será criada a planilha de resultados)
    |
    +--- leitor.py
    +--- requirements.txt
    ```
3.  **Crie um ambiente virtual** (recomendado):
    ```bash
    python -m venv venv
    ```
4.  **Ative o ambiente virtual**:
    -   No Windows: `.\venv\Scripts\Activate.ps1`
    -   No macOS/Linux: `source venv/bin/activate`
5.  **Instale as bibliotecas Python** necessárias com o `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Execução

1.  **Coloque os arquivos** de imagem das suas notas fiscais na pasta `Documentos`.
2.  **Execute o script** a partir do seu terminal (com o ambiente virtual ativado):
    ```bash
    python leitor.py
    ```
3.  **Verifique o resultado**: Após a execução, uma planilha chamada `planilha de dados.xlsx` será criada ou atualizada na pasta `Planilha` com todos os dados extraídos.

## Personalização

-   **Caminhos de Pasta**: Você pode alterar os caminhos de `PASTA_DOCUMENTOS` e `PASTA_PLANILHA` diretamente no topo do arquivo `leitor.py`.
-   **Prompt da IA**: A lógica de extração é controlada pelo `prompt` dentro da função `processar_documento_com_llm_local`. Você pode ajustar este prompt para extrair outros campos ou lidar com layouts de nota fiscal diferentes.