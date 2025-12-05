import pandas as pd
import numpy as np

# Nome del file di input e output
INPUT_FILE = 'trump_truth_social_posts.csv'
OUTPUT_FILE = 'trump_posts_cleaned.csv'

print(f"Caricamento dataset da '{INPUT_FILE}'...")
try:
    df = pd.read_csv(INPUT_FILE)
except FileNotFoundError:
    print(f"Errore: File '{INPUT_FILE}' non trovato.")
    print("Assicurati di aver prima eseguito lo script di scraping.")
    exit()

print(f"Numero totale di post originali: {len(df)}")

# --- Inizio Fase 1: Filtro Semplice ---

# 0. Preparazione: gestisci valori mancanti (NaN) e rimuovi spazi extra
# Questo evita errori nelle prossime fasi
df_cleaned = df.copy()
df_cleaned['post_text'] = df_cleaned['post_text'].fillna('').str.strip()

# 1. Filtro: Rimuovi i Re-Post (basato sulla colonna 'repost_flag')
# Questo è il modo più affidabile, meglio che cercare 'RT @'
initial_count = len(df_cleaned)
df_cleaned = df_cleaned[df_cleaned['repost_flag'] == False]
print(f"Filtro [repost_flag]: Rimossi {initial_count - len(df_cleaned)} re-post.")

# 2. Filtro: Rimuovi post troppo corti (sotto i 10 caratteri, come hai chiesto)
initial_count = len(df_cleaned)
df_cleaned = df_cleaned[df_cleaned['post_text'].str.len() > 10]
print(f"Filtro [Lunghezza < 10]: Rimossi {initial_count - len(df_cleaned)} post.")

# 3. Filtro: Rimuovi placeholder [Image] o [Video]
initial_count = len(df_cleaned)
placeholders = ['[Image]', '[Video]']
df_cleaned = df_cleaned[~df_cleaned['post_text'].isin(placeholders)]
print(f"Filtro [Placeholder]: Rimossi {initial_count - len(df_cleaned)} post.")

# 4. Filtro: Rimuovi post che sono SOLO link (che iniziano con 'http')
initial_count = len(df_cleaned)
df_cleaned = df_cleaned[~df_cleaned['post_text'].str.startswith('http')]
print(f"Filtro [Solo Link]: Rimossi {initial_count - len(df_cleaned)} post.")
 
# --- Fine Filtri ---

print("\n--- RIEPILOGO ---")
print(f"Post totali prima del filtro: {len(df)}")
print(f"Post rimasti dopo il filtro: {len(df_cleaned)}")
print(f"Percentuale di post 'rumorosi' rimossa: {100 * (len(df) - len(df_cleaned)) / len(df):.2f}%")

# Salvataggio del nuovo dataset pulito
df_cleaned.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
print(f"\nDataset pulito salvato in '{OUTPUT_FILE}'.")

# Mostra un'anteprima dei post "candidati" per la Fase 2
print("\n--- Esempio di post 'puliti' ---")
try:
    print(df_cleaned[['post_id', 'post_text']].sample(5))
except ValueError:
    print("Non ci sono abbastanza post rimasti per mostrare un campione.")