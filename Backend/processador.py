import os
import json
import hashlib
import re # Importa a biblioteca de expressões regulares
import base64
import io
from datetime import datetime
from typing import Dict, Any
import time # Para Azure OCR
from dotenv import load_dotenv # Mantido para credenciais DB, se necessário
import traceback # Para depuração de erros

# Carrega as variáveis de ambiente do ficheiro .env na raiz do projeto
# Necessário se outras partes do backend usarem .env (ex: database.py)
load_dotenv()

# --- Bibliotecas de Extração ---
import ollama
import fitz # PyMuPDF para PDFs

# --- Bibliotecas Azure ---
try:
    from azure.cognitiveservices.vision.computervision import ComputerVisionClient
    from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
    from msrest.authentication import CognitiveServicesCredentials
    from msrest.exceptions import HttpOperationError # Para capturar erros HTTP do Azure
    AZURE_AVAILABLE = True
    print("Bibliotecas Azure Computer Vision carregadas com sucesso.")
except ImportError:
    print("AVISO: Bibliotecas Azure não encontradas. O processamento com Azure OCR falhará.")
    print("Instale com: pip install azure-cognitiveservices-vision-computervision msrest")
    AZURE_AVAILABLE = False

# --- Configurações Azure (Hardcoded) --- # <-- MODIFICADO
AZURE_SUBSCRIPTION_KEY = "" # Sua chave (direto no código)
AZURE_ENDPOINT = "" # Seu endpoint (direto no código)

# --- Validação das credenciais Azure (Simplificada) ---
if AZURE_AVAILABLE:
    if not AZURE_SUBSCRIPTION_KEY or not AZURE_ENDPOINT:
        print("="*50)
        print("ERRO CRÍTICO: Credenciais Azure (AZURE_SUBSCRIPTION_KEY ou AZURE_ENDPOINT) não estão definidas diretamente no código!")
        print("O OCR com Azure não funcionará.")
        print("="*50)
        AZURE_AVAILABLE = False
    elif not AZURE_ENDPOINT.lower().startswith("https://"):
         print("="*50)
         print(f"AVISO: Endpoint Azure '{AZURE_ENDPOINT}' não parece começar com 'https://'. Verifique o valor definido no código.")
         print("="*50)
    else:
        print("Credenciais Azure definidas diretamente no código.")
# --- Fim Validação ---


# --- Mantido: EasyOCR (Opcional, não usado) ---
try:
    import easyocr
    EASYOCR_READER = easyocr.Reader(['pt', 'en'], gpu=True)
    EASYOCR_AVAILABLE_BACKUP = True
except ImportError:
    EASYOCR_AVAILABLE_BACKUP = False
    EASYOCR_READER = None
except Exception as e:
    # print(f"AVISO: Falha ao carregar EasyOCR (Backup). Erro: {e}") # Comentado
    EASYOCR_AVAILABLE_BACKUP = False
    EASYOCR_READER = None
# --- FIM EasyOCR ---


