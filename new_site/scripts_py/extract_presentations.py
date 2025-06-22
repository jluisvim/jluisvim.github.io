import re
import sys
from bs4 import BeautifulSoup

def extract_presentations_from_html(html_file, output_txt):
    """
    Extrae presentaciones del HTML y las guarda en formato TXT estándar
    
    Args:
        html_file (str): Ruta al archivo HTML de presentaciones
        output_txt (str): Ruta donde guardar el archivo TXT resultante
    """
    # Leer el archivo HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Diccionario para mapear iconos a tipos de presentación
    icon_to_type = {
        '&#x1F5FA': 'International Conference',
        '&#x1F5FC': 'National Conference',
        '&#x1F5E3': 'Seminar'
    }
    
    presentations = []
    
    # Extraer todas las secciones por año
    for tabcontent in soup.find_all('div', class_='tabcontent'):
        year = tabcontent.get('id', 'Unknown')
        
        # Extraer cada presentación en esta sección de año
        for row in tabcontent.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) < 3:  # Cambiado a < 3 para mayor seguridad
                continue  # Saltar filas que no tienen 3 columnas
            
            try:
                # Extraer información de la primera columna (fecha/icono)
                date_icon = cols[0].get_text(strip=True, separator='\n').split('\n')
                month = date_icon[0].strip() if len(date_icon) > 0 else ''
                icon = date_icon[1].strip('() ') if len(date_icon) > 1 else ''
                
                # Extraer información de la segunda columna (evento/título)
                event = cols[1].find('b').get_text(strip=True) if cols[1].find('b') else ''
                title = cols[1].find('i').get_text(strip=True).strip("''") if cols[1].find('i') else ''
                
                # Extraer información de la tercera columna (ubicación)
                location = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                
                # Determinar tipo de presentación
                pres_type = icon_to_type.get(icon, 'Other')
                
                # Extraer autores si existen
                authors_div = cols[1].find('div', class_='presentation-authors')
                authors = authors_div.get_text(strip=True) if authors_div else 'José-Luis Vilchis-Medina'
                
                # Crear entrada en formato estándar
                presentation = f"""Año: {year}
Tipo: {pres_type}
Mes: {month}
Evento: {event}
Título: {title}
Lugar: {location}
Autores: {authors}
---
"""
                presentations.append(presentation)
            
            except Exception as e:
                print(f"Advertencia: Error al procesar una fila - {str(e)}")
                continue
    
    # Escribir todas las presentaciones al archivo TXT
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(presentations))
    
    print(f"Se extrajeron {len(presentations)} presentaciones y se guardaron en {output_txt}")

def main():
    # Verificar que se proporcionaron los argumentos correctos
    if len(sys.argv) != 2:
        print("Uso: python3 archivo.py ruta_archivo_html")
        print("Ejemplo: python3 archivo.py presentations.html")
        sys.exit(1)
    
    html_file = sys.argv[1]
    output_txt = html_file.replace('.html', '_extracted.txt')
    
    try:
        extract_presentations_from_html(html_file, output_txt)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {html_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
