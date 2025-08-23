import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import os
import psycopg
import re
from db.sql.queries import *

PROD_DB = os.getenv("PROD_DB")
LOCAL_DB = os.getenv("LOCAL_DB")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")

def get_rag_db_conn():
    conn = psycopg.connect(LOCAL_DB)
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('ai.ollama_host', %s, false);", (OLLAMA_HOST,))
    return conn

def get_prod_connection():
    conn = psycopg.connect(PROD_DB)
    return conn

def get_documents():
    with get_prod_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(get_documents_query)
            documents = cur.fetchall()
    
    return documents
        
def insert_embeddings():
    documents = get_documents()

    with get_rag_db_conn() as conn:
        with conn.cursor() as cur:
            for doc in documents:
                print(f"Inserting document: {doc[0]}")
                cur.execute(insert_embeddings_query, (doc[0], doc[0]))
        conn.commit()
   
def get_response():
    user_question = '59328 numaralı sevkiyat hakkında bilgi ver'
    
    with get_rag_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(hybrit_search_query, (user_question, user_question))
            documents = cur.fetchone()[0]
            
            documents = re.sub(r'\\n+', ' ', documents)
            documents = documents.replace("'", "")
            documents = re.sub(r'\s+', ' ', documents).strip()
            
            cur.execute(get_response_from_llm_query(str(user_question), str(documents)))

            response = cur.fetchone()
            return response
    

