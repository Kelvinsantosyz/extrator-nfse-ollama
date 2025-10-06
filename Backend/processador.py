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
    MODELO_FIXO = 'llava:13b'
    print(f"     [LLaVA] Enviando '{os.path.basename(filepath)}' para o modelo '{MODELO_FIXO}'...")
    
    # Prompt atualizado para incluir o campo 'valor_inss'
    prompt = """
    Você é um assistente de IA especialista em extrair dados de Notas Fiscais de Serviço (NFS-e) brasileiras. Analise a imagem em anexo com extrema atenção.
    Sua única tarefa é retornar um objeto JSON completo e válido. Não inclua NENHUMA palavra ou explicação fora do objeto JSON.
    Com base no campo 'discriminacao', sugira uma categoria de despesa (ex: 'Serviços de TI', 'Marketing', 'Manutenção', 'Consultoria', 'Saúde').
    Extraia o valor do campo 'INSS (R$)' para o campo 'valor_inss'.

    Siga rigorosamente esta estrutura JSON:
    {
      "numero_nota": "...", "data_hora_emissao": "...", "codigo_verificacao": "...",
      "prestador": { "cnpj": "...", "razao_social": "...", "inscricao_municipal": "...", "endereco": { "logradouro": "...", "bairro": "...", "cep": "...", "cidade": "...", "uf": "..." } },
      "tomador": { "cpf": "...", "razao_social": "...", "email": "...", "endereco": { "logradouro": "...", "bairro": "...", "cep": "...", "cidade": "...", "uf": "..." } },
      "servico": { "discriminacao": "...", "codigo": "...", "descricao": "..." },
      "valores": { "total_servico": "...", "base_calculo": "...", "aliquota": "...", "valor_iss": "...", "valor_inss": "..." },
      "valor_total_impostos": "...",
      "categoria": "Sugestão de Categoria"
    }
    """
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
        print(f"     [LLaVA] ERRO: Nenhum JSON encontrado na resposta.")
        return {}
    except Exception as e:
        print(f"     [LLaVA] Erro ao usar modelo multimodal: {e}")
        return {}

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def generate_file_hash(filepath: str) -> str:
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4_096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def clean_and_format_data(dados_brutos: Dict[str, Any]) -> Dict[str, Any]:
    dados_limpos = dados_brutos.copy()
    # Adicionado 'valor_inss' à lista
    campos_monetarios = ['valor_total_servico', 'base_calculo', 'valor_iss', 'valor_total_impostos', 'valor_inss']
    for campo in campos_monetarios:
        # A lógica agora busca tanto no dicionário principal quanto no aninhado 'valores'
        valor_str = dados_brutos.get(campo) or dados_brutos.get("valores", {}).get(campo, '0') or '0'
        if isinstance(valor_str, str):
            valor_numerico = valor_str.replace('R$', '').strip().replace('.', '').replace(',', '.')
            try:
                dados_limpos[campo] = float(valor_numerico)
            except (ValueError, TypeError):
                dados_limpos[campo] = 0.0
    
    aliquota_str = dados_brutos.get("valores", {}).get('aliquota', '0') or '0'
    if isinstance(aliquota_str, str):
        valor_numerico = aliquota_str.replace('%', '').strip().replace(',', '.')
        try:
            dados_limpos['aliquota'] = float(valor_numerico) / 100.0
        except (ValueError, TypeError):
            dados_limpos['aliquota'] = 0.0
            
    data_str = dados_brutos.get('data_hora_emissao', '') or ''
    if isinstance(data_str, str) and data_str:
        try:
            if len(data_str) > 10:
                 dt_obj = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
            else:
                 dt_obj = datetime.strptime(data_str, '%d/%m/%Y')
            dados_limpos['data_hora_emissao'] = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            dados_limpos['data_hora_emissao'] = None
            
    dados_limpos['categoria'] = str(dados_brutos.get('categoria', 'Não Categorizado'))
    
    return dados_limpos

