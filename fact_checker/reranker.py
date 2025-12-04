import json
import os
from .utils import get_domain_from_url

class CredibilityReranker:
    def __init__(self):
        self.scores = {}
        self.default_score = 3
        
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'sources.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.default_score = config['sources'].get('default_score', 3)
            
            # Carica i punteggi appiattendo la struttura JSON
            for category, data in config['sources'].items():
                if isinstance(data, dict) and 'domains' in data:
                    score = data.get('score', self.default_score)
                    for domain in data['domains']:
                        self.scores[domain] = score
                        
            print(f"Re-Ranker caricato con {len(self.scores)} domini autorevoli.")
            
        except FileNotFoundError:
            print("ATTENZIONE: config/sources.json non trovato. Il Re-Ranker userà solo punteggi di default.")
        except Exception as e:
            print(f"Errore durante il caricamento di sources.json: {e}")

    def rank(self, articles):
        """
        Riordina una lista di articoli (da Tavily) in base al punteggio di credibilità.
        """
        print(f"Re-ranking di {len(articles)} articoli per credibilità...")
        
        reranked_list = []
        for article in articles:
            domain = get_domain_from_url(article.get('url', ''))
            
            # Tavily assegna un suo "score" di rilevanza. Lo usiamo come base.
            relevance_score = article.get('score', 0.0)
            
            # Cerchiamo il nostro punteggio di credibilità
            credibility_score = self.scores.get(domain, self.default_score)
            
            # Calcoliamo un punteggio finale ibrido.
            # Diamo un peso enorme alla credibilità.
            final_score = (credibility_score * 10) + relevance_score
            
            reranked_list.append((final_score, article))
        
        # Ordina per punteggio finale, dal più alto al più basso
        reranked_list.sort(key=lambda x: x[0], reverse=True)
        
        # Restituisci solo gli articoli, senza lo score
        return [article for score, article in reranked_list]