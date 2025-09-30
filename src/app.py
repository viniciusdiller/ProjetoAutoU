import os
import json
import uuid # NOVO: Para gerar um ID único
from flask import Flask, request, jsonify, render_template, Response, session # NOVO: Importa 'session'
import google.generativeai as genai
from dotenv import load_dotenv
import pypdf

# Lógica de importação para suportar o ambiente serverless (Vercel)
try:
    from database import initialize_db, insert_classification, get_history, get_raw_history_data
    from export import export_history_to_csv 
except ImportError as e:
    # Cria funções de placeholder com a assinatura atualizada (com user_id)
    print(f"ATENÇÃO: Falha ao importar módulos customizados: {e}")
    # Atualiza a assinatura dos placeholders para aceitar user_id
    def insert_classification(*args, **kwargs): pass 
    def initialize_db(): pass
    def get_history(*args): return []
    def get_raw_history_data(*args): return []
    def export_history_to_csv(data): return Response("Erro de Módulo", mimetype="text/plain", status=500)


load_dotenv()

# Ajusta o root_path para encontrar as pastas 'templates' e 'static'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
app = Flask(__name__, root_path=project_root)

# CONFIGURAÇÃO DE SESSÃO FLASK
# A variável SECRET_KEY é essencial. Use uma chave segura e aleatória.
# É recomendável configurar SECRET_KEY no painel de Environment Variables da Vercel.
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24)) 

# Configuração da API do Google Generative AI (mantida)
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente GEMINI_API_KEY não foi definida.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
except Exception as e:
    print(f"Erro ao configurar a API do Google: {e}")
    model = None

# Template do Prompt (mantido)
PROMPT_TEMPLATE = """
Analise o e-mail fornecido e retorne um objeto JSON.
O objetivo é classificar o e-mail como "Produtivo" ou "Improdutivo".

- "Produtivo": E-mails que requerem uma ação ou resposta específica (ex: solicitações, dúvidas, atualizações de casos).
- "Improdutivo": E-mails que não necessitam de uma ação (ex: felicitações, agradecimentos, spam).

E-mail para análise:
---
{email_content}
---

O JSON de saída deve ter a seguinte estrutura em inglês:
- "classification": A categoria ("Produtivo" ou "Improdutivo").
- "confidence_score": Um número entre 0.0 e 1.0 indicando sua confiança na classificação.
- "key_topic": Uma frase curta (máximo 5 palavras) ou palavra-chave que resume o tema principal do e-mail (ex: "Solicitação de Orçamento", "Atualização de Projeto", "Agradecimento Geral").
- "sentiment": A emoção geral expressa no e-mail (ex: "Neutro", "Urgente", "Positivo", "Frustração").
- "suggested_response": Se o e-mail for "Produtivo", sugira uma resposta curta e profissional. Se for "Improdutivo", retorne "Nenhuma resposta necessária.".

Retorne apenas o JSON, sem nenhum texto, markdown ou explicação adicional.
"""

# FUNÇÃO AUXILIAR PARA GARANTIR QUE CADA USUÁRIO TENHA UM ID
def get_or_create_user_id():
    """Verifica ou cria um user_id baseado na sessão do Flask."""
    if 'user_id' not in session:
        # Usa UUID4 para gerar um ID de usuário único e armazena na sessão
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']


