import csv
import os
from fact_checker.pipeline import FactCheckPipeline


# 1. Specifica il percorso del tuo file CSV di PolitiFact
INPUT_FILE_PATH = "data/politifact.csv"

# 2. Questo sarà il nostro file di output e di checkpoint
OUTPUT_FILE_PATH = "output/evaluation_results.csv"

# 3. Quante *nuove* righe vogliamo processare in questo batch
EVALUATION_LIMIT = 250

# 4. Le colonne del nostro file di output
OUTPUT_HEADERS = ['claim', 'politifact_label', 'rag_label', 'rag_motivation']


def load_processed_claims(filepath):
    """
    Legge il file di output per capire quali claim abbiamo GIA' processato.
    Questo è il nostro meccanismo di CHECKPOINT.
    """
    processed_claims = set()
    
    # Assicurati che la cartella 'output/' esista
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    try:
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'claim' in row:
                    processed_claims.add(row['claim'])
        print(f"Trovati {len(processed_claims)} claim già processati. Saranno saltati.")
    except FileNotFoundError:
        # È la prima esecuzione, il file non esiste ancora.
        print("File di output non trovato. Inizio una nuova esecuzione.")
        # Creiamo il file e scriviamo l'intestazione
        with open(filepath, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_HEADERS)
            writer.writeheader()
    
    return processed_claims

def run_evaluation():
    """
    Esegue il batch di valutazione sul dataset PolitiFact.
    """
    if not os.path.exists(INPUT_FILE_PATH):
        print(f"ERRORE: File di input non trovato: {INPUT_FILE_PATH}")
        print("Per favore, imposta il percorso corretto in 'INPUT_FILE_PATH' in evaluate.py")
        return

    # 1. Carica i claim già processati per il checkpoint
    processed_claims = load_processed_claims(OUTPUT_FILE_PATH)
    
    # 2. Inizializza la pipeline RAG
    pipeline = FactCheckPipeline()
    
    new_rows_processed = 0
    
    # 3. Apri entrambi i file: leggiamo dall'input e scriviamo (in append) sull'output
    try:
        with open(INPUT_FILE_PATH, mode='r', encoding='utf-8') as infile, \
             open(OUTPUT_FILE_PATH, mode='a', encoding='utf-8', newline='') as outfile:
            
            # Usiamo DictReader per leggere facilmente le colonne per nome
            reader = csv.DictReader(infile)
            
            # Usiamo DictWriter per scrivere facilmente le colonne per nome
            writer = csv.DictWriter(outfile, fieldnames=OUTPUT_HEADERS)

            for row in reader:
                # 4. Estrai i dati dal CSV di PolitiFact
                claim = row.get('quote', '').strip().replace('â\x80\x9c', '“').replace('â\x80\x9d', '”')
                politifact_label = row.get('rating_label', '').strip()
                
                # --- NUOVA PARTE: ESTRAZIONE METADATI ---
                metadata = {
                    'author': row.get('author', '').strip(),
                    'context': row.get('context', '').strip(),
                    'date': row.get('date', '').strip()
                }

                if not claim:
                    continue # Salta righe vuote

                # 5. LOGICA DI CHECKPOINT:
                if claim in processed_claims:
                    continue # Già fatto, salta

                # 6. LOGICA DI BATCH:
                if new_rows_processed >= EVALUATION_LIMIT:
                    print(f"Limite di {EVALUATION_LIMIT} nuove righe raggiunto. Interrompo il batch.")
                    break # Abbiamo finito il nostro batch da 100

                # 7. Esegui il RAG (Questa è la chiamata API a pagamento!)
                print(f"Processing ({new_rows_processed + 1}/{EVALUATION_LIMIT}): {claim[:70]}...")
                rag_result = pipeline.run(claim, metadata)
                
                # 8. Prepara la riga di output
                output_row = {
                    'claim': claim,
                    'politifact_label': politifact_label,
                    'rag_label': rag_result.get('verdetto'),
                    'rag_motivation': rag_result.get('motivazione')
                }
                
                # 9. Scrivi il risultato IMMEDIATAMENTE (salva i progressi)
                writer.writerow(output_row)
                processed_claims.add(claim) # Aggiorna il nostro set in memoria
                new_rows_processed += 1

    except Exception as e:
        print(f"\nERRORE durante l'elaborazione: {e}")
        print("Il processo è stato interrotto, ma i risultati finora ottenuti sono salvi in " + OUTPUT_FILE_PATH)

    print(f"\nValutazione batch completata. {new_rows_processed} nuove righe processate.")

if __name__ == "__main__":
    run_evaluation()