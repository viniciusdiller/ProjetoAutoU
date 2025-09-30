import sqlite3
import datetime
import os

# "/tmp" para Vercel ou normal para localhost
if os.getenv('VERCEL'): 
    DATABASE_NAME = '/tmp/emails.db'
else:
    DATABASE_NAME = 'emails.db'

def initialize_db():
    #Cria a tabela de histórico se ela não existir
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classification TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            suggested_response TEXT,
            email_content TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def insert_classification(classification, confidence_score, suggested_response, email_content):
    """Insere um novo registro de classificação no banco de dados."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    created_at = datetime.datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO classifications (classification, confidence_score, suggested_response, email_content, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (classification, confidence_score, suggested_response, email_content, created_at))
    conn.commit()
    conn.close()

def get_history():
    # Recupera os últimos 20 registros.
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT classification, created_at, email_content, suggested_response
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
            'suggested_response': row[3]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return history

def get_raw_history_data():
    # Recupera TODOS os campos (sem limite) para uso na exportação CSV.

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, created_at, classification, confidence_score, email_content, suggested_response
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
            'suggested_response': row[5]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return raw_history

if __name__ == '__main__':
    initialize_db()