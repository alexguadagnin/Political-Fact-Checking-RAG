import csv
import os

# Il file CSV generato da evaluate.py
RESULTS_FILE_PATH = "output/evaluation_results.csv" 

PF_TRUE_LABELS = {'true', 'mostly-true'}
PF_FALSE_LABELS = {'false', 'pants-on-fire'}
PF_AMBIGUOUS_LABELS = {'half-true', 'mostly-false'} # Queste verranno IGNORATE

# Come consideriamo le etichette del nostro RAG
RAG_POSITIVE_PREDICTION = {'SUPPORTED'}
RAG_NEGATIVE_PREDICTION = {'NEGATE'}
RAG_NO_PREDICTION = {'BASELESS', 'ERRORE'}

def analyze_strict_metrics():
    """
    Legge il file CSV e calcola le metriche complete (Precision, Recall, F1)
    usando solo i claim "Netti" (ignora 'half-true' e 'mostly-false').
    """
    if not os.path.exists(RESULTS_FILE_PATH):
        print(f"ERRORE: File dei risultati non trovato: {RESULTS_FILE_PATH}")
        return

    # Contatori per le nostre metriche
    total_rows = 0
    rag_failures = 0
    pf_ambiguous = 0
    
    tp = 0  # True Positive
    fp = 0  # False Positive
    tn = 0  # True Negative
    fn = 0  # False Negative

    try:
        with open(RESULTS_FILE_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows += 1
                
                pf_label = row.get('politifact_label', '').lower().strip()
                rag_label = row.get('rag_label', '').upper().strip()

                # --- 1. Filtriamo i fallimenti del RAG ---
                if rag_label in RAG_NO_PREDICTION:
                    rag_failures += 1
                    continue 

                # --- 2. Filtriamo i claim ambigui di PolitiFact ---
                if pf_label in PF_AMBIGUOUS_LABELS:
                    pf_ambiguous += 1
                    continue 

                # --- 3. Valutazione dei claim "Netti" (Veri o Falsi) ---                
                is_pf_true = pf_label in PF_TRUE_LABELS
                is_pf_false = pf_label in PF_FALSE_LABELS
                is_rag_positive = rag_label in RAG_POSITIVE_PREDICTION
                is_rag_negative = rag_label in RAG_NEGATIVE_PREDICTION

                # --- MODIFICA: Popoliamo la Matrice di Confusione ---
                if is_rag_positive and is_pf_true:
                    tp += 1
                elif is_rag_positive and is_pf_false:
                    fp += 1
                elif is_rag_negative and is_pf_false:
                    tn += 1
                elif is_rag_negative and is_pf_true:
                    fn += 1
                # --- FINE MODIFICA ---

    except Exception as e:
        print(f"ERRORE durante la lettura del file: {e}")
        return

    # --- 4. Calcola le Metriche (Copiato da analyze_metrics.py) ---
    total_evaluated = tp + fp + tn + fn
    
    try:
        accuracy = (tp + tn) / total_evaluated
    except ZeroDivisionError:
        accuracy = 0.0
    try:
        precision = tp / (tp + fp)
    except ZeroDivisionError:
        precision = 0.0
    try:
        recall = tp / (tp + fn)
    except ZeroDivisionError:
        recall = 0.0
    try:
        f1_score = 2 * (precision * recall) / (precision + recall)
    except ZeroDivisionError:
        f1_score = 0.0
    try:
        specificity = tn / (tn + fp)
    except ZeroDivisionError:
        specificity = 0.0


    # --- 5. Stampa il Report (Aggiornato) ---
    print("\n--- Analisi Performance RAG (Approccio 'Stretto') ---")
    print(f"   (Ignora 'half-true' e 'mostly-false')")
    print(f"Totale Claim Processati: {total_rows}")
    print("-------------------------------------------------")
    
    print(f"Claim Ignorati (Fallimenti RAG):")
    rag_fail_perc = (rag_failures / total_rows) * 100 if total_rows > 0 else 0
    print(f"  - 'BASELESS' o 'ERRORE': {rag_failures} ({rag_fail_perc:.1f}%)")

    print(f"\nClaim Ignorati (Ambigui PF):")
    ambig_perc = (pf_ambiguous / total_rows) * 100 if total_rows > 0 else 0
    print(f"  - 'half-true', 'mostly-false': {pf_ambiguous} ({ambig_perc:.1f}%)")

    print("\n-------------------------------------------------")
    print(f"Totale Claim Valutati (Netti): {total_evaluated}")
    
    if total_evaluated > 0:
        print("\nMatrice di Confusione (Netti):")
        print(f"  - True Positives (TP):  {tp}")
        print(f"    (RAG ha detto SUPPORTED e PF era true/mostly-true)")
        print(f"  - True Negatives (TN):  {tn}")
        print(f"    (RAG ha detto NEGATE e PF era false/pants-on-fire)")
        print(f"  - False Positives (FP): {fp}")
        print(f"    (RAG ha detto SUPPORTED ma PF era false/pants-on-fire)")
        print(f"  - False Negatives (FN): {fn}")
        print(f"    (RAG ha detto NEGATE ma PF era true/mostly-true)")
        
        print("\n-------------------------------------------------")
        print("Metriche di Performance (Netti):")
        print(f"  - Accuratezza (Accuracy):  {(accuracy * 100):.1f}%")
        print(f"  - Precisione (Precision):  {(precision * 100):.1f}%")
        print(f"  - Richiamo (Recall):       {(recall * 100):.1f}%")
        print(f"  - F1-Score:                {(f1_score * 100):.1f}%")
        print(f"  - Specificità (TNR):     {(specificity * 100):.1f}%")
    else:
        print("Nessun claim è stato valutato (tutti falliti o ambigui).")

if __name__ == "__main__":
    analyze_strict_metrics()