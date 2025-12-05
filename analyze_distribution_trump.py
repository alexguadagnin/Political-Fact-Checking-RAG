import csv
import os
from collections import Counter
import random


INPUT_FILE = "output/trump_results.csv"  # File generato da evaluate_trump.py


def analyze_trump_claims():
    if not os.path.exists(INPUT_FILE):
        print(f"ERRORE: File {INPUT_FILE} non trovato.")
        return

    # Contatori
    counts = Counter()
    total = 0
    
    # Liste per salvare esempi da mostrare
    examples = {
        "SUPPORTED": [],
        "NEGATE": [],
        "BASELESS": [],
        "ERRORE": []
    }

    try:
        with open(INPUT_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Recupera tutti i dati in una lista per poterli mescolare (per esempi casuali)
            rows = list(reader)
            random.shuffle(rows)

            for row in rows:
                # Normalizza l'etichetta
                label = row.get('rag_label', 'ERRORE').upper().strip()
                
                # Correggi eventuali etichette sporche se necessario
                if "SUPPORT" in label: label = "SUPPORTED"
                elif "NEGAT" in label: label = "NEGATE"
                elif "BASE" in label: label = "BASELESS"
                
                counts[label] += 1
                total += 1
                
                # Salva fino a 5 esempi per categoria
                if len(examples.get(label, [])) < 5:
                    examples.setdefault(label, []).append(row)

    except Exception as e:
        print(f"Errore lettura file: {e}")
        return

    # --- STAMPA DEL REPORT ---
    print("\n" + "="*50)
    print(f"📊 ANALISI FINALE: CLAIM DI TRUMP SU TRUTH SOCIAL")
    print("="*50)
    print(f"Totale Claim Analizzati: {total}")
    print("-" * 50)

    # Ordine di stampa preferito
    order = ["SUPPORTED", "NEGATE", "BASELESS", "ERRORE"]
    
    for label in order:
        count = counts[label]
        if total > 0:
            perc = (count / total) * 100
        else:
            perc = 0
        
        # Emoji per leggibilità
        icon = "✅" if label == "SUPPORTED" else "❌" if label == "NEGATE" else "🤷" if label == "BASELESS" else "⚠️"
        
        print(f"{icon} {label:<10} : {count:4d}  ({perc:.1f}%)")

    print("-" * 50)
    print("\n🔎 ESEMPI QUALITATIVI (Per la tua relazione):")
    
    for label in order:
        if examples[label]:
            print(f"\n--- Esempi di {label} ---")
            for i, ex in enumerate(examples[label][:3]): # Mostra i primi 3 esempi
                clean_claim = ex['claim_text'].replace("\n", " ")[:100] + "..."
                clean_mot = ex['rag_motivation'].replace("\n", " ")[:150] + "..."
                
                print(f"{i+1}. CLAIM: \"{clean_claim}\"")
                print(f"   MOTIVAZIONE: {clean_mot}")
                print("")

if __name__ == "__main__":
    analyze_trump_claims()