import os
import psycopg
from db.sql.queries import insert_embeddings_query, get_documents_query

DSN = os.getenv("DSN")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")

def get_conn():
    conn = psycopg.connect(DSN)
    with conn.cursor() as cur:
        # ensure every session knows where Ollama is
        cur.execute("SELECT set_config('ai.ollama_host', %s, false);", (OLLAMA_HOST,))
    return conn

