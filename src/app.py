import os
import json
from flask import Flask, request, jsonify, render_template, Response
import google.generativeai as genai
from dotenv import load_dotenv
import pypdf
import nltk                                # NOVO: Importa NLTK
from nltk.corpus import stopwords          # NOVO: Para Stop Words
from nltk.stem import RSLPStemmer          # NOVO: Para Stemming em Português
import re 

# Lógica de importação para suportar o ambiente serverless (Vercel)
try:
    from database import initialize_db, insert_classification, get_history, get_raw_history_data
    from export import export_history_to_csv 
except ImportError as e:
    # Cria funções de placeholder se os módulos não forem encontrados, garantindo que o Flask inicie.
    print(f"ATENÇÃO: Falha ao importar módulos customizados: {e}")
    def initialize_db(): pass
    def insert_classification(*args, **kwargs): pass
    def get_history(): return []
    def get_raw_history_data(): return []
    def export_history_to_csv(data): return Response("Erro de Módulo", mimetype="text/plain", status=500)


load_dotenv()

NLTK_DATA_DIR = '/tmp/nltk_data'
os.makedirs(NLTK_DATA_DIR, exist_ok=True)
nltk.data.path.append(NLTK_DATA_DIR)

# Tenta fazer o download dos recursos necessários, se não existirem
def setup_nltk_data():
    """Garante que os dados do NLTK necessários para Português estejam em /tmp."""
    try:
        # Tenta carregar os dados
        stopwords.words('portuguese')
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/rslp')
    except (LookupError, FileNotFoundError):
        print("Baixando dados do NLTK para /tmp...")
        try:
            # Baixa os módulos necessários
            nltk.download('stopwords', download_dir=NLTK_DATA_DIR)
            nltk.download('rslp', download_dir=NLTK_DATA_DIR)
            nltk.download('punkt', download_dir=NLTK_DATA_DIR) 
            print("Download do NLTK concluído.")
        except Exception as e:
            print(f"Erro ao baixar dados do NLTK: {e}")

setup_nltk_data()

# Ajusta o root_path para encontrar as pastas 'templates' e 'static' no diretório pai,
# após mover 'app.py' para a pasta 'src/'.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
app = Flask(__name__, root_path=project_root)

# Configuração da API do Google Generative AI
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # A chave deve ser configurada via Environment Variables (Vercel) ou arquivo .env (local)
        raise ValueError("A variável de ambiente GEMINI_API_KEY não foi definida.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
except Exception as e:
    print(f"Erro ao configurar a API do Google: {e}")
    model = None

# Template do Prompt para o Modelo de IA
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
- "suggested_response": Se o e-mail for "Produtivo", sugira uma resposta curta e profissional. Se for "Improdutivo", retorne "Nenhuma resposta necessária.".

Retorne apenas o JSON, sem nenhum texto, markdown ou explicação adicional.
"""

def preprocess_text_nlp(text):
    """
    Executa Limpeza, Tokenização, Remoção de Stop Words e Stemming (RSLP) em Português.
    """
    # 1. Limpeza básica (converter para minúsculas e remover pontuação)
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text) 

    # 2. Tokenização
    tokens = nltk.word_tokenize(text, language='portuguese')

    # 3. Remoção de Stop Words
    stop_words = set(stopwords.words('portuguese'))
    # Filtra tokens que não estão na lista de stop words e que não são apenas espaços em branco
    filtered_tokens = [word for word in tokens if word not in stop_words and word.strip()]

    # 4. Stemming (Redução ao radical - RSLP para Português)
    stemmer = RSLPStemmer()
    stemmed_tokens = [stemmer.stem(word) for word in filtered_tokens]
    
    # Retorna o texto pré-processado como uma string, separado por espaço
    return ' '.join(stemmed_tokens)

@app.route('/')
def index():
    """Renderiza a página inicial e garante a inicialização do DB (necessário no Serverless)."""
    initialize_db()
    return render_template('index.html')

@app.route('/classify', methods=['POST'])
def classify_email():
    """Recebe o e-mail, classifica com a IA, salva no banco e retorna o resultado."""
    initialize_db()
    
    if not model:
        return jsonify({'error': 'O modelo de IA não foi inicializado. Verifique a chave da API.'}), 503

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

            # Limpa a resposta da IA para extrair apenas o JSON
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '')

            # Tenta analisar o JSON e trata erros
            try:
                result_json = json.loads(cleaned_response)
            except json.JSONDecodeError:
                print(f"Erro ao decodificar JSON. Resposta da IA: {cleaned_response}")
                return jsonify({'error': 'A resposta da IA não estava em um formato JSON válido.'}), 500

            # Salva a classificação no histórico
            classification = result_json.get("classification", "Desconhecido")
            confidence_score = result_json.get("confidence_score", 0.0)
            suggested_response = result_json.get("suggested_response", "Nenhuma resposta")
            
            # Garante que confidence_score seja um float
            if not isinstance(confidence_score, (int, float)):
                try:
                    confidence_score = float(confidence_score)
                except ValueError:
                    confidence_score = 0.0 
                    
            insert_classification(classification, confidence_score, suggested_response, email_content)

            return jsonify(result_json)

        except genai.types.generation_types.StopCandidateException as e:
            print(f"Geração interrompida pela IA: {e}")
            return jsonify({'error': f"A IA interrompeu a geração por razões de segurança ou conteúdo."}), 500
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            return jsonify({'error': f"Ocorreu um erro inesperado no servidor."}), 500

@app.route('/history')
def history():
    """Retorna os últimos e-mails classificados."""
    initialize_db()
    
    history_data = get_history()
    
    # Processa os dados para adicionar o snippet para o frontend
    processed_history = []
    for row in history_data:
        email_content = row.get('email_content', '')
        snippet = email_content.strip().replace('\n', ' ')[:150] + '...' if len(email_content.strip()) > 150 else email_content.strip().replace('\n', ' ')
        
        processed_history.append({
            'classification': row.get('classification', 'Desconhecido'),
            'created_at': row.get('created_at', ''),
            'email_snippet': snippet,
            'email_content': email_content,
            'suggested_response': row.get('suggested_response', 'Nenhuma resposta')
        })
        
    return jsonify(processed_history)

@app.route('/export_history')
def export_history():
    """Exporta todo o histórico do banco de dados para um arquivo CSV."""
    initialize_db()
    
    try:
        raw_data = get_raw_history_data()
        return export_history_to_csv(raw_data)
        
    except Exception as e:
        print(f"Erro ao exportar histórico: {e}")
        return jsonify({'error': 'Falha ao gerar o arquivo CSV.'}), 500


if __name__ == '__main__':
    # Bloco para execução local
    initialize_db() 
    app.run(debug=True)
