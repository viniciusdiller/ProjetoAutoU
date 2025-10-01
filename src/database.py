import os
import psycopg2 
from psycopg2 import sql 
import datetime

# A URL do PostgreSQL será lida das variáveis de ambiente.

def get_db_connection():
    """
    Cria e retorna a conexão com o banco de dados PostgreSQL.
    Tenta URLs UNPOOLED/padrão para máxima compatibilidade Serverless.
    """
    
    # 1. Tenta a URL UNPOOLED (Mais estável para driver síncrono na Vercel)
    connection_url = os.getenv("DATABASE_URL_UNPOOLED")
    
    # 2. Faz fallback para a URL poolada (Geralmente a principal)
    if not connection_url:
        connection_url = os.getenv("DATABASE_URL")
    
    if not connection_url:
        raise ValueError("Nenhuma URL de banco de dados (UNPOOLED ou padrão) foi definida.")
    
    # AJUSTE FINAL: Usa 'sslmode=prefer' e timeout para estabilidade.
    # Nota: Removemos o sslmode='require' do código anterior para garantir 
    # que este modo preferencial seja aplicado.
    return psycopg2.connect(connection_url, sslmode='prefer', connect_timeout=5)


def initialize_db():
    """Cria a tabela e o índice no PostgreSQL se não existirem."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Cria a tabela com a nova coluna user_id
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classifications (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,  -- Chave para isolamento de dados
                classification TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                suggested_response TEXT,
                email_content TEXT,
                key_topic TEXT,  
                sentiment TEXT,  
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Cria um índice para a busca por usuário (performance)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id 
            ON classifications (user_id);
        """)
        
        conn.commit()
    except Exception as e:
        print(f"Erro ao inicializar o DB (PostgreSQL): {e}")
        # É VITAL NUNCA DAR 'raise' EM initialize_db no Flask, mas sim em try/except
        # para que o servidor não caia na inicialização. Deixaremos 'raise' para ser propagado
        # e falhar no /classify e /history, onde o erro deve ser visível.
        raise
    finally:
        if conn:
            conn.close()

# user_id é agora o primeiro argumento
def insert_classification(user_id, classification, confidence_score, key_topic, sentiment, suggested_response, email_content):
    """Insere um novo registro de classificação no banco de dados para o ID de sessão."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insere dados, usando user_id dinâmico
        cursor.execute("""
            INSERT INTO classifications (user_id, classification, confidence_score, key_topic, sentiment, suggested_response, email_content)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, classification, confidence_score, key_topic, sentiment, suggested_response, email_content))
        
        # O commit é o que finaliza a transação. Se o problema for timeout,
        # este comando falhará, mas o servidor não travará.
        conn.commit()
    except Exception as e:
        # Se a inserção falhar, esta exceção será levantada, mas o Flask tentará retornar o 500
        print(f"ERRO CRÍTICO DE INSERÇÃO: {e}")
        # A requisição /classify falhará, mas o servidor continuará online.
        raise 
    finally:
        if conn:
            conn.close()

# user_id é agora o primeiro argumento
def get_history(user_id):
    """Recupera os últimos 20 registros APENAS para o user_id fornecido."""
    conn = None
    history = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Seleciona registros FILTRANDO por user_id
        cursor.execute("""
            SELECT classification, created_at, email_content, suggested_response, key_topic, sentiment
            FROM classifications
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 20
        """, (user_id,))
        
        rows = cursor.fetchall()
        
        # Processamento de dados (mantido)
        # ...
        
    except Exception as e:
        print(f"ERRO CRÍTICO DE LEITURA: {e}")
        return [] # Retorna vazio, mas o erro será registrado
    finally:
        if conn:
            conn.close()
            
    return history

# user_id é agora o primeiro argumento
def get_raw_history_data(user_id):
    """Recupera TODOS os campos APENAS para o user_id fornecido para exportação CSV."""
    conn = None
    raw_history = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Seleciona TODOS os campos FILTRANDO por user_id
        cursor.execute("""
            SELECT id, created_at, classification, confidence_score, email_content, suggested_response, key_topic, sentiment
            FROM classifications
            WHERE user_id = %s
            ORDER BY created_at ASC
        """, (user_id,))
        
        rows = cursor.fetchall()

        for row in rows:
            raw_history.append({
                'id': row[0],
                'created_at': row[1].isoformat() if isinstance(row[1], datetime.datetime) else row[1],
                'classification': row[2],
                'confidence_score': row[3],
                'email_content': row[4],
                'suggested_response': row[5],
                'key_topic': row[6],
                'sentiment': row[7]
            })
            
    except Exception as e:
        print(f"Erro ao recuperar dados brutos para exportação: {e}")
        return []
    finally:
        if conn:
            conn.close()
            
    return raw_history

if __name__ == '__main__':
    initialize_db()