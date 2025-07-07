import requests
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime

def fetch_future_conferences(keyword):
    url = f" https://easychair.org/cfp/search.cgi?query={keyword}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar la sección de conferencias futuras
            future_section = soup.find('h3', string='CFPs for Future Events')
            if future_section:
                table = future_section.find_next('table', {'class': 'ct_table'})
                if table:
                    rows = table.find_all('tr')[1:]  # Saltar la fila de encabezados
                    results = []
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 6:
                            acronym = cols[0].get_text(strip=True)
                            name = cols[1].get_text(strip=True)
                            location = cols[2].get_text(strip=True)
                            submission_deadline = cols[3].get_text(strip=True)
                            start_date = cols[4].get_text(strip=True)
                            topics = cols[5].get_text(strip=True)
                            # Obtener el enlace de la conferencia
                            link_tag = cols[0].find('a')
                            link = link_tag['href'] if link_tag else None
                            full_link = f"https://easychair.org{link}" if link else None
                            results.append({
                                'acronym': acronym,
                                'name': name,
                                'location': location,
                                'submission_deadline': submission_deadline,
                                'start_date': start_date,
                                'topics': topics,
                                'link': full_link
                            })
                    return results
                else:
                    return "No se encontraron conferencias futuras."
            else:
                return "No se encontró la sección de conferencias futuras."
        else:
            return f"Error en la consulta a {url}: {response.status_code} {response.reason}"
    except requests.exceptions.RequestException as e:
        return f"Error en la consulta a {url}: {str(e)}"

def save_to_csv(results, filename):
    if not results:
        print(f"No hay resultados para guardar en el archivo {filename}.")
        return
    
    keys = results[0].keys()
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    print(f"Resultados guardados en {filename}")

def create_output_folder():
    timestamp = datetime.now().strftime("%Y%m%d")
    folder_name = f"conferences_{timestamp}"
    os.makedirs(folder_name, exist_ok=True)
    print(f"Carpeta creada: {folder_name}")
    return folder_name

def main():
    keywords = input("Ingrese las palabras clave para la búsqueda (separadas por comas): ").split(',')
    keywords = [keyword.strip() for keyword in keywords]
    
    output_folder = create_output_folder()
    
    for keyword in keywords:
        print(f"Buscando conferencias para la palabra clave: {keyword}")
        results = fetch_future_conferences(keyword)
        
        if isinstance(results, list):
            print(f"Resultados para la búsqueda '{keyword}':")
            for result in results:
                print(f"Acronimo: {result['acronym']}")
                print(f"Nombre: {result['name']}")
                print(f"Lugar: {result['location']}")
                print(f"Fecha de Entrega: {result['submission_deadline']}")
                print(f"Fecha de Inicio: {result['start_date']}")
                print(f"Temas: {result['topics']}")
                print(f"Enlace: {result['link']}")
                print("-" * 80)
            
            # Guardar los resultados en un archivo CSV
            filename = os.path.join(output_folder, f"conferences_{keyword.replace(' ', '_')}.csv")
            save_to_csv(results, filename)
        else:
            print(results)

if __name__ == "__main__":
    main()
