import os
import json
import hashlib
from datetime import datetime
import pandas as pd
from typing import Dict, Any

# --- Bibliotecas ---
import ollama
import pytesseract
from PIL import Image
import fitz  # pymupdf

# ==============================================================================
# CONFIGURAÇÕES LOCAIS
# ==============================================================================
PASTA_DOCUMENTOS = r'H:\projeto2\Documentos'
PASTA_PLANILHA = r'H:\projeto2\Planilha'
NOME_ARQUIVO_PLANILHA = 'planilha de dados.xlsx'
CAMINHO_PLANILHA = os.path.join(PASTA_PLANILHA, NOME_ARQUIVO_PLANILHA)

# ==============================================================================
# FUNÇÃO OCR (fallback se LLaVA não estiver disponível)
# ==============================================================================
def extrair_texto_ocr(filepath: str) -> str:
    if filepath.lower().endswith(".pdf"):
        texto_pdf = ""
        with fitz.open(filepath) as pdf:
            for pagina in pdf:
                texto_pdf += pagina.get_text()
        return texto_pdf
    else:
        img = Image.open(filepath)
        return pytesseract.image_to_string(img, lang="por")

# ==============================================================================
# FUNÇÃO PRINCIPAL DE PROCESSAMENTO (LLM multimodal ou OCR)
# ==============================================================================
def processar_documento_com_llm_local(filepath: str) -> Dict[str, Any]:
    print(f"      [LLaVA] Tentando enviar '{os.path.basename(filepath)}' para o modelo multimodal...")

    prompt = """
    Você é um sistema de extração de dados altamente preciso. Analise a Nota Fiscal de Serviços (NFS-e) fornecida.
    Sua única tarefa é retornar um objeto JSON válido, no formato abaixo, preenchido com os dados da nota.
    Não inclua explicações ou texto fora do JSON.

    Estrutura JSON:
    {
      "numero_nota": "...",
      "data_hora_emissao": "...",
      "codigo_verificacao": "...",
      "prestador": {
        "cnpj": "...",
        "razao_social": "...",
        "inscricao_municipal": "...",
        "endereco": {
          "logradouro": "...",
          "bairro": "...",
          "cep": "...",
          "cidade": "...",
          "uf": "..."
        }
      },
      "tomador": {
        "cpf": "...",
        "razao_social": "...",
        "email": "...",
        "endereco": {
          "logradouro": "...",
          "bairro": "...",
          "cep": "...",
          "cidade": "...",
          "uf": "..."
        }
      },
      "servico": {
        "discriminacao": "...",
        "codigo": "...",
        "descricao": "..."
      },
      "valores": {
        "total_servico": "...",
        "base_calculo": "...",
        "aliquota": "...",
        "valor_iss": "..."
      },
      "valor_total_impostos": "..."
    }
    """

    try:
        response = ollama.chat(
            model='llava:13b',
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [filepath]
            }],
            options={'temperature': 0.0}
        )

        resposta_llm = response["message"]["content"]
        print(f"\n--- RESPOSTA BRUTA DO LLaVA ---\n{resposta_llm}\n---------------------------------\n")

        json_text = resposta_llm.replace("```json", "").replace("```", "").strip()
        inicio_json = json_text.find('{')
        fim_json = json_text.rfind('}') + 1

        if inicio_json != -1 and fim_json != 0:
            json_text = json_text[inicio_json:fim_json]
            print("      [LLaVA] JSON extraído com sucesso.")
            return json.loads(json_text)

        print("      [LLaVA] Nenhum JSON válido encontrado. Caindo para OCR...")
        return {"texto_extraido": extrair_texto_ocr(filepath)}

    except Exception as e:
        print(f"      [LLaVA] Erro ao usar modelo multimodal: {e}")
        print("      [Fallback] Usando OCR com Tesseract.")
        return {"texto_extraido": extrair_texto_ocr(filepath)}

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def generate_file_hash(filepath: str) -> str:
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def clean_and_format_data(dados_brutos: Dict[str, Any]) -> Dict[str, Any]:
    dados_limpos = dados_brutos.copy()
    campos_monetarios = ['valor_total_servico', 'base_calculo', 'valor_iss', 'valor_total_impostos']
    for campo in campos_monetarios:
        valor_str = dados_brutos.get(campo, '0') or '0'
        if isinstance(valor_str, str):
            valor_numerico = valor_str.replace('R$', '').strip().replace('.', '').replace(',', '.')
            try:
                dados_limpos[campo] = float(valor_numerico)
            except (ValueError, TypeError):
                dados_limpos[campo] = 0.0
    aliquota_str = dados_brutos.get('aliquota', '0') or '0'
    if isinstance(aliquota_str, str):
        valor_numerico = aliquota_str.replace('%', '').strip().replace(',', '.')
        try:
            dados_limpos['aliquota'] = float(valor_numerico) / 100.0
        except (ValueError, TypeError):
            dados_limpos['aliquota'] = 0.0
    data_str = dados_limpos.get('data_hora_emissao', '') or ''
    if isinstance(data_str, str) and data_str:
        try:
            dt_obj = datetime.strptime(data_str, '%d/%m/%Y')
            dados_limpos['data_hora_emissao'] = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            dados_limpos['data_hora_emissao'] = data_str
    return dados_limpos

