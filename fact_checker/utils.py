from urllib.parse import urlparse

def get_domain_from_url(url):
    """Estrae il dominio pulito da un URL (es. 'www.repubblica.it' -> 'repubblica.it')."""
    try:
        domain = urlparse(url).netloc
        if domain.startswith('www.'):
            return domain[4:]
        return domain
    except:
        return None