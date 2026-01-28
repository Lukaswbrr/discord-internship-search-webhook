import requests
import os
from supabase import create_client
from ddgs import DDGS
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_data = supabase.table("found_internships").select("link").execute()
existing_links = [item['link'] for item in supabase_data.data]

def verify_link_is_alive(url):
    """
    Visits the URL to check for:
    1. HTTP Errors (404, 403, 500)
    2. Soft 404s (200 OK, but text says 'Job Closed')
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Soft 404 phrases (English & Portuguese)
    dead_phrases = [
        # PT-BR
        "vaga encerrada", "não aceita mais candidaturas", "processo seletivo encerrado",
        "página não encontrada", "oops!", "expirou", "não está mais disponível",
        # EN
        "job closed", "no longer accepting", "page not found", "job expired",
        "position filled", "error 404", "this posting is closed"
    ]

    try:
        # Timeout is low (5s) to keep script fast. 
        r = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        
        # 1. HARD FAIL (Status Code)
        if r.status_code >= 400:
            return False

        # 2. SOFT FAIL (Page Content)
        # We parse only the first 5k characters to save time/memory
        soup = BeautifulSoup(r.text[:50000], "html.parser")
        text_content = soup.get_text(" ", strip=True).lower()
        title_content = soup.title.string.lower() if soup.title else ""

        if any(p in title_content for p in dead_phrases):
            return False
        
        # Check body text (more expensive, so we do it last)
        if any(p in text_content for p in dead_phrases):
            return False

        return True

    except Exception as e:
        # If the request fails (timeout/connection error), assume link is bad/unstable
        return False

def filter_results(results, lang="en"):
    """
    Cleans up search results to remove generic job board pages 
    and keep only specific job listings.
    """
    clean_results = []
    
    # Terms that indicate a generic search page (Bad)
    banned_url_terms = ["/jobs/search", "/remote-brazil-jobs", "linkedin.com/jobs/search", "/blog", "/talks", "not_found", "404"]
    banned_title_terms = ["jobs in", "top 20", "hiring now", "search for"]
    ptbr_banned_title_terms = ["vagas de", "top 20", "contratando agora", "buscar por", "pleno", "sênior"]
    
    # checks body term from DGBG first, then in the live page later
    ptbr_banned_body_terms = ["vagas encerradas", "inscrições encerradas", "candidaturas encerradas", "não há vagas", "nenhuma vaga encontrada", "pleno", "sênior", "não está mais ativa", "arquivada"]

    for res in results:
        link = res['href']
        body = res["body"]
        title = res['title']
        
        if link in existing_links:
            continue

        # 1. Skip if URL looks like a search aggregator page
        if any(term in link for term in banned_url_terms):
            continue
            
        # 2. Skip if Title looks like a category header
        if any(term in title.lower() for term in banned_title_terms):
            continue

        match lang:
            case "pt":
                if any(term in title.lower() for term in ptbr_banned_title_terms):
                    continue

                if any(term in body.lower() for term in ptbr_banned_body_terms):
                    continue
        
        # 3. Verify link is alive (no 404s or soft 404s)
        if not verify_link_is_alive(link):
            continue
                    
        clean_results.append(res)
        
    return clean_results

def search_brazil_internships():
    """
    Searches for internships specifically in the Brazilian market 
    using Portuguese keywords and local platforms.
    """
    print("Searching Brazil/LatAm specific internships...")
    
    # Portuguese Query: Targets Gupy (huge in Brazil), Programathor, and others
    # search_query = """
    # (site:gupy.io OR site:programathor.com.br OR site:coodesh.com OR site:remotar.com.br OR site:trampos.co)
    # ("estágio" OR "estagiário" OR "trainee" OR "bolsa")
    # ("desenvolvedor" OR "programador" OR "software" OR "front-end" OR "back-end" OR "full stack")
    # (remoto OR "home office")
    # """

    job_boards = [
        "gupy.io",
        "programathor.com.br",
        "coodesh.com",
        "remotar.com.br"
    ]

    ## TODO: add for loop that goes through every job board, makes seperate search requests,
    # adds to a array and checks if the array does not have a duplicate item.
    # this is a way to probably deal with OR statements that ddgs might not handle well.
    
    keywords = "estágio software desenvolvedor remoto"
    searcy_query: str
    total_results = []
    
    for board in job_boards:
        search_query = f'site:{board} ({keywords})'
        results = DDGS().text(search_query, max_results=25)
        total_results.extend(results)

        search_query = ""

    # frozen set
    total_results = list({frozenset(item.items()):item for item in total_results}.values())
    return filter_results(total_results, "pt")


def search_global_internships():
    """
    Searches for global companies hiring in Brazil/LatAm 
    using English keywords and major ATS platforms.
    """
    print("Searching Global/English internships...")
    
    # English Query: Targets global ATS systems but filters for Brazil/LatAm location
    # search_query = """
    # (site:boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com OR site:apply.workable.com OR site:breezy.hr OR site:getonbrd.com)
    # ("intern" OR "internship")
    # ("software engineer" OR "web developer" OR "full stack")
    # (remote OR "work from home")
    # ("brazil" OR "latin america" OR "south america" OR "anywhere")
    # """

    job_boards = [
        "boards.greenhouse.io",
        "jobs.lever.co",
        "jobs.ashbyhq.com",
        "apply.workable.com",
        "breezy.hr",
        "getonbrd.com"
    ]

    ## TODO: add for loop that goes through every job board, makes seperate search requests,
    # adds to a array and checks if the array does not have a duplicate item.
    # this is a way to probably deal with OR statements that ddgs might not handle well.
    
    keywords = "intern software developer remote"
    searcy_query: str
    total_results = []
    
    for board in job_boards:
        search_query = f'site:{board} ({keywords})'
        results = DDGS().text(search_query, max_results=25)
        total_results.extend(results)

        search_query = ""

    total_results = list({frozenset(item.items()):item for item in total_results}.values())
    return filter_results(total_results)

def search_brazil_github_internships():
    """
    Searches GitHub Jobs for internships with Brazil/LatAm location.
    """
    print("Searching GitHub Jobs internships...")
    
    github_query = """
    site:github.com ("internship" OR "estágio") ("2026") ("Brazil" OR "Brasil" OR "LatAm") "README.md"
    """
    
    results = DDGS().text(github_query, max_results=100)
    return filter_results(results)