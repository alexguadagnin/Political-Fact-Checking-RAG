from fact_checker.pipeline import FactCheckPipeline

def run_fact_check():
    print("--- Avvio Fact-Checker RAG ---")
    
    # Esempio di claim da verificare
    claim = "A proposed constitutional amendment âwould allow anyone to run for a 3rd term. Including â Barack Obama.â" #false
    #claim = "Says Tim Walz said he carried weapons in war, but âhe has not spent a day in a combat zone.â" #true
    
    # 1. Inizializza la pipeline
    pipeline = FactCheckPipeline()
    
    # 2. Esegui la pipeline
    result = pipeline.run(claim)
    
    # 3. Stampa il risultato
    print("\n--- RISULTATO FINALE ---")
    print(f"CLAIM: {claim}")
    print(f"VERDETTO: {result.get('verdetto')}")
    print(f"MOTIVAZIONE: {result.get('motivazione')}")
    print("\n--- Prove utilizzate ---")

    # --- ECCO LA CORREZIONE ---
    # Il risultato di Tavily non ha 'source':{'name'}, ma ha 'url' e 'title'
    evidence_list = result.get('evidence', [])
    if not evidence_list:
        print("Nessuna prova trovata.")
    else:
        for i, article in enumerate(evidence_list):
            # Usiamo 'title' e 'url' che sono le chiavi corrette di Tavily
            print(f"Prova {i+1}: {article.get('title', 'Titolo non disponibile')} (Fonte: {article.get('url', 'URL non disponibile')})")

if __name__ == "__main__":
    run_fact_check()