# ==============================================================================
# FUNÇÃO DE EXTRAÇÃO DE TEXTO (AZURE COMPUTER VISION) COM MELHOR ERROR HANDLING
# ==============================================================================
def extrair_texto_com_azure(filepath: str) -> str:
    """
    Extrai texto bruto de um ficheiro (imagem ou PDF) usando Azure Computer Vision OCR.
    """
    # Verifica disponibilidade e credenciais carregadas
    if not AZURE_AVAILABLE or not AZURE_SUBSCRIPTION_KEY or not AZURE_ENDPOINT:
        print("    [AZURE OCR] ERRO: Bibliotecas Azure não disponíveis ou credenciais não configuradas no código.")
        return ""

    filename = os.path.basename(filepath)
    file_extension = os.path.splitext(filename)[1].lower()
    texto_extraido_total = ""
    computervision_client = None # Inicializa como None

    print(f"    [AZURE OCR] Tentando extrair texto de '{filename}'...")

    try:
        # Inicializa o cliente Azure com credenciais hardcoded
        print(f"    [AZURE OCR] Inicializando cliente com Endpoint: {AZURE_ENDPOINT[:20]}...")
        computervision_client = ComputerVisionClient(AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_SUBSCRIPTION_KEY))
        print(f"    [AZURE OCR] Cliente inicializado.")

        results_list = [] # Para armazenar respostas (contêm headers)

        # --- Processamento ---
        if file_extension in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]:
            try:
                with open(filepath, "rb") as image_stream:
                    print(f"    [AZURE OCR] Enviando imagem '{filename}' para read_in_stream...")
                    read_response = computervision_client.read_in_stream(image_stream, raw=True)
                    results_list.append(read_response)
                    print(f"    [AZURE OCR] Chamada read_in_stream enviada para imagem.")
            except HttpOperationError as http_err: # Erro específico da chamada HTTP
                 print(f"    [AZURE OCR] ERRO HTTP ao enviar imagem '{filename}': Status={http_err.response.status_code}, Resposta={http_err.response.text}")
                 return ""
            except Exception as e:
                 print(f"    [AZURE OCR] Erro ao ler/enviar stream da imagem '{filename}': {e}")
                 traceback.print_exc() # Imprime traceback completo
                 return ""

        elif file_extension == ".pdf":
            try:
                print(f"    [AZURE OCR] Processando PDF '{filename}' página por página...")
                with fitz.open(filepath) as doc:
                    if len(doc) == 0:
                        print(f"    [AZURE OCR] PDF '{filename}' está vazio.")
                        return ""
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        pix = page.get_pixmap(dpi=300) # Mantido DPI alto
                        img_bytes = pix.tobytes("png")

                        with io.BytesIO(img_bytes) as image_page_stream:
                            print(f"    [AZURE OCR] Enviando página {page_num + 1}/{len(doc)} do PDF '{filename}'...")
                            try:
                                read_response = computervision_client.read_in_stream(image_page_stream, raw=True)
                                results_list.append(read_response)
                                print(f"    [AZURE OCR] Chamada read_in_stream enviada para página {page_num + 1}.")
                            except HttpOperationError as http_err:
                                print(f"    [AZURE OCR] ERRO HTTP ao enviar página {page_num + 1} do PDF '{filename}': Status={http_err.response.status_code}, Resposta={http_err.response.text}")
                                continue # Continua para a próxima página por padrão
                            except Exception as e:
                                 print(f"    [AZURE OCR] Erro ao ler/enviar stream da página {page_num + 1} do PDF '{filename}': {e}")
                                 traceback.print_exc()
                                 continue # Continua para a próxima página por padrão
            except Exception as e:
                 print(f"    [AZURE OCR] Erro ao abrir ou processar páginas do PDF '{filename}': {e}")
                 traceback.print_exc()
                 return ""
        else:
            print(f"    [AZURE OCR] Tipo de ficheiro não suportado: '{filename}'")
            return ""

        # --- Obter Resultados (Polling) ---
        if not results_list:
             print(f"    [AZURE OCR] Nenhuma operação iniciada com sucesso para '{filename}'.")
             return ""

        for i, read_response in enumerate(results_list):
            operation_id = None # Reseta para cada operação
            try:
                operation_location_header = read_response.headers.get("Operation-Location")
                if not operation_location_header:
                    print(f"    [AZURE OCR] Falha ao obter Operation-Location para a operação {i+1} de '{filename}'. Pulando.")
                    continue
                operation_id = operation_location_header.split("/")[-1]

                print(f"    [AZURE OCR] Aguardando resultado da operação {i+1} (ID: {operation_id[:6]}...) para '{filename}'...")

                max_retries = 15 # Tenta por ~15 segundos
                retry_count = 0
                while True:
                    retry_count += 1
                    if retry_count > max_retries:
                        print(f"    [AZURE OCR] Tempo limite excedido ao aguardar resultado da operação {i+1} (ID: {operation_id[:6]}).")
                        read_result = None # Define como None para indicar falha
                        break # Sai do loop while

                    try:
                        read_result = computervision_client.get_read_result(operation_id)
                        if read_result.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:
                            break # Sai se concluído (sucesso ou falha)
                        time.sleep(1) # Espera 1 segundo
                    except HttpOperationError as http_err_poll:
                         print(f"    [AZURE OCR] ERRO HTTP (tentativa {retry_count}/{max_retries}) ao verificar status da operação {i+1} (ID: {operation_id[:6]}): Status={http_err_poll.response.status_code}, Resposta={http_err_poll.response.text}")
                         if 400 <= http_err_poll.response.status_code < 500:
                              print(f"    [AZURE OCR] Erro cliente ({http_err_poll.response.status_code}). Desistindo da operação {i+1}.")
                              read_result = None # Indica falha
                              break
                         time.sleep(retry_count) # Backoff simples
                    except Exception as poll_e:
                        print(f"    [AZURE OCR] Erro inesperado (tentativa {retry_count}/{max_retries}) ao verificar status da operação {i+1} (ID: {operation_id[:6]}): {poll_e}")
                        traceback.print_exc()
                        read_result = None # Indica falha
                        break # Sai do loop while

                # Processa o resultado final
                if read_result and read_result.status == OperationStatusCodes.succeeded:
                    print(f"    [AZURE OCR] Operação {i+1} bem-sucedida para '{filename}'. Extraindo texto...")
                    if read_result.analyze_result and read_result.analyze_result.read_results:
                        for text_result in read_result.analyze_result.read_results:
                            if text_result.lines:
                                for line in text_result.lines:
                                    if line.text:
                                        texto_extraido_total += line.text + "\n"
                    else: print(f"    [AZURE OCR] Operação {i+1} sucedeu, mas não retornou resultados analisáveis.")
                elif read_result:
                    print(f"    [AZURE OCR] Falha na operação {i+1} para '{filename}'. Status: {read_result.status}")
                    if hasattr(read_result, 'error') and read_result.error: print(f"      Erro Azure: Code={read_result.error.code}, Message={read_result.error.message}")
                    else: print("      Erro Azure: Detalhes do erro não disponíveis no resultado.")
                # Se read_result for None, o erro já foi logado

            except Exception as e:
                print(f"    [AZURE OCR] Erro ao obter/processar resultado da operação {i+1} (ID: {operation_id[:6] if operation_id else 'N/A'}) para '{filename}': {e}")
                traceback.print_exc()

    except Exception as e:
        print(f"    [AZURE OCR] ERRO GERAL INESPERADO durante a extração para '{filename}': {e}.")
        traceback.print_exc()
        return ""

    print(f"    [AZURE OCR] Extração concluída para '{filename}'. Caracteres totais: {len(texto_extraido_total)}")
    texto_extraido_total = '\n'.join([line for line in texto_extraido_total.splitlines() if line.strip()])
    return texto_extraido_total


