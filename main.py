import requests
import datetime
import os
from supabase import create_client
from search import search_global_internships, search_brazil_github_internships, search_brazil_internships
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def send_alert():
    try:
        results_worldwide = search_global_internships()
        results_brazil = search_brazil_internships()
    except Exception as e:
        discord_failed_payload = {
            "username": "Internship Job Posts Bot", 
            "content": f"## Error occurred during internship search!\n{e}"
        }

        response = requests.post(WEBHOOK_URL, json=discord_failed_payload)
        
        if response.status_code == 204:
            print("Success!")
        else:
            print(f"Discord Failed Payload HTTP Error: {response.status_code}")
        
        return
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_data = supabase.table("found_internships").select("link").execute()
    existing_links = [item['link'] for item in supabase_data.data]

    discord_worldwide_content = "## New Internships found! @everyone"
    discord_brazil_content = "## New Internships found in Brazil! @everyone"

    clear_results_worldwide = []
    clear_results_brazil = []

    for k in results_worldwide:
        if k['href'] in existing_links:
            continue

        if len(discord_worldwide_content) > 1000:
            discord_worldwide_content += "\n\n*And more...*"
            break
        
        clear_results_worldwide.append(k)
        discord_worldwide_content += format_html_data(k)
        supabase.table("found_internships").insert({"title": k['title'], "link": k['href'], "type": "worldwide"}).execute()
    
    for k in results_brazil:
        if k['href'] in existing_links:
            results_brazil.remove(k)
            continue

        if len(discord_brazil_content) > 1000:
            discord_brazil_content += "\n\n*And more...*"
            break

        clear_results_brazil.append(k)
        discord_brazil_content += format_html_data(k)
        supabase.table("found_internships").insert({"title": k['title'], "link": k['href'], "type": "brazil"}).execute()

    if not clear_results_worldwide:
        discord_worldwide_content = "\n\nNo new internships found worldwide."
    
    if not clear_results_brazil:
        discord_brazil_content = "\n\nNo new internships found in Brazil."

    discord_worldwide_payload = {
        "username": "Internship Job Posts Bot (Worldwide)", # Bot name
        "content": discord_worldwide_content # Message content
    }

    discord_brazil_payload = {
        "username": "Internship Job Posts Bot (Brazil)", # Bot name
        "content": discord_brazil_content # Message content
    }

    try:
        response_worldwide = requests.post(WEBHOOK_URL, json=discord_worldwide_payload)
        response_brazil = requests.post(WEBHOOK_URL, json=discord_brazil_payload)

        if response_worldwide.status_code == 204:
            print("Success!")
        else:
            print(f"Discord HTTP Error: {response_worldwide.status_code}")
    
        if response_brazil.status_code == 204:
            print("Success! (Brazil)")
        else:
            print(f"Discord HTTP Error (Brazil): {response_brazil.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def format_html_data(dict_data):
    title = dict_data["title"]
    link = dict_data["href"]
    body = dict_data["body"]

    return f"\n**{title}**\n{link}\n"


send_alert()