import csv
import os

# --- CONFIGURAZIONE ---
INPUT_FILE = "output/evaluation_results.csv"  
OUTPUT_FILE = "output/falsi_positivi.csv"     

# Definizioni per l'analisi "Tollerante"
RAG_POSITIVE = 'SUPPORTED'
PF_NEGATIVE_LABELS = {'false', 'pants-on-fire', 'mostly-false'}
# ----------------------

def extract_false_positives():
    if not os.path.exists(INPUT_FILE):
        print(f"Errore: File {INPUT_FILE} non trovato.")
        return

    fp_count = 0
    
    try:
        with open(INPUT_FILE, mode='r', encoding='utf-8') as infile, \
             open(OUTPUT_FILE, mode='w', encoding='utf-8', newline='') as outfile:
            
            reader = csv.DictReader(infile)
            # Copiamo le intestazioni originali
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()

            print(f"Analisi di {INPUT_FILE} in corso...")

            for row in reader:
                rag_label = row.get('rag_label', '').upper().strip()
                pf_label = row.get('politifact_label', '').lower().strip()

                # Logica Falso Positivo:
                # RAG dice "SUPPORTED" MA PolitiFact dice "Falso/Pants-on-fire/Mostly-false"
                if rag_label == RAG_POSITIVE and pf_label in PF_NEGATIVE_LABELS:
                    writer.writerow(row)
                    fp_count += 1

        print(f"\n✅ Estrazione completata.")
        print(f"Trovati {fp_count} Falsi Positivi.")
        print(f"Salvati in: {OUTPUT_FILE}")

    except Exception as e:
        print(f"Errore durante l'elaborazione: {e}")

if __name__ == "__main__":
    extract_false_positives()