@app.route('/')
def index():
    """Renderiza a página inicial e garante o ID de sessão."""
    initialize_db()
    # Cria ou recupera o ID de sessão do usuário
    get_or_create_user_id()
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify_email():
    """Recebe o e-mail, classifica com a IA, salva no banco (com ID de sessão) e retorna o resultado."""
    initialize_db()
    
    if not model:
        return jsonify({'error': 'O modelo de IA não foi inicializado. Verifique a chave da API.'}), 503
    
    # OBTÉM O ID DE SESSÃO DO USUÁRIO
    user_id = get_or_create_user_id()

    email_content = ""
    # Extrai o conteúdo do formulário de texto ou do arquivo enviado
    if 'email_text' in request.form and request.form['email_text']:
        email_content = request.form['email_text']
    elif 'file' in request.files:
        file = request.files['file']
        
        # Bloco de processamento de arquivos (.txt e .pdf)
        if file.filename.endswith('.txt'):
            try:
                email_content = file.read().decode('utf-8')
            except UnicodeDecodeError:
                return jsonify({'error': 'Não foi possível decodificar o arquivo .txt. Tente usar a codificação UTF-8.'}), 400
        elif file.filename.endswith('.pdf'):
            try:
                reader = pypdf.PdfReader(file)
                text = "".join(page.extract_text() or "" for page in reader.pages)
                email_content = text.strip()
            except Exception as e:
                print(f"Erro ao processar PDF: {e}")
                return jsonify({'error': f'Falha ao processar o arquivo PDF. Verifique se o texto é legível.'}), 400

    if not email_content.strip():
        return jsonify({'error': 'Nenhum conteúdo de e-mail fornecido ou o arquivo está vazio.'}), 400

    try:
        prompt = PROMPT_TEMPLATE.format(email_content=email_content)
        response = model.generate_content(prompt)

        # Limpa e analisa o JSON
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        try:
            result_json = json.loads(cleaned_response)
        except json.JSONDecodeError:
            print(f"Erro ao decodificar JSON. Resposta da IA: {cleaned_response}")
            return jsonify({'error': 'A resposta da IA não estava em um formato JSON válido.'}), 500

        # Salva a classificação no histórico
        classification = result_json.get("classification", "Desconhecido")
        confidence_score = result_json.get("confidence_score", 0.0)
        key_topic = result_json.get("key_topic", "N/A")
        sentiment = result_json.get("sentiment", "Neutro")
        suggested_response = result_json.get("suggested_response", "Nenhuma resposta")
        
        if not isinstance(confidence_score, (int, float)):
            try:
                confidence_score = float(confidence_score)
            except ValueError:
                confidence_score = 0.0 
        
        # CHAMA insert_classification COM O user_id DINÂMICO
        insert_classification(user_id, classification, confidence_score, key_topic, sentiment, suggested_response, email_content)

        return jsonify(result_json)

    except genai.types.generation_types.StopCandidateException as e:
        print(f"Geração interrompida pela IA: {e}")
        return jsonify({'error': f"A IA interrompeu a geração por razões de segurança ou conteúdo."}), 500
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        return jsonify({'error': f"Ocorreu um erro inesperado no servidor."}), 500

@app.route('/history')
def history():
    """Retorna o histórico persistente e isolado pelo ID de sessão."""
    initialize_db()
    
    # OBTÉM O ID DE SESSÃO DO USUÁRIO
    user_id = get_or_create_user_id()
    
    # CHAMA get_history COM O user_id DINÂMICO
    history_data = get_history(user_id)
    
    # Processa os dados para o frontend (mantendo a estrutura de retorno)
    processed_history = []
    for row in history_data:
        processed_history.append({
            'classification': row.get('classification', 'Desconhecido'),
            'created_at': row.get('created_at', ''),
            'email_snippet': row.get('email_snippet', ''),
            'email_content': row.get('email_content', ''),
            'suggested_response': row.get('suggested_response', 'Nenhuma resposta'),
            'key_topic': row.get('key_topic', 'N/A'),
            'sentiment': row.get('sentiment', 'Neutro')
        })
        
    return jsonify(processed_history)

@app.route('/export_history')
def export_history():
    """Exporta todo o histórico isolado para CSV pelo ID de sessão."""
    initialize_db()
    
    # OBTÉM O ID DE SESSÃO DO USUÁRIO
    user_id = get_or_create_user_id()
    
    try:
        # CHAMA get_raw_history_data COM O user_id DINÂMICO
        raw_data = get_raw_history_data(user_id)
        return export_history_to_csv(raw_data)
        
    except Exception as e:
        print(f"Erro ao exportar histórico: {e}")
        return jsonify({'error': 'Falha ao gerar o arquivo CSV.'}), 500


if __name__ == '__main__':
    # Bloco para execução local
    initialize_db() 
    app.run(debug=True)