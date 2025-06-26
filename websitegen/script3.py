import requests
from bs4 import BeautifulSoup
from datetime import datetime
from collections import Counter

def search_conferences_by_theme(theme):
    # URL con el formulario de búsqueda
    base_url = "https://easychair.org/cfp/search.cgi" 
    params = {
        "query": theme
    }
    
    # Encabezados para simular una solicitud de un navegador web
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://easychair.org/cfp/", 
        "Connection": "keep-alive"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []
    
    # Depuración: Imprimir la URL y el contenido de la respuesta
    print(f"Request URL: {response.url}")
    print(f"Response Status Code: {response.status_code}")
    # print(f"Response Content:\n{response.text[:1000]}")  # Uncomment to see the first 1000 characters of the response
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extraer entradas de conferencias
    conference_entries = soup.select("#ec\\:table1 tr.blue")  # Selector para cada entrada de conferencia
    
    if not conference_entries:
        print("No conference entries found. Check the HTML structure or the search query.")
        # Imprimir el contenido de la respuesta para depuración
        print(f"Response Content:\n{response.text[:1000]}")  # Mostrar los primeros 1000 caracteres
        return []
    
    current_datetime = datetime.now()
    
    conferences = []
    for entry in conference_entries:
        acronym_tag = entry.select_one("td:first-child a")
        acronym = acronym_tag.text.strip() if acronym_tag else "N/A"
        name = entry.select_one("td:nth-child(2)").text.strip() if entry.select_one("td:nth-child(2)") else "N/A"
        location = entry.select_one("td:nth-child(3)").text.strip() if entry.select_one("td:nth-child(3)") else "N/A"
        
        submission_deadline_tag = entry.select_one("td:nth-child(4) span.cfp_date")
        submission_deadline_str = submission_deadline_tag.text.strip() if submission_deadline_tag else "N/A"
        submission_deadline = parse_date(submission_deadline_str)
        
        start_date_tag = entry.select_one("td:nth-child(5) span.cfp_date")
        start_date_str = start_date_tag.text.strip() if start_date_tag else "N/A"
        start_date = parse_date(start_date_str)
        
        topics_tags = entry.select("td:nth-child(6) a span.tag")
        topics = [topic.text.strip() for topic in topics_tags] if topics_tags else ["N/A"]
        
        link = acronym_tag["href"] if acronym_tag else "N/A"
        
        # Incluir conferencias con N/A en submission deadline o con submission deadline posterior a la fecha actual
        if submission_deadline_str == "N/A" or submission_deadline >= current_datetime:
            conferences.append({
                "acronym": acronym,
                "name": name,
                "location": location,
                "submission_deadline": submission_deadline,
                "start_date": start_date,
                "topics": topics,
                "link": link,
                "raw_submission_deadline": submission_deadline_str,
                "raw_start_date": start_date_str
            })
    
    # Ordenar conferencias por fecha de inicio en orden decreciente
    conferences_sorted = sorted(conferences, key=lambda x: x["start_date"], reverse=True)
    
    return conferences_sorted

def parse_date(date_str):
    # Intentar parsear la fecha en diferentes formatos
    date_formats = ["%b %d, %Y", "%B %d, %Y"]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return datetime.min  # Fallback para fechas inválidas

def print_conferences(conferences):
    if not conferences:
        print("No conferences found for the given theme.")
        return
    
    for conf in conferences:
        print(f"Acronym: {conf['acronym']}")
        print(f"Name: {conf['name']}")
        print(f"Location: {conf['location']}")
        print(f"Submission Deadline: {conf['raw_submission_deadline']}")
        print(f"Start Date: {conf['raw_start_date']}")
        print(f"Topics: {', '.join(conf['topics'])}")
        print(f"Link: https://easychair.org{conf['link']}") 
        print("-" * 40)

def print_metrics(conferences):
    if not conferences:
        print("No metrics to display for the given theme.")
        return
    
    total_conferences = len(conferences)
    conferences_with_deadline = sum(1 for conf in conferences if conf["raw_submission_deadline"] != "N/A")
    conferences_without_deadline = total_conferences - conferences_with_deadline
    
    submission_deadlines = [conf["submission_deadline"] for conf in conferences if conf["submission_deadline"] != datetime.min]
    if submission_deadlines:
        nearest_submission_deadline = min(submission_deadlines).strftime("%b %d, %Y")
    else:
        nearest_submission_deadline = "N/A"
    
    start_dates = [conf["start_date"] for conf in conferences if conf["start_date"] != datetime.min]
    if start_dates:
        latest_start_date = max(start_dates).strftime("%b %d, %Y")
    else:
        latest_start_date = "N/A"
    
    all_topics = [topic for conf in conferences for topic in conf["topics"]]
    topic_counts = Counter(all_topics)
    most_common_topics = topic_counts.most_common(5)  # Top 5 temas más comunes
    
    print("\nMetrics:")
    print(f"Total Conferences Found: {total_conferences}")
    print(f"Conferences with Specific Submission Deadline: {conferences_with_deadline}")
    print(f"Conferences with N/A Submission Deadline: {conferences_without_deadline}")
    print(f"Nearest Submission Deadline: {nearest_submission_deadline}")
    print(f"Latest Start Date: {latest_start_date}")
    print("Top 5 Most Common Topics:")
    for topic, count in most_common_topics:
        print(f"  - {topic}: {count}")

if __name__ == "__main__":
    theme = input("Enter a theme (e.g., 'logic', 'AI', 'Machine Learning'): ")
    conferences = search_conferences_by_theme(theme)
    print_conferences(conferences)
    print_metrics(conferences)
