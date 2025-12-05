import csv
import os

RESULTS_FILE_PATH = "output/evaluation_results.csv"

# Come consideriamo le etichette di PolitiFact
PF_POSITIVE_LABELS = {'true', 'mostly-true', 'half-true'}
PF_NEGATIVE_LABELS = {'false', 'pants-on-fire', 'mostly-false'}

# Come consideriamo le etichette del nostro RAG
RAG_POSITIVE_PREDICTION = {'SUPPORTED'}
RAG_NEGATIVE_PREDICTION = {'NEGATE'}
RAG_NO_PREDICTION = {'BASELESS', 'ERRORE'}


def analyze_full_metrics():
    """
    Calcola la matrice di confusione e le metriche (Precision, Recall, F1)
    usando una mappatura "tollerante" che include 'half-true' e 'mostly-false'.
    """
    if not os.path.exists(RESULTS_FILE_PATH):
        print(f"ERRORE: File dei risultati non trovato: {RESULTS_FILE_PATH}")
        return

    # Contatori per la Matrice di Confusione
    tp = 0  # True Positive
    fp = 0  # False Positive
    tn = 0  # True Negative
    fn = 0  # False Negative
    
    total_rows = 0
    rag_failures = 0 # 'BASELESS' o 'ERRORE'

    try:
        with open(RESULTS_FILE_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows += 1
                pf_label = row.get('politifact_label', '').lower().strip()
                rag_label = row.get('rag_label', '').upper().strip()

                # --- 1. Filtra i fallimenti del RAG ---
                # Se il RAG non ha fatto una previsione, non possiamo valutarlo.
                if rag_label in RAG_NO_PREDICTION:
                    rag_failures += 1
                    continue
                
                # --- 2. Determina la Verità e la Previsione ---
                is_pf_positive = pf_label in PF_POSITIVE_LABELS
                is_pf_negative = pf_label in PF_NEGATIVE_LABELS
                
                # Se l'etichetta PF non è in nessuna delle nostre liste, la saltiamo
                if not is_pf_positive and not is_pf_negative:
                    continue

                is_rag_positive = rag_label in RAG_POSITIVE_PREDICTION
                is_rag_negative = rag_label in RAG_NEGATIVE_PREDICTION

                # --- 3. Popola la Matrice di Confusione ---
                if is_rag_positive and is_pf_positive:
                    tp += 1
                elif is_rag_positive and is_pf_negative:
                    fp += 1
                elif is_rag_negative and is_pf_negative:
                    tn += 1
                elif is_rag_negative and is_pf_positive:
                    fn += 1

    except Exception as e:
        print(f"ERRORE durante la lettura del file: {e}")
        return

    # --- 4. Calcola le Metriche ---
    total_evaluated = tp + fp + tn + fn
    
    # Gestione divisione per zero (se non ci sono TP, FP, ecc.)
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


    # --- 5. Stampa il Report ---
    print("\n--- Analisi Metriche RAG (Approccio 'Tollerante') ---")
    print(f"Totale Claim Processati: {total_rows}")
    print(f"Claim Ignorati (BASELESS/ERRORE): {rag_failures}")
    print("-------------------------------------------------")
    print(f"Totale Claim Valutati (con mappatura tollerante): {total_evaluated}")
    print("\nMatrice di Confusione:")
    print(f"  - True Positives (TP):  {tp}")
    print(f"    (RAG ha detto SUPPORTED e PF era true/mostly-true/half-true)")
    print(f"  - True Negatives (TN):  {tn}")
    print(f"    (RAG ha detto NEGATE e PF era false/mostly-false/pants-on-fire)")
    print(f"  - False Positives (FP): {fp}")
    print(f"    (RAG ha detto SUPPORTED ma PF era falso/mostly-false/pants-on-fire)")
    print(f"  - False Negatives (FN): {fn}")
    print(f"    (RAG ha detto NEGATE ma PF era true/mostly-true/half-true)")
    print("\n-------------------------------------------------")
    print("Metriche di Performance:")
    print(f"  - Accuratezza (Accuracy):  {(accuracy * 100):.1f}%")
    print(f"  - Precisione (Precision):  {(precision * 100):.1f}%")
    print(f"  - Richiamo (Recall):       {(recall * 100):.1f}%")
    print(f"  - F1-Score:                {(f1_score * 100):.1f}%")
    print(f"  - Specificità (TNR):     {(specificity * 100):.1f}%")

if __name__ == "__main__":
    analyze_full_metrics()