import os
from dotenv import load_dotenv

# Carica le variabili dal file .env che si trova nella cartella principale
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Rendi disponibili le chiavi API
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NOVITA_API_KEY = os.getenv("NOVITA_API_KEY")

# Impostazioni RAG
TAVILY_MAX_RESULTS = 100 # Recuperiamo il massimo possibile
TOP_K_ARTICLES = 30      # Passiamo i migliori 20 all'LLM