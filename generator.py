from openai import OpenAI
from config.settings import OPENAI_API_KEY, DEEPSEEK_API_KEY, GROQ_API_KEY, NOVITA_API_KEY
import json

class LLMGenerator:
    def __init__(self):
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.query_model = "gpt-4.1-mini"
        self.verdict_model = "gpt-5-mini" 
        

    def _get_fallback_query(self, claim):
        """Genera una query di fallback semplice se l'LLM fallisce."""
        print("ATTENZIONE: Attivazione query di fallback.")
        return claim.strip()
    
    def _clean_and_parse_json(self, raw_content):
        """
        Pulisce la risposta dell'LLM da eventuali blocchi Markdown
        e prova a parsare il JSON.
        """
        if not raw_content:
            raise ValueError("L'LLM ha restituito una risposta vuota.")

        # Rimuove i blocchi di codice Markdown ```json ... ``` se presenti
        cleaned_content = raw_content.strip()
        if "```" in cleaned_content:
            # Usa una regex per estrarre il contenuto tra i backticks
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned_content, re.DOTALL)
            if match:
                cleaned_content = match.group(1)
            else:
                # Fallback semplice: rimuovi solo i primi/ultimi caratteri se sono backticks
                cleaned_content = cleaned_content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(cleaned_content)

    def generate_tavily_query(self, claim, metadata):
        print("--- 1a. Pianificazione Query (Modalità Fact-Check) ---")
        
        metadata_str = ""
        if metadata.get('author'): metadata_str += f"Autore: {metadata.get('author')}\n"
        if metadata.get('context'): metadata_str += f"Contesto: {metadata.get('context')}\n"
        if metadata.get('date'): metadata_str += f"Data: {metadata.get('date')}\n"

        
        full_prompt = (
            f"Agisci come un esperto di ricerca per il fact-checking.\n"
            f"Il tuo compito è generare una stringa di ricerca ottimizzata per Tavily.\n"
            f"L'obiettivo NON è trovare la fonte originale, ma trovare fonti affidabili (fact-checkers, media, report) "
            f"che verifichino o smentiscano il claim.\n"
            f"Includi sempre la parola 'fact-check' o 'verità' nella query.\n\n"
            f"DATI:\n"
            f"CLAIM: \"{claim}\"\n"
            f"METADATI: {metadata_str}\n\n"
            f"RISPONDI SOLO ED ESCLUSIVAMENTE CON UN OGGETTO JSON VALID:\n"
            f"{{\"query\": \"...tua stringa di ricerca...\"}}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.query_model, 
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                max_completion_tokens=1000, 
                response_format={"type": "json_object"} 
            )
            
            raw_content = response.choices[0].message.content
            
            # Debug
            if not raw_content:
                print(f"[DEBUG ERROR] Motivo stop: {response.choices[0].finish_reason}")
                print(f"[DEBUG ERROR] Refusal: {getattr(response.choices[0], 'refusal', 'None')}")
            
            params = self._clean_and_parse_json(raw_content)
            query = params.get('query', '').strip()
            
            print(f"Query Pianificata: {query}")
            return query
            
        except Exception as e:
            print(f"Errore generazione query: {e}")
            return self._get_fallback_query(claim)

    def generate_verdict(self, claim, context):
        """
        Genera un verdetto.
        """
        print("--- Generazione verdetto LLM ---")
        system_prompt = (
            "Sei un analista di fact-checking esperto. Il tuo compito è valutare la veridicità "
            "di un claim basandoti sulle prove fornite."
        )
        
        user_prompt = (
            f"Valuta il seguente claim:\nCLAIM: \"{claim}\"\n\n"
            f"CONTESTO (Prove dal web):\n--- INIZIO CONTESTO ---\n{context}\n--- FINE CONTESTO ---\n\n"
            
            f"⚠️ ISTRUZIONI CRITICHE DI SICUREZZA (LEGGERE ATTENTAMENTE):\n"
            
            f"1. **LA TRAPPOLA DEL FACT-CHECKER:**\n"
            f"   - Se nel contesto vedi un articolo di PolitiFact, Snopes, FactCheck.org, ecc., "
            f"   FAI ATTENZIONE. Spesso questi siti *ripetono* il claim nel titolo o nell'intro "
            f"   prima di smentirlo.\n"
            f"   - Se il testo dice 'Claim: [X]' o 'Fact check: [X]', NON assumere che X sia vero "
            f"   solo perché è scritto sul sito. Cerca il VERDETTO (es. 'False', 'Debunked', 'No evidence', 'Incorrect').\n"
            f"   - Se il fact-checker dice che il claim è Falso, il tuo verdetto DEVE essere `NEGATE`.\n"
            
            f"2. **DISTINGUERE EVENTO DA IMMAGINE:**\n"
            f"   - Se il claim riguarda una FOTO o un VIDEO (es. 'Image shows...'), non basta che l'evento "
            f"   descritto sia accaduto. Devi verificare se *quella specifica immagine* è autentica.\n"
            f"   - Se le prove dicono che l'immagine è AI, modificata o fuori contesto (anche se l'evento è reale), "
            f"   il verdetto è `NEGATE`.\n"
            
            f"3. **FALSI POSITIVI:**\n"
            f"   - Se trovi solo blog sconosciuti o post social che ripetono il claim, ma nessuna fonte "
            f"   autorevole (AP, Reuters, BBC) che lo conferma, sii scettico. Usa `BASELESS` o `NEGATE`.\n"
            
            f"4. **GESTIONE DELLE SFUMATURE:**\n"
            f"   - Usa `SUPPORTED` solo se i fatti chiave sono confermati.\n"
            f"   - Usa `NEGATE` se i fatti chiave sono smentiti.\n\n"
            
            f"Rispondi JSON (in ITALIANO!): {{\"verdetto\": \"...\", \"motivazione\": \"...\"}}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.verdict_model, 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Errore durante la chiamata all'LLM: {e}")
            return {"verdetto": "ERRORE", "motivazione": str(e)}