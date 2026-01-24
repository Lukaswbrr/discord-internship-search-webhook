from ddgs import DDGS

def filter_results(results, lang="en"):
    """
    Cleans up search results to remove generic job board pages 
    and keep only specific job listings.
    """
    clean_results = []
    
    # Terms that indicate a generic search page (Bad)
    banned_url_terms = ["/jobs/search", "/remote-brazil-jobs", "linkedin.com/jobs/search", "/blog", "/careers"]
    banned_title_terms = ["jobs in", "top 20", "hiring now", "search for"]
    ptbr_banned_title_terms = ["vagas de", "top 20", "contratando agora", "buscar por", "pleno", "sênior", "vagas"]
    ptbr_banned_body_terms = ["vagas encerradas", "inscrições encerradas", "candidaturas encerradas", "não há vagas", "nenhuma vaga encontrada", "pleno", "sênior", "não está mais ativa", "arquivada"]

    for res in results:
        link = res['href']
        body = res["body"]
        title = res['title']
        
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
        
        # TODO: make a 1024 character limit for body to avoid discord api issues.
                    
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
    search_query = """
    (site:boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com OR site:apply.workable.com OR site:breezy.hr OR site:getonbrd.com)
    ("intern" OR "internship")
    ("software engineer" OR "web developer" OR "full stack")
    (remote OR "work from home")
    ("brazil" OR "latin america" OR "south america" OR "anywhere")
    """
    
    results = DDGS().text(search_query, max_results=100)
    return filter_results(results)

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