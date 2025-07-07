import requests

def fetch_url_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return f"Error en la consulta a {url}: {response.status_code} {response.reason}"
    except requests.exceptions.RequestException as e:
        return f"Error en la consulta a {url}: {str(e)}"

def main():
    urls_list = """
https://pfia2025.u-bourgogne.fr/infos/hebergement/ 
https://easychair.org/cfp/ 
https://www.nonexistentwebsite12345.com 
"""
    urls = [url.strip() for url in urls_list.split('\n') if url.strip()]

    for url in urls:
        result = fetch_url_content(url)
        if "Error" not in result:
            print(f"Consulta a {url} exitosa.")
            print("Contenido de la página:")
            print(result[:500])  # Imprimir solo los primeros 500 caracteres para brevedad
            print("-" * 80)
        else:
            print(result)

if __name__ == "__main__":
    main()
