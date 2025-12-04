# Political Fact-Checking RAG

Un sistema di **Retrieval-Augmented Generation (RAG)** progettato per verificare la veridicità di dichiarazioni politiche in tempo reale, superando i limiti di generalizzazione dei classificatori ML statici tradizionali.


## Caratteristiche Principali
* **Architettura a 4 Stadi:** Pianificatore, Retriever, Re-Ranker, Giudice.
* **Query Planning Dinamico:** Un LLM trasforma il claim in query di ricerca ottimizzate per il fact-checking, gestendo contesti multilingua e temporali.
* **Credibility Re-Ranking:** Un modulo specializzato che riordina i risultati di ricerca premiando le fonti autorevoli (es. Reuters, AP, PolitiFact) per evitare che il modello venga ingannato da fonti di disinformazione.
* **Analisi Sfumata:** Il sistema non si limita a Vero/Falso, ma fornisce motivazioni dettagliate e gestisce casi di ambiguità (`BASELESS`).

## Architettura del Sistema

Il progetto implementa una pipeline avanzata:

1.  **Pianificatore (Planner - gpt-4.1-mini):** Analizza il claim e genera una query di ricerca mirata (es. `"{claim}" fact-check`).
2.  **Retriever (Tavily API):** Esegue una ricerca web profonda recuperando fino a 100 frammenti di contesto.
3.  **Re-Ranker:** Filtra e riordina i risultati basandosi su una whitelist di domini ad alta affidabilità.
4.  **Giudice (Judge - gpt-5-mini):** Analizza i Top-15 risultati più credibili ed emette un verdetto (`SUPPORTED`, `NEGATE`, `BASELESS`) con motivazione.

## 📊 Performance

Il sistema è stato validato su un test set estratto da PolitiFact.

| Metrica | Risultato |
| :--- | :--- |
| **Accuracy** | **93.6%** |
| **Precision** | **84.6%** |
| **Recall** | **58.9%** |
| **F1-Score** | **69.5%** |
| **Specificity (TNR)** | **98.5%** | 
