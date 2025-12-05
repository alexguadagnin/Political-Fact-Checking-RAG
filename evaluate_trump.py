import csv
import os
import sys
from fact_checker.pipeline import FactCheckPipeline

# --- IMPOSTAZIONI ---
INPUT_FILE_PATH = "trump-truth/trump_posts_classified.csv"
OUTPUT_FILE_PATH = "output/trump_results.csv"

# Nomi colonne confermati dal debug
TEXT_COLUMN = 'post_text'      
CLASS_COLUMN = 'classification' 
TARGET_LABEL = 'CLAIM'

# Batch Size
BATCH_SIZE = 500 

OUTPUT_HEADERS = ['claim_text', 'rag_label', 'rag_motivation']

# Aumenta limite CSV
try:
    csv.field_size_limit(500000)
except OverflowError:
    csv.field_size_limit(sys.maxsize // 10)

def count_remaining_work(filepath, class_col, target_val, processed_set):
    total_claims_in_file = 0
    claims_left_to_do = 0
    
    if not os.path.exists(filepath):
        return 0, 0

    try:
        # USA utf-8-sig PER GESTIRE IL BOM (\ufeff)
        with open(filepath, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Verifica preliminare colonne
            if TEXT_COLUMN not in reader.fieldnames:
                print(f"❌ ERRORE FATALE: La colonna '{TEXT_COLUMN}' non esiste nel CSV!")
                print(f"Colonne trovate: {reader.fieldnames}")
                return 0, 0

            for i, row in enumerate(reader):
                # È un CLAIM?
                if row.get(class_col, '').strip() == target_val:
                    total_claims_in_file += 1
                    
                    claim_txt = row.get(TEXT_COLUMN, '').strip()
                    
                    # DEBUG: Se trova il claim ma il testo è vuoto
                    if not claim_txt:
                        print(f"⚠️ ATTENZIONE: Riga {i+2} è CLASSIFIED come CLAIM ma il testo è vuoto!")
                        continue

                    # È già stato fatto?
                    if claim_txt not in processed_set:
                        claims_left_to_do += 1
                        
    except Exception as e:
        print(f"Errore lettura preliminare: {e}")
        return 0, 0
        
    return total_claims_in_file, claims_left_to_do

def load_processed_claims(filepath):
    processed = set()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    try:
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'claim_text' in row:
                    processed.add(row['claim_text'])
    except FileNotFoundError:
        with open(filepath, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_HEADERS)
            writer.writeheader()
    return processed

def run_batch_evaluation():
    if not os.path.exists(INPUT_FILE_PATH):
        print(f"ERRORE: File input non trovato: {INPUT_FILE_PATH}")
        return

    print("--- 1. Caricamento Checkpoint ---")
    processed_claims = load_processed_claims(OUTPUT_FILE_PATH)
    print(f"Claim già analizzati e salvati: {len(processed_claims)}")

    print(f"Analisi del file di input...")
    total_claims, remaining = count_remaining_work(INPUT_FILE_PATH, CLASS_COLUMN, TARGET_LABEL, processed_claims)

    to_process_now = min(remaining, BATCH_SIZE)

    print("\n" + "="*60)
    print(f"📊 STATO DEL PROGETTO")
    print(f"   Totale Claim nel file:      {total_claims}")
    print(f"   Già completati:             {len(processed_claims)}")
    print(f"   Rimanenti da fare:          {remaining}")
    print("-" * 60)
    print(f"📦 BATCH CORRENTE:             {to_process_now} claim")
    est_cost = to_process_now * 0.015
    print(f"💰 Costo stimato per questo batch: ~${est_cost:.2f}")
    print("="*60)

    if to_process_now == 0:
        if remaining == 0 and total_claims > 0:
             print("✅ Tutti i claim validi sono stati processati!")
        elif total_claims == 0:
             print("❌ Non ho trovato nessun CLAIM nel file. Controlla la colonna 'classification'.")
        return

    confirm = input(f"\nVuoi avviare l'analisi per questo blocco di {to_process_now} claim? (s/n): ").lower()
    if confirm != 's':
        print("Operazione annullata.")
        return

    print("\n🚀 Avvio Pipeline RAG...")
    pipeline = FactCheckPipeline()
    new_processed_count = 0
    
    try:
        # Usa utf-8-sig anche qui
        with open(INPUT_FILE_PATH, mode='r', encoding='utf-8-sig') as infile, \
             open(OUTPUT_FILE_PATH, mode='a', encoding='utf-8', newline='') as outfile:
            
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=OUTPUT_HEADERS)

            for row in reader:
                if new_processed_count >= to_process_now:
                    break

                classification = row.get(CLASS_COLUMN, '').strip()
                claim = row.get(TEXT_COLUMN, '').strip()

                if classification != TARGET_LABEL: continue
                if not claim: continue
                if claim in processed_claims: continue

                print(f"[{new_processed_count + 1}/{to_process_now}] Analisi: {claim[:50]}...")
                
                # --- ESECUZIONE RAG ---
                metadata = {} 
                # Se nel CSV hai la data, puoi passarla:
                if 'date' in row: metadata['date'] = row['date']

                rag_result = pipeline.run(claim, metadata)
                
                output_row = {
                    'claim_text': claim,
                    'rag_label': rag_result.get('verdetto'),
                    'rag_motivation': rag_result.get('motivazione')
                }
                
                writer.writerow(output_row)
                processed_claims.add(claim) 
                new_processed_count += 1

    except Exception as e:
        print(f"\n❌ ERRORE CRITICO: {e}")
        return

    print(f"\n✅ Batch completato! {new_processed_count} claim salvati.")

if __name__ == "__main__":
    run_batch_evaluation()