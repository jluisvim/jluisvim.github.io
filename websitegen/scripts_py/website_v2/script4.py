import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import json
from pprint import pprint

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_pais.log'),
        logging.StreamHandler()
    ]
)

def obtener_datos_panel(pais, debug=False):
    """
    Función para obtener información específica del panel react-tabs-1
    
    Args:
        pais (str): Nombre del país en inglés (ej. 'united-states', 'mexico', 'spain')
        debug (bool): Si True, muestra información detallada del proceso
    
    Returns:
        dict/DataFrame: Datos estructurados del panel
    """
    # Construir la URL
    url = f"https://data.worldbank.org/country/{pais}"
    logging.info(f"Iniciando consulta para el país: {pais}")
    if debug:
        logging.debug(f"URL construida: {url}")

    try:
        # Obtener el contenido HTML de la página
        logging.info("Realizando solicitud HTTP...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        if debug:
            logging.debug(f"Status code: {response.status_code}")
            logging.debug(f"Tamaño de la respuesta: {len(response.text)} bytes")
            with open('debug_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)

        # Parsear el HTML
        logging.info("Parseando el HTML...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar específicamente el panel react-tabs-1
        logging.info("Buscando el panel react-tabs-1...")
        panel = soup.find(id='react-tabs-1')
        
        if not panel:
            logging.warning("No se encontró el panel react-tabs-1")
            if debug:
                logging.debug("Buscando todos los elementos con ID que contengan 'react-tabs'")
                tabs = soup.find_all(id=lambda x: x and 'react-tabs' in x)
                logging.debug(f"Se encontraron {len(tabs)} paneles react-tabs")
                for tab in tabs:
                    logging.debug(f"ID encontrado: {tab.get('id')}")
            return None

        if debug:
            logging.debug(f"Contenido del panel react-tabs-1:\n{str(panel)[:1000]}...")

        # Extraer datos del panel (adaptar según estructura específica)
        datos = {}
        
        # Ejemplo: Extraer secciones del panel
        secciones = panel.find_all('div', class_='section')
        logging.info(f"Se encontraron {len(secciones)} secciones en el panel")
        
        for seccion in secciones:
            titulo = seccion.find('h3')
            if titulo:
                titulo_text = titulo.get_text(strip=True)
                contenido = []
                
                # Extraer elementos de contenido (ajustar según necesidad)
                items = seccion.find_all('li') or seccion.find_all('p')
                for item in items:
                    contenido.append(item.get_text(strip=True))
                
                datos[titulo_text] = contenido if contenido else seccion.get_text(strip=True, separator='\n')
                
                if debug:
                    logging.debug(f"Sección '{titulo_text}': {len(contenido)} elementos")
        
        # Si no se encontraron secciones, extraer todo el texto
        if not datos:
            logging.info("Extrayendo todo el contenido del panel")
            datos['contenido_completo'] = panel.get_text(strip=True, separator='\n')
        
        # Convertir a DataFrame si la estructura lo permite
        try:
            if datos and len(datos) > 1:
                df = pd.DataFrame.from_dict({k: pd.Series(v) for k, v in datos.items()})
                if debug:
                    logging.debug("DataFrame creado a partir de los datos:")
                    logging.debug(f"\n{df.head()}")
                return df
            return datos
        except Exception as e:
            logging.warning(f"No se pudo convertir a DataFrame: {e}")
            return datos
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Error en la solicitud HTTP: {e}")
        if debug:
            logging.exception("Traceback completo:")
        return None
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        if debug:
            logging.exception("Traceback completo:")
        return None

# Ejemplo de uso con debug
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Consultar datos de países desde World Bank')
    parser.add_argument('pais', help='Nombre del país en formato URL (ej. united-states)')
    parser.add_argument('--debug', action='store_true', help='Activar modo debug')
    parser.add_argument('--json', action='store_true', help='Mostrar salida en formato JSON')
    args = parser.parse_args()
    
    print(f"\n{' CONSULTA ESPECÍFICA (react-tabs-1) ':=^60}\n")
    
    datos = obtener_datos_panel(args.pais, debug=args.debug)
    
    if datos is not None:
        print("\nResultados obtenidos del panel react-tabs-1:")
        
        if args.json:
            print(json.dumps(datos, indent=2, ensure_ascii=False))
        elif isinstance(datos, pd.DataFrame):
            print(datos)
        else:
            pprint(datos)
        
        # Opcional: Guardar en archivo
        guardar = input("\n¿Desea guardar los datos? (s/n): ")
        if guardar.lower() == 's':
            nombre_archivo = f"datos_panel_{args.pais}.{'json' if args.json or not isinstance(datos, pd.DataFrame) else 'csv'}"
            if isinstance(datos, pd.DataFrame):
                datos.to_csv(nombre_archivo, index=False)
            else:
                with open(nombre_archivo, 'w', encoding='utf-8') as f:
                    json.dump(datos, f, indent=2, ensure_ascii=False)
            print(f"Datos guardados en {nombre_archivo}")
    else:
        print("\nNo se pudieron obtener los datos del panel. Revise el log para más detalles.")
    
    print("\n" + "="*60)
    if args.debug:
        print("\nDebug: Puede revisar los archivos 'debug_response.html' y 'debug_pais.log'")