# ==============================================================================
# FUNÇÃO PRINCIPAL DE PROCESSAMENTO (LLM) - AGORA USA AZURE OCR
# ==============================================================================
def processar_documento_com_llm_local(filepath: str) -> Dict[str, Any]:
    """
    Processa um documento:
    1. Extrai texto usando Azure Computer Vision OCR.
    2. Envia o texto extraído para o modelo LLM (Ollama) para estruturação em JSON.
    3. RETORNA um dicionário com o texto bruto e o JSON bruto para fine-tuning.
    """
    filename = os.path.basename(filepath)

    # 1. Extrai o texto usando a nova função Azure OCR
    print(f"    [FLUXO] Iniciando extração de texto com Azure OCR para '{filename}'...")
    texto_bruto = extrair_texto_com_azure(filepath)

    dados_extraidos = {}
    resposta_llm = ""

    # 2. Se a extração de texto foi bem-sucedida, envia para LLM (Ollama)
    if texto_bruto and len(texto_bruto) > 10:

        # Modelo LLM para Extração JSON (mantido como Ollama)
        modelo_usado = 'phi3:medium' # Ou seu modelo fine-tuned: 'meu_extrator_nfse:latest'

        print(f"    [{modelo_usado.upper()}] Enviando texto extraído (Azure) de '{filename}' para o modelo '{modelo_usado}'...")

        # ---> PROMPT REFINADO (v5) <---
        prompt_texto = f"""
        Você é um sistema especialista em extrair informações de Notas Fiscais de Serviço brasileiras (NFS-e) a partir de texto OCRizado.
        Sua única tarefa é retornar **estritamente e somente** um objeto JSON válido contendo os campos listados abaixo.
        **NÃO adicione nenhum texto introdutório, explicações, comentários, nem mesmo ```json antes ou depois do objeto JSON.** A saída deve ser apenas o JSON completo e nada mais.

        Analise o texto OCR da nota fiscal abaixo. Ignore erros de OCR e textos grandes que sejam claramente marcas d'água (ex: 'EXEMPLO', 'SEM VALOR FISCAL').
        Preencha cada campo do formato JSON abaixo com o valor correspondente encontrado no texto.
        Se um campo **não for encontrado** no texto OCR, use uma string vazia ("") como valor para esse campo no JSON.
        Preste **muita atenção** para diferenciar "PRESTADOR DE SERVIÇOS" de "TOMADOR DE SERVIÇOS". Verifique os cabeçalhos das seções.

        **Instruções Específicas para Impostos e Deduções:**
        Procure ativamente por rótulos como "Valor PIS", "PIS/PASEP (R$)", "Retenção de PIS", "Valor COFINS", "COFINS (R$)", "Retenção de COFINS", "Valor CSLL", "CSLL (R$)", "Retenção de CSLL", "Valor IRRF", "IRRF (R$)", "Retenção IR", "Valor INSS", "INSS (R$)", "Retenção de INSS", "Valor das Deduções", "Deduções (R$)", "Crédito (R$)", "Valor Aprox. Tributos".
        Associe o rótulo ao valor numérico mais próximo, mesmo que esteja em outra coluna ou linha.
        Se encontrar um valor explicitamente como "0,00" ou "R$ 0,00", use "0,00" no JSON para o campo correspondente (ex: "ocr_valor_cofins": "0,00").
        Se o rótulo do imposto/dedução existir, mas o valor ao lado estiver ausente, for um traço ('-'), ou não for um número claro, use "".
        Se nem o rótulo for encontrado, use "".

        <EXEMPLO_DE_TAREFA>
        Texto de Entrada (Exemplo):
        ---
        PREFEITURA MUNICIPAL DE EXEMPLO
        NOTA FISCAL DE SERVIÇOS - NFS-e
        Número da Nota: 0000555 Data: 15/03/2024 10:30:00 Código Verificação: ABCD-1234
        PRESTADOR: MINHA EMPRESA DE SERVIÇOS LTDA CNPJ: 11.111.111/0001-11 IM: 98765 MUNICÍPIO: EXEMPLO UF: EX
        TOMADOR: CLIENTE IMPORTANTE S/A CNPJ: 22.222.222/0001-22 EMAIL: contato@cliente.com END: RUA EXEMPLO, 123
        DISCRIMINAÇÃO DOS SERVIÇOS:
        Consultoria especializada. Ref. Contrato XPTO.
        Código Serviço: 01.07 - Suporte técnico em informática.
        VALOR SERVIÇOS: R$ 1.500,00
        (-) Deduções: R$ 0,00
        Base Cálculo: R$ 1.500,00 Alíquota: 5,00% Valor ISS: R$ 75,00
        Retenção de PIS R$ 9,75 Retenção de COFINS R$ 45,00 CSLL (R$) R$ 15,00 Retenção IR R$ 22,50 INSS R$ 0,00
        Crédito (R$): -
        Valor Aprox Tributos: R$ 166,25 (11,08%) Fonte: IBPT
        ---
        Formato JSON de Saída (Exemplo):
        {{
            "ocr_numero": "0000555", "ocr_emissao_datahora": "15/03/2024 10:30:00", "ocr_codigo_verificacao": "ABCD-1234",
            "ocr_prestador_nome": "MINHA EMPRESA DE SERVIÇOS LTDA", "ocr_prestador_cpf_cnpj": "11.111.111/0001-11", "ocr_prestador_inscricao_municipal": "98765",
            "ocr_prestador_endereco": "", "ocr_prestador_municipio": "EXEMPLO", "ocr_prestador_uf": "EX",
            "ocr_tomador_nome": "CLIENTE IMPORTANTE S/A", "ocr_tomador_cpf_cnpj": "22.222.222/0001-22", "ocr_tomador_endereco": "RUA EXEMPLO, 123",
            "ocr_tomador_inscricao_municipal": "", "ocr_tomador_municipio": "", "ocr_tomador_uf": "", "ocr_tomador_email": "contato@cliente.com",
            "ocr_discriminacao": "Consultoria especializada. Ref. Contrato XPTO. Suporte técnico em informática.", "ocr_codigo_servico": "01.07",
            "ocr_valor_total": "1.500,00", "ocr_valor_base_calculo": "1.500,00", "ocr_valor_aliquota": "5,00%", "ocr_valor_iss": "75,00",
            "ocr_valor_deducoes": "0,00", "ocr_valor_pis_pasep": "9,75", "ocr_valor_cofins": "45,00", "ocr_valor_csll": "15,00",
            "ocr_valor_irrf": "22,50", "ocr_valor_inss": "0,00", "ocr_valor_credito": "", "ocr_valor_tributos_fonte": "166,25",
            "ocr_valor_tributos_fonte_percentual": "11,08%", "ocr_municipio_prestacao_servico": "",
            "ocr_intermediario_nome": "", "ocr_intermediario_cpf_cnpj": "", "ocr_outras_informacoes": "",
            "ocr_numero_inscricao_obra": "", "alogo_visivel": "", "categoria": "Consultoria TI"
        }}
        </EXEMPLO_DE_TAREFA>

        <TAREFA_REAL>
        Texto Extraído da Nota Fiscal (Via OCR):
        ---
        {texto_bruto}
        ---

        Formato JSON Obrigatório (preencha os "..."):
        {{
            "ocr_numero": "...", "ocr_emissao_datahora": "...", "ocr_codigo_verificacao": "...",
            "ocr_prestador_nome": "...", "ocr_prestador_cpf_cnpj": "...", "ocr_prestador_inscricao_municipal": "...",
            "ocr_prestador_endereco": "...", "ocr_prestador_municipio": "...", "ocr_prestador_uf": "...",
            "ocr_tomador_nome": "...", "ocr_tomador_cpf_cnpj": "...", "ocr_tomador_endereco": "...",
            "ocr_tomador_inscricao_municipal": "...", "ocr_tomador_municipio": "...", "ocr_tomador_uf": "...", "ocr_tomador_email": "...",
            "ocr_discriminacao": "...", "ocr_codigo_servico": "...",
            "ocr_valor_total": "...", "ocr_valor_base_calculo": "...", "ocr_valor_aliquota": "...", "ocr_valor_iss": "...",
            "ocr_valor_deducoes": "...", "ocr_valor_pis_pasep": "...", "ocr_valor_cofins": "...", "ocr_valor_csll": "...",
            "ocr_valor_irrf": "...", "ocr_valor_inss": "...", "ocr_valor_credito": "...",
            "ocr_valor_tributos_fonte": "...", "ocr_valor_tributos_fonte_percentual": "...",
            "ocr_municipio_prestacao_servico": "...", "ocr_intermediario_nome": "...", "ocr_intermediario_cpf_cnpj": "...",
            "ocr_outras_informacoes": "...", "ocr_numero_inscricao_obra": "...", "alogo_visivel": "...", "categoria": "..."
        }}
        </TAREFA_REAL>
        """
        # ---> FIM DO PROMPT REFINADO <---

        try:
            # Chama o Ollama para extrair o JSON do texto obtido pelo Azure
            response = ollama.chat( model=modelo_usado, messages=[{'role': 'user', 'content': prompt_texto}], options={'temperature': 0.0} )
            resposta_llm = response["message"]["content"]
            print(f"\n--- RESPOSTA BRUTA DO {modelo_usado.upper()} PARA '{filename}' ---\n{resposta_llm}\n{'-'*40}\n")
        except Exception as e:
             print(f"    [{modelo_usado.upper()}] Erro ao comunicar com o modelo Ollama para '{filename}': {e}")
             resposta_llm = ""
    else:
        print(f"    [PROCESSAMENTO] ERRO: Extração de texto (Azure OCR) falhou ou retornou texto insuficiente para '{filename}'. Impossível processar com LLM.")
        return {
            "texto_bruto_ocr": texto_bruto, # Retorna o texto (ou vazio) que veio do Azure
            "json_bruto_llm": None,
            "resposta_llm_com_erro": "Extração de texto Azure falhou ou texto insuficiente"
        }

    # --- Processamento Final da Resposta LLM (Ollama) ---
    if not resposta_llm:
        print(f"    [PROCESSAMENTO] ERRO FINAL: Não foi possível obter resposta do LLM ({modelo_usado}) para '{filename}'.")
        return {
            "texto_bruto_ocr": texto_bruto,
            "json_bruto_llm": None,
            "resposta_llm_com_erro": "Resposta do LLM (Ollama) foi vazia"
        }

    try:
        # Extrai o JSON da resposta do LLM (Ollama)
        # Tenta ser mais robusto na extração do JSON
        json_match = re.search(r'\{.*\}', resposta_llm, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
            # Tenta corrigir JSONs mal formados (ex: vírgula extra no final)
            try:
                dados_extraidos = json.loads(json_text)
            except json.JSONDecodeError as json_err:
                print(f"    [PROCESSAMENTO WARN] Tentativa de corrigir JSON mal formado para '{filename}'. Erro original: {json_err}")
                # Remove vírgulas extras antes de } ou ]
                json_text_corrected = re.sub(r',\s*([\}\]])', r'\1', json_text)
                try:
                    dados_extraidos = json.loads(json_text_corrected)
                    print(f"    [PROCESSAMENTO] JSON corrigido e extraído com sucesso para '{filename}'.")
                except json.JSONDecodeError as final_json_err:
                    print(f"    [PROCESSAMENTO ERRO] Falha ao corrigir e extrair JSON para '{filename}'. Erro final: {final_json_err}. Resposta original:\n{resposta_llm}")
                    dados_extraidos = {} # Define como falha

            # Se dados_extraidos não for vazio após tentativa de correção
            if dados_extraidos:
                print(f"    [PROCESSAMENTO] JSON extraído com sucesso (Ollama) para '{filename}'.")
                print(f"\n{'='*20} INSPECIONANDO DADOS BRUTOS DO LLM PARA '{filename}' {'='*20}")
                print(json.dumps(dados_extraidos, indent=4, ensure_ascii=False))
                print(f"{'='* (42 + len(filename))}\n")
            # Se a correção falhou, dados_extraidos já está {}

        else: # Se nem o regex encontrou um JSON
            print(f"    [PROCESSAMENTO] ERRO: Nenhum JSON válido encontrado (via regex) na resposta final do LLM (Ollama) para '{filename}'. Resposta recebida:\n{resposta_llm}")
            dados_extraidos = {}

    except Exception as e: # Captura outros erros inesperados
        print(f"    [PROCESSAMENTO] Erro inesperado ao processar a resposta do LLM (Ollama) para '{filename}': {e}")
        traceback.print_exc()
        dados_extraidos = {}

    # --- Retorno para Treinamento ---
    if dados_extraidos:
        return {
            "texto_bruto_ocr": texto_bruto, # Texto do Azure
            "json_bruto_llm": dados_extraidos # JSON do Ollama
        }
    else: # Se a extração do JSON falhou
        return {
            "texto_bruto_ocr": texto_bruto, # Texto do Azure
            "json_bruto_llm": None,
            "resposta_llm_com_erro": resposta_llm # Resposta completa do Ollama que falhou
        }


# ==============================================================================
# FUNÇÕES AUXILIARES (generate_file_hash, clean_and_format_data)
# ==============================================================================
def generate_file_hash(filepath: str) -> str:
    # ... (código inalterado) ...
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"    [HASH] Erro ao gerar hash para {filepath}: {e}")
        return None

