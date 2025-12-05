import requests
import pandas as pd
import time

# L'URL di base dell'API che hai trovato
BASE_URL = "http://api.factsquared.com/json/factba.se-trump-social.php"

# Parametri che rimangono fissi
PARAMS = {
    'q': '',
    'platform': 'Truth Social',
    'sort': 'date',
    'sort_order': 'desc'
}

def get_all_posts():
    """
    Esegue lo scraping di tutte le pagine dell'API di Factba.se
    e restituisce un elenco di tutti i post.
    """
    
    all_posts_data = []
    page_num = 1
    total_pages = 1 # Inizializziamo a 1, verrà aggiornato alla prima chiamata
    
    print("Avvio dello scraping dell'API di Factba.se...")

    while True:
        # Imposta il numero di pagina corrente nei parametri
        PARAMS['page'] = page_num
        
        try:
            # Esegui la richiesta GET all'API
            response = requests.get(BASE_URL, params=PARAMS)
            response.raise_for_status() # Controlla se ci sono errori HTTP
            
            data = response.json()
            
            # Aggiorna il numero totale di pagine alla prima iterazione
            if page_num == 1:
                total_pages = data['meta']['page_count']
                print(f"Trovate {data['meta']['total_hits']} post su {total_pages} pagine.")

            # Estrai i post dalla risposta
            posts_in_page = data.get('data', [])
            if not posts_in_page:
                print("Nessun altro post trovato. Uscita.")
                break # Esce se la pagina è vuota

            # Estrai i dati che ci interessano
            for post in posts_in_page:
                social_data = post.get('social', {})
                all_posts_data.append({
                    'date': post.get('date'),
                    'post_id': post.get('document_id'),
                    'post_text': social_data.get('post_text'),
                    'post_url': post.get('post_url'),
                    'repost_flag': social_data.get('repost_flag'),
                    'urls_in_post': ", ".join(social_data.get('urls', [])), # Unisce le URL in una stringa
                    'hashtags': ", ".join(social_data.get('hashtags', [])), # Unisce gli hashtag
                })

            print(f"Pagina {page_num}/{total_pages} scaricata. ({len(all_posts_data)} post totali)")

            # Controlla se abbiamo finito
            if page_num >= total_pages:
                print("Scraping completato. Tutte le pagine sono state scaricate.")
                break
                
            # Incrementa la pagina e attendi per non sovraccaricare il server
            page_num += 1
            time.sleep(0.5) # Pausa di mezzo secondo tra una richiesta e l'altra

        except requests.exceptions.RequestException as e:
            print(f"Errore durante la richiesta alla pagina {page_num}: {e}")
            print("Attendo 10 secondi e riprovo...")
            time.sleep(10)
            
    return all_posts_data

# --- ESECUZIONE ---
posts_list = get_all_posts()

if posts_list:
    print(f"\nDownload completato. Totale post estratti: {len(posts_list)}")
    
    # Converti la lista di post in un DataFrame pandas
    df = pd.DataFrame(posts_list)
    
    # Salva il DataFrame in un file CSV
    output_file = 'trump_truth_social_posts.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"Dati salvati con successo in '{output_file}'")
    
    # Mostra i primi 5 post
    print("\n--- Anteprima dei dati ---")
    print(df.head())