# ==============================================================================
# MAIN
# ==============================================================================
def main():
    try:
        os.makedirs(PASTA_DOCUMENTOS, exist_ok=True)
        os.makedirs(PASTA_PLANILHA, exist_ok=True)
        HEADERS = [
            'hash', 'arquivo', 'data_processamento', 'numero_nota', 'data_hora_emissao', 'codigo_verificacao',
            'prestador_cnpj', 'prestador_razao_social', 'prestador_logradouro', 'prestador_bairro', 'prestador_cep',
            'prestador_cidade', 'prestador_uf', 'prestador_inscricao_municipal',
            'tomador_cpf', 'tomador_razao_social', 'tomador_logradouro', 'tomador_bairro', 'tomador_cep',
            'tomador_cidade', 'tomador_uf', 'tomador_email',
            'discriminacao_servicos', 'servico_codigo', 'servico_descricao',
            'valor_total_servico', 'base_calculo', 'aliquota', 'valor_iss',
            'valor_total_impostos'
        ]

        df = pd.DataFrame(columns=HEADERS)
        if os.path.exists(CAMINHO_PLANILHA):
            print(f"Carregando planilha existente de: {CAMINHO_PLANILHA}")
            try:
                df = pd.read_excel(CAMINHO_PLANILHA)
                if df.empty:
                    df = pd.DataFrame(columns=HEADERS)
            except Exception as e:
                print(f"Aviso: não foi possível ler a planilha existente. Começando do zero. Erro: {e}")
                df = pd.DataFrame(columns=HEADERS)
        else:
            print(f"Planilha não encontrada. Criando estrutura em memória.")

        existing_hashes = set(df['hash'].astype(str).tolist())
        arquivos_na_pasta = os.listdir(PASTA_DOCUMENTOS)
        novos_dados = []

        for filename in arquivos_na_pasta:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
                filepath = os.path.join(PASTA_DOCUMENTOS, filename)
                current_hash = generate_file_hash(filepath)
                if current_hash in existing_hashes:
                    continue
                print(f"\n-> Processando novo arquivo: '{filename}'")

                dados_brutos = processar_documento_com_llm_local(filepath)
                if not dados_brutos:
                    print(f"❌ Falha ao processar '{filename}'.")
                    continue

                # Se caiu no OCR, só salva texto cru
                if "texto_extraido" in dados_brutos:
                    dados_finais = {
                        "hash": current_hash,
                        "arquivo": filename,
                        "data_processamento": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "discriminacao_servicos": dados_brutos["texto_extraido"]
                    }
                else:
                    # Caso LLaVA tenha conseguido JSON
                    dados_achatados = {
                        "numero_nota": dados_brutos.get("numero_nota"),
                        "data_hora_emissao": dados_brutos.get("data_hora_emissao"),
                        "codigo_verificacao": dados_brutos.get("codigo_verificacao"),
                        "prestador_cnpj": dados_brutos.get("prestador", {}).get("cnpj"),
                        "prestador_razao_social": dados_brutos.get("prestador", {}).get("razao_social"),
                        "prestador_inscricao_municipal": dados_brutos.get("prestador", {}).get("inscricao_municipal"),
                        "prestador_logradouro": dados_brutos.get("prestador", {}).get("endereco", {}).get("logradouro"),
                        "prestador_bairro": dados_brutos.get("prestador", {}).get("endereco", {}).get("bairro"),
                        "prestador_cep": dados_brutos.get("prestador", {}).get("endereco", {}).get("cep"),
                        "prestador_cidade": dados_brutos.get("prestador", {}).get("endereco", {}).get("cidade"),
                        "prestador_uf": dados_brutos.get("prestador", {}).get("endereco", {}).get("uf"),
                        "tomador_cpf": dados_brutos.get("tomador", {}).get("cpf"),
                        "tomador_razao_social": dados_brutos.get("tomador", {}).get("razao_social"),
                        "tomador_email": dados_brutos.get("tomador", {}).get("email"),
                        "tomador_logradouro": dados_brutos.get("tomador", {}).get("endereco", {}).get("logradouro"),
                        "tomador_bairro": dados_brutos.get("tomador", {}).get("endereco", {}).get("bairro"),
                        "tomador_cep": dados_brutos.get("tomador", {}).get("endereco", {}).get("cep"),
                        "tomador_cidade": dados_brutos.get("tomador", {}).get("endereco", {}).get("cidade"),
                        "tomador_uf": dados_brutos.get("tomador", {}).get("endereco", {}).get("uf"),
                        "discriminacao_servicos": dados_brutos.get("servico", {}).get("discriminacao"),
                        "servico_codigo": dados_brutos.get("servico", {}).get("codigo"),
                        "servico_descricao": dados_brutos.get("servico", {}).get("descricao"),
                        "valor_total_servico": dados_brutos.get("valores", {}).get("total_servico"),
                        "base_calculo": dados_brutos.get("valores", {}).get("base_calculo"),
                        "aliquota": dados_brutos.get("valores", {}).get("aliquota"),
                        "valor_iss": dados_brutos.get("valores", {}).get("valor_iss"),
                        "valor_total_impostos": dados_brutos.get("valor_total_impostos")
                    }
                    dados_finais = clean_and_format_data(dados_achatados)
                    dados_finais['hash'] = current_hash
                    dados_finais['arquivo'] = filename
                    dados_finais['data_processamento'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                novos_dados.append(dados_finais)
                print(f"✅ Dados de '{filename}' extraídos com sucesso.")

        if novos_dados:
            novos_df = pd.DataFrame(novos_dados)
            df_final = pd.concat([df, novos_df], ignore_index=True)
            df_final.to_excel(CAMINHO_PLANILHA, index=False, columns=HEADERS)
            print(f"\n✅ {len(novos_dados)} novo(s) registro(s) foram adicionados à planilha!")
        else:
            print("\nNenhum arquivo novo para processar.")

        print("\nProcesso concluído.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    main()