def clean_and_format_data(dados_brutos: Dict[str, Any]) -> Dict[str, Any]:
    # ... (código inalterado da função clean_and_format_data) ...
    print(f"    [LIMPEZA] Iniciando limpeza para dados brutos (Schema OCR)...")
    dados_limpos = {}
    campos_esperados = [
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
        'categoria' # Adicionado categoria
    ]
    campos_monetarios = [
        'ocr_valor_total', 'ocr_valor_base_calculo', 'ocr_valor_iss', 'ocr_valor_deducoes',
        'ocr_valor_pis_pasep', 'ocr_valor_cofins', 'ocr_valor_csll', 'ocr_valor_irrf',
        'ocr_valor_inss', 'ocr_valor_credito', 'ocr_valor_tributos_fonte'
    ]
    campos_string = [k for k in campos_esperados if k not in campos_monetarios and k not in ['ocr_valor_aliquota', 'ocr_emissao_datahora', 'ocr_valor_tributos_fonte_percentual']]

    # 1. Limpeza inicial (strings)
    for key in campos_string:
        value = dados_brutos.get(key)
        dados_limpos[key] = "" if value is None or str(value).strip() == "..." or str(value).strip() == "" else str(value).strip()

    # 2. Limpeza de campos monetários
    for campo in campos_monetarios:
        valor_str = str(dados_brutos.get(campo) or '0')
        valor_numerico_str = ''.join(c for c in valor_str if c.isdigit() or c in [',', '.'])
        valor_numerico_str = valor_numerico_str.replace('R$', '').strip()
        if ',' in valor_numerico_str and '.' in valor_numerico_str:
            if valor_numerico_str.rfind('.') < valor_numerico_str.rfind(','):
                 valor_numerico_str = valor_numerico_str.replace('.', '').replace(',', '.')
            else:
                 valor_numerico_str = valor_numerico_str.replace(',', '')
        elif ',' in valor_numerico_str:
             valor_numerico_str = valor_numerico_str.replace(',', '.')
        elif '.' in valor_numerico_str:
             partes = valor_numerico_str.split('.')
             if len(partes[-1]) != 2:
                  valor_numerico_str = valor_numerico_str.replace('.', '')
        try:
            dados_limpos[campo] = float(valor_numerico_str) if valor_numerico_str else 0.0
        except ValueError:
            print(f"    [LIMPEZA WARN] Não foi possível converter valor monetário '{valor_str}' para float no campo '{campo}'. Usando 0.0.")
            dados_limpos[campo] = 0.0

    # 3. Limpeza da Alíquota
    aliquota_str = str(dados_brutos.get('ocr_valor_aliquota') or '0')
    aliquota_str = aliquota_str.replace('%', '').strip()
    valor_numerico = ''.join(c for c in aliquota_str if c.isdigit() or c == ',').replace(',', '.')
    try:
        aliquota_float = float(valor_numerico) if valor_numerico else 0.0
        if aliquota_float >= 1:
            dados_limpos['ocr_valor_aliquota'] = aliquota_float / 100.0
        else:
            dados_limpos['ocr_valor_aliquota'] = aliquota_float
    except ValueError:
        print(f"    [LIMPEZA WARN] Não foi possível converter alíquota '{aliquota_str}' para float. Usando 0.0.")
        dados_limpos['ocr_valor_aliquota'] = 0.0

    # 4. Limpeza de 'ocr_valor_tributos_fonte_percentual'
    percent_str = str(dados_brutos.get('ocr_valor_tributos_fonte_percentual') or '')
    dados_limpos['ocr_valor_tributos_fonte_percentual'] = percent_str.replace('%', '').strip()

    # 5. Limpeza da Data/Hora
    data_str = dados_brutos.get('ocr_emissao_datahora', '') or ''
    dados_limpos['ocr_emissao_datahora'] = None
    data_encontrada_str = None
    dt_obj = None
    data_str_original = data_str
    if isinstance(data_str, str) and data_str and data_str.strip() != "...":
        data_str_limpa = data_str.replace("```", "").replace("json", "").strip()
        data_str_limpa = re.sub(r'\s*\(.*\)\s*', '', data_str_limpa).strip()
        data_str_limpa = re.sub(r'[^\d/\-:\sTZtz]', '', data_str_limpa).strip()
        data_str_limpa = data_str_limpa.replace('.', '/').replace('-', '/')
        data_str_limpa = data_str_limpa.replace('//', '/')
        formatos_principais = [
            '%d/%m/%Y %H:%M:%S', '%Y/%m/%d %H:%M:%S',
            '%d/%m/%Y %H:%M',    '%Y/%m/%d %H:%M',
            '%d/%m/%Y',          '%Y/%m/%d',
            '%Y-%m-%dT%H:%M:%SZ', '%Y/%m/%dT%H:%M:%SZ',
        ]
        formatos_principais.extend([f.replace('/', '-') for f in formatos_principais if '/' in f])
        for fmt in formatos_principais:
            try:
                str_to_parse = data_str_limpa.replace('Z', '') if 'Z' not in fmt else data_str_limpa
                dt_obj = datetime.strptime(str_to_parse, fmt)
                data_encontrada_str = data_str_limpa
                break
            except ValueError: continue
        if dt_obj is None:
            print(f"    [DATA DEBUG] Formatos padrão falharam para '{data_str_original}'. Tentando Regex...")
            match_datetime = re.search(
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})[\sT]*(\d{1,2}:\d{1,2}(:\d{1,2})?)?|'
                r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})[\sT]*(\d{1,2}:\d{1,2}(:\d{1,2})?)?Z?',
                data_str_original
            )
            if match_datetime:
                if match_datetime.group(1) and match_datetime.group(2): data_pescada, hora_pescada = match_datetime.group(1), match_datetime.group(2)
                elif match_datetime.group(4) and match_datetime.group(5): data_pescada, hora_pescada = match_datetime.group(4), match_datetime.group(5)
                elif match_datetime.group(1): data_pescada, hora_pescada = match_datetime.group(1), ""
                elif match_datetime.group(4): data_pescada, hora_pescada = match_datetime.group(4), ""
                else: data_pescada, hora_pescada = "", ""
                if data_pescada:
                     data_hora_pescada = f"{data_pescada.strip()} {hora_pescada.strip() if hora_pescada else ''}".strip()
                     print(f"    [DATA DEBUG] Regex encontrou: '{data_hora_pescada}'")
                     formatos_pesca = formatos_principais
                     for fmt_pesca in formatos_pesca:
                         try:
                             str_to_parse = data_hora_pescada.replace('Z', '') if 'Z' not in fmt_pesca else data_hora_pescada
                             if '/' in fmt_pesca and '-' in str_to_parse: str_to_parse = str_to_parse.replace('-', '/')
                             if '-' in fmt_pesca and '/' in str_to_parse: str_to_parse = str_to_parse.replace('/', '-')
                             dt_obj = datetime.strptime(str_to_parse, fmt_pesca)
                             data_encontrada_str = data_hora_pescada
                             print(f"    [DATA DEBUG] Regex parse funcionou com formato '{fmt_pesca}'")
                             break
                         except ValueError: continue
            else: print(f"    [DATA DEBUG] Regex não encontrou padrão de data/hora em '{data_str_original}'.")
    if dt_obj:
        continha_hora = ':' in (data_encontrada_str or "")
        if dt_obj.hour == 0 and dt_obj.minute == 0 and dt_obj.second == 0 and not continha_hora:
             dados_limpos['ocr_emissao_datahora'] = dt_obj.strftime('%Y-%m-%d 00:00:00')
        else:
             try: dados_limpos['ocr_emissao_datahora'] = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
             except ValueError: dados_limpos['ocr_emissao_datahora'] = dt_obj.strftime('%Y-%m-%d 00:00:00')
        print(f"    [DATA DEBUG] Data final formatada: {dados_limpos['ocr_emissao_datahora']}")
    else: print(f"    [DATA FINAL] Aviso: Formato de data não reconhecido ou inválido após todas as tentativas: '{data_str_original}'")

    # 6. Verificação Final
    for campo in campos_esperados:
        if campo not in dados_limpos:
            if campo == 'ocr_emissao_datahora': dados_limpos[campo] = None
            elif campo in campos_monetarios or campo == 'ocr_valor_aliquota': dados_limpos[campo] = 0.0
            else: dados_limpos[campo] = ''
        elif (campo in campos_monetarios or campo == 'ocr_valor_aliquota') and dados_limpos[campo] is None:
             dados_limpos[campo] = 0.0

    # Adiciona categoria se não foi extraída (pode ser calculada aqui se necessário)
    if 'categoria' not in dados_limpos or not dados_limpos['categoria']:
         dados_limpos['categoria'] = "" # Ou lógica para determinar a categoria

    return dados_limpos


# --- Funções OCR legadas (mantidas mas não chamadas) ---
def extrair_texto_do_documento_EASYOCR_LEGACY(filepath: str) -> str:
    filename = os.path.basename(filepath)
    print(f"    [OCR EasyOCR LEGACY] Tentando extrair texto de '{filename}'...")
    # ... (resto da lógica do EasyOCR aqui) ...
    return "Texto EasyOCR Legado" # Placeholder

def extrair_texto_com_llava_LEGACY(filepath: str, modelo_lmm: str) -> str:
    filename = os.path.basename(filepath)
    print(f"    [{modelo_lmm.upper()} LEGACY] Tentando extrair texto de '{filename}' (Método LMM)...")
    # ... (resto da lógica do Ollama LMM aqui) ...
    return "Texto Ollama LMM Legado" # Placeholder