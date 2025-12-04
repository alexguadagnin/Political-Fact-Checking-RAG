from tavily import TavilyClient
from config.settings import TAVILY_API_KEY, TAVILY_MAX_RESULTS

class TavilyRetriever:
    def __init__(self):
        self.client = TavilyClient(api_key=TAVILY_API_KEY)
        self.max_results = TAVILY_MAX_RESULTS
        
    def search(self, claim_query):
        """
        Interroga Tavily usando il claim in linguaggio naturale
        e ottiene un contesto pulito e le fonti.
        """
        try:
            response = self.client.search(
                query=claim_query,
                search_depth="advanced", 
                include_raw_content=False, 
                max_results=self.max_results
            )
            
            # La lista di risultati è nella chiave 'results'
            return response.get('results', []) 
        
        except Exception as e:
            print(f"Errore durante la chiamata a Tavily: {e}")
            return []