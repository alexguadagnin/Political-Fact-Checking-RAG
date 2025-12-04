from .retriever import TavilyRetriever
from .reranker import CredibilityReranker
from .generator import LLMGenerator
from config.settings import TOP_K_ARTICLES 

class FactCheckPipeline:
    def __init__(self):
        self.retriever = TavilyRetriever()
        self.reranker = CredibilityReranker()
        self.generator = LLMGenerator()

    def run(self, claim, metadata={}): 
        """
        Esegue la pipeline di fact-checking completa di Re-Ranking.
        """
        
        # --- FASE 1: PIANIFICAZIONE QUERY ---
        tavily_query = self.generator.generate_tavily_query(claim, metadata)
        
        # --- FASE 2: RECUPERO ---
        print("Fase 1b: Recupero contesto con Tavily...")
        evidence_results = self.retriever.search(tavily_query)
        
        if not evidence_results:
            return {"verdetto": "BASELESS", "motivazione": "Nessuna informazione trovata da Tavily.", "evidence": []}

        # --- NUOVA FASE: RE-RANKING ---
        print(f"Fase 2a: Trovati {len(evidence_results)} frammenti. Riordino per credibilità...")
        reranked_evidence = self.reranker.rank(evidence_results)
        
        # --- FASE 3: PREPARAZIONE CONTESTO ---
        # Selezioniamo i Top-K DOPO il re-ranking
        final_evidence = reranked_evidence[:TOP_K_ARTICLES]
        
        print(f"Fase 2b: Selezionati i Top {len(final_evidence)} articoli più credibili per il Giudice.")
        context = ""
        for i, doc in enumerate(final_evidence):
            context += f"PROVA {i+1} (Fonte: {doc.get('url')})\n"
            context += f"CONTENUTO: {doc.get('content', 'N/A')}\n\n"
            
        # --- FASE 4: GENERAZIONE VERDETTO ---
        print("Fase 3: Generazione verdetto LLM...")
        result = self.generator.generate_verdict(claim, context)
        
        result['evidence'] = final_evidence
        return result