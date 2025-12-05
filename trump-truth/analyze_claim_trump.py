import pandas as pd
import time
import os
import numpy as np
from openai import OpenAI, OpenAIError
from tqdm import tqdm

# --- CONFIGURAZIONE ---
# 1. Incolla la tua chiave API di Novita AI qui
NOVITA_API_KEY = "..." 

# 2. Modello da utilizzare (8B è più veloce ed economico, 70B è più potente)
MODEL_NAME = "meta-llama/llama-3.3-70b-instruct"

# 3. Nomi dei file
INPUT_FILE = 'trump_posts_cleaned.csv'
OUTPUT_FILE = 'trump_posts_classified.csv'
# --- FINE CONFIGURAZIONE ---

# Inizializza il client OpenAI con il base_url di Novita
try:
    client = OpenAI(
        api_key=NOVITA_API_KEY,
        base_url="https://api.novita.ai/openai"
    )

except Exception as e:
    print(f"Errore nell'inizializzazione del client: {e}")
    exit()

# Questo è il "cervello": il prompt che definisce cosa è un claim
SYSTEM_PROMPT = """
Sei un assistente esperto di fact-checking. Il tuo compito è classificare un post sui social media come 'CLAIM' o 'NO_CLAIM'.
Devi valutare se il tweet che ti viene passato necessita di una valutazione di fact checking.

- 'CLAIM': È un'affermazione fattuale specifica che può essere verificata. Contiene fatti, statistiche, o dichiarazioni su eventi specifici.
  - Esempio: "L'economia è cresciuta del 4%."
  - Esempio: "Abbiamo costruito 500 miglia di muro."
  - Esempio: "Il tasso di criminalità è sceso del 10% a Chicago."

- 'NO_CLAIM': È un'opinione, un insulto, una domanda retorica, uno slogan, un'esortazione o un commento vago.
  - Esempio: "Questa è una CACCIA ALLE STREGHE!"
  - Esempio: "Persone magnifiche! Grazie."
  - Esempio: "I Democratici sono un disastro."

Analizza il post dell'utente. Rispondi *solo ed esclusivamente* con la parola 'CLAIM' o la parola 'NO_CLAIM'. NON DEVI aggiungere altre parole.
"""

def classify_post(post_text, retries=3, delay=10):
    """
    Chiama l'API Novita (via client OpenAI) per classificare un singolo post.
    Implementa una logica di retry in caso di fallimento.
    
    *** VERSIONE CORRETTA: usa un controllo esatto (==) invece di (in) ***
    """
    if NOVITA_API_KEY == "LA_TUA_CHIAVE_API_QUI":
        raise ValueError("ERRORE: Inserisci la tua NOVITA_API_KEY nello script.")

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": post_text}
                ],
                max_tokens=5,   # Ci aspettiamo solo "CLAIM" o "NO_CLAIM"
                temperature=0.0 # Vogliamo una risposta deterministica
            )
            
            # Pulisce la risposta: rimuove spazi, converte in maiuscolo, rimuove virgolette
            classification = response.choices[0].message.content.strip().upper()
            classification = classification.replace('"', '').replace("'", "")

            # --- LA LOGICA CORRETTA ---
            # Controlla l'uguaglianza esatta, non la sottostringa
            if classification == "CLAIM":
                return "CLAIM"
            elif classification == "NO_CLAIM":
                return "NO_CLAIM"
            else:
                # Se il modello risponde in modo strano (es. "QUESTO È UN NO_CLAIM")
                # lo sapremo perché verrà classificato come "UNSURE".
                print(f"\n[Warning] Risposta inattesa: '{classification}'")
                return "UNSURE"

        except OpenAIError as e:
            print(f"\n[Errore OpenAI Tentativo {attempt+1}/{retries}] Post: {post_text[:30]}... Errore: {e}")
            if attempt < retries - 1:
                print(f"Riprovo tra {delay} secondi...")
                time.sleep(delay)
            else:
                print("\nMassimo numero di tentativi raggiunto. Marco come 'ERROR'.")
                return "ERROR"
        except Exception as e:
            print(f"\n[Errore Generico] {e}. Marco come 'ERROR'.")
            return "ERROR"
            
    return "ERROR"

def main():
    """
    Funzione principale per caricare, elaborare e salvare il dataset.
    """
    print(f"Caricamento di '{INPUT_FILE}'...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"Errore: File '{INPUT_FILE}' non trovato. Assicurati che sia nella stessa cartella.")
        return

    # Se il file di output esiste, lo carichiamo per riprendere da dove eravamo
    if os.path.exists(OUTPUT_FILE):
        print(f"Trovato file di output esistente '{OUTPUT_FILE}'. Riprendo il lavoro...")
        df_out = pd.read_csv(OUTPUT_FILE)
    else:
        print(f"Creo nuovo file di output '{OUTPUT_FILE}'.")
        df_out = df.copy()
        df_out['classification'] = pd.Series(index=df.index, dtype='object')

    # Filtra solo le righe che non sono ancora state classificate
    to_process = df_out[df_out['classification'].isna()]
    
    if len(to_process) == 0:
        print("Lavoro già completato! Tutti i post sono classificati.")
    else:
        print(f"Avvio classificazione per {len(to_process)} post rimanenti...")

    # Usiamo tqdm per una barra di progresso
    for index, row in tqdm(to_process.iterrows(), total=len(to_process), desc="Classificando i post"):
        post_text = row['post_text']
        
        # Gestisce il caso in cui il testo sia vuoto/NaN anche se non dovrebbe
        if not isinstance(post_text, str) or len(post_text) < 5:
            classification = "NO_CLAIM"
        else:
            classification = classify_post(post_text)
            time.sleep(3.1)

        # Salva il risultato nel DataFrame
        df_out.at[index, 'classification'] = classification
        
        # Salva i progressi ogni 100 post
        if (to_process.index.get_loc(index) + 1) % 100 == 0:
            # print(f"\nSalvataggio progressi...") # Rimuovo per non sporcare la barra tqdm
            df_out.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    # Salvataggio finale
    print("Classificazione completata. Salvataggio finale...")
    df_out.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    
    print("\n--- RIEPILOGO CLASSIFICAZIONE ---")
    print(df_out['classification'].value_counts())

if __name__ == "__main__":
    main()