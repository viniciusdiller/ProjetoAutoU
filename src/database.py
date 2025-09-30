import sqlite3
import datetime
import os

# "/tmp" para Vercel ou normal para localhost
if os.getenv('VERCEL'): 
    DATABASE_NAME = '/tmp/emails.db'
else:
    DATABASE_NAME = 'emails.db'

def add_column_if_not_exists(cursor, column_name, column_type):
    """Adiciona uma coluna à tabela 'classifications' se ela ainda não existir."""
    try:
        # Tenta selecionar a coluna. Se falhar, ela não existe.
        cursor.execute(f"SELECT {column_name} FROM classifications LIMIT 1")
    except sqlite3.OperationalError:
        print(f"ADICIONANDO COLUNA: {column_name}")
        cursor.execute(f"ALTER TABLE classifications ADD COLUMN {column_name} {column_type}")

def initialize_db():
    # Cria a tabela de histórico se ela não existir
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    # 1. Criação da Tabela (se não existir)
    # Inclui todos os campos mais recentes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classification TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            suggested_response TEXT,
            email_content TEXT,
            created_at TEXT NOT NULL,
            key_topic TEXT,  
            sentiment TEXT  
        )
    """)
    
    # 2. Lógica de Migração (Garante que colunas de versões anteriores sejam adicionadas)
    add_column_if_not_exists(cursor, 'key_topic', 'TEXT')
    add_column_if_not_exists(cursor, 'sentiment', 'TEXT')
    
    conn.commit()
    conn.close()

def insert_classification(classification, confidence_score, key_topic, sentiment, suggested_response, email_content):
    """Insere um novo registro de classificação no banco de dados."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    created_at = datetime.datetime.now().isoformat()
    # A ordem dos campos na query deve corresponder à ordem na chamada da função em app.py
    cursor.execute("""
        INSERT INTO classifications (classification, confidence_score, key_topic, sentiment, suggested_response, email_content, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (classification, confidence_score, key_topic, sentiment, suggested_response, email_content, created_at))
    conn.commit()
    conn.close()

def get_history():
    # Recupera os últimos 20 registros, incluindo os novos campos.
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT classification, created_at, email_content, suggested_response, key_topic, sentiment
        FROM classifications
        ORDER BY created_at DESC
        LIMIT 20
    """)
    
    history = [
        {
            'classification': row[0],
            'created_at': row[1],
            'email_snippet': row[2].strip().replace('\n', ' ')[:100] + '...' if len(row[2].strip()) > 100 else row[2].strip().replace('\n', ' '),
            'email_content': row[2], 
            'suggested_response': row[3],
            'key_topic': row[4] or 'N/A',
            'sentiment': row[5] or 'N/A'
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return history

def get_raw_history_data():
    # Recupera TODOS os campos para exportação CSV.

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, created_at, classification, confidence_score, email_content, suggested_response, key_topic, sentiment
        FROM classifications
        ORDER BY created_at ASC
    """)
    
    # Mapeia os dados brutos para dicionários
    raw_history = [
        {
            'id': row[0],
            'created_at': row[1],
            'classification': row[2],
            'confidence_score': row[3],
            'email_content': row[4],
            'suggested_response': row[5],
            'key_topic': row[6],
            'sentiment': row[7]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return raw_history

if __name__ == '__main__':
    initialize_db()