from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3.2:3b",                   
    base_url="http://localhost:11434",  
    temperature=0,
    keep_alive=-1                       
)