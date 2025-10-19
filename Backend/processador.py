import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any

# --- Bibliotecas de Extração ---
import ollama

# ==============================================================================
# FUNÇÃO PRINCIPAL DE PROCESSAMENTO (LLM)
# ==============================================================================
def processar_documento_com_llm_local(filepath: str) -> Dict[str, Any]:
    """Usa um modelo multimodal (LLaVA) com um prompt baseado em exemplos para extrair dados."""
    MODELO_FIXO = 'llava:13b'
    print(f"    [LLaVA] Enviando '{os.path.basename(filepath)}' para o modelo '{MODELO_FIXO}'...")

    # Prompt otimizado para extrair todos os campos, incluindo a categoria
    prompt = """
    Você é um sistema de extração de dados altamente preciso. Analise a imagem da Nota Fiscal de Serviços (NFS-e) em anexo.
    Sua única tarefa é retornar um objeto JSON. Não retorne NADA além do objeto JSON.
    Preencha a estrutura JSON abaixo com os dados exatos encontrados na imagem.
    Sugira uma 'categoria' com base na 'discriminacao' do serviço (ex: 'Tecnologia', 'Marketing', 'Saúde', 'Serviços Gerais').

    Use este formato com exemplos como seu guia:
    {
      "numero_nota": "00016838",
      "data_hora_emissao": "18/11/2018",
      "codigo_verificacao": "LUES-8XKJ",
      "prestador": {
        "cnpj": "00.126.717/0001-84",
        "razao_social": "CLINICA VALERIO LTDA",
        "inscricao_municipal": "2.276.461-5",
        "endereco": { "logradouro": "R PORTO XAVIER 00066", "bairro": "TAQUERA", "cep": "08210-170", "cidade": "São Paulo", "uf": "SP" }
      },
      "tomador": {
        "cpf": "050.972.418-09",
        "razao_social": "DIELSON DOS PASSOS MENDES",
        "email": "dielsonmendes@hotmail.com",
        "endereco": { "logradouro": "R Salvador do Sul 154, APTO 02 BL 02", "bairro": "Vila Progresso (Zona Leste)", "cep": "08240-500", "cidade": "São Paulo", "uf": "SP" }
      },
      "servico": {
        "discriminacao": "REFERENTE A SERVIÇOS ODONTOLOGICO DO MESMO",
        "codigo": "04893",
        "descricao": "Odontologia."
      },
      "valores": {
        "total_servico": "R$ 1.200,00",
        "base_calculo": "1.200,00",
        "aliquota": "2,00%",
        "valor_iss": "24,00"
      },
      "valor_total_impostos": "R$ 195,96",
      "categoria": "Saúde"
    }
    """
    
    resposta_llm = ""
    try:
        response = ollama.chat(
            model=MODELO_FIXO,
            messages=[{'role': 'user', 'content': prompt, 'images': [filepath]}],
            options={'temperature': 0.0}
        )
        
        resposta_llm = response["message"]["content"]
        json_text = resposta_llm.replace("```json", "").replace("```", "").strip()
        inicio_json = json_text.find('{')
        fim_json = json_text.rfind('}') + 1
        
        if inicio_json != -1 and fim_json != 0:
            json_text = json_text[inicio_json:fim_json]
            return json.loads(json_text)
        
        print(f"    [LLaVA] ERRO: Nenhum JSON encontrado na resposta.")
        return {}
    except Exception as e:
        print(f"    [LLaVA] Erro ao usar modelo multimodal: {e}")
        return {}

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def generate_file_hash(filepath: str) -> str:
    """Calcula o hash MD5 de um arquivo para evitar reprocessamento."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def clean_and_format_data(dados_brutos: Dict[str, Any]) -> Dict[str, Any]:
    """Limpa e formata os dados extraídos para os tipos corretos (números, datas)."""
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
            
    data_str = dados_brutos.get('data_hora_emissao', '') or ''
    if isinstance(data_str, str) and data_str:
        try:
            # Tenta múltiplos formatos de data para maior robustez
            if len(data_str) > 10:
                 dt_obj = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
            else:
                 dt_obj = datetime.strptime(data_str, '%d/%m/%Y')
            dados_limpos['data_hora_emissao'] = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            dados_limpos['data_hora_emissao'] = data_str
            
    return dados_limpos

