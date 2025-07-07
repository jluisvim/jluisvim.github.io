import requests
import pandas as pd

# Configuración
pais_iso3 = 'US'  # Código ISO3 para Estados Unidos

# Lista de indicadores clave con sus códigos correspondientes
indicadores = {
    "PIB per cápita (USD)": "NY.GDP.PCAP.CD",
    "Esperanza de vida al nacer": "SP.DYN.LE00.IN",
    "Tasa de alfabetización (%)": "SE.ADT.LITR.ZS",
    "Pobreza (% de la población)": "SI.POV.NAHC",
    "Desempleo (%)": "SL.UEM.TOTL.ZS",
    "Emisiones de CO₂ (kg por USD PIB)": "EN.ATM.CO2E.KG",
    "Índice de Gini": "SI.POV.GINI"
}

# Función para obtener dato del Banco Mundial
def get_worldbank_data(country_code, indicator_code):
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator_code}?format=json&date=latest"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ Error al acceder a {indicator_code}: código {response.status_code}")
        return None
    
    data = response.json()
    if len(data) < 2 or not data[1]:
        print(f"⚠️ No hay datos disponibles para {indicator_code}")
        return None

    for item in data[1]:
        if item['value'] is not None:
            return item['value']
    
    print(f"⚠️ No hay valores válidos para {indicator_code}")
    return None

# Extraer datos
resultados = {}
for nombre, codigo in indicadores.items():
    valor = get_worldbank_data(pais_iso3, codigo)
    resultados[nombre] = valor

# Convertir a DataFrame
df = pd.DataFrame([resultados])

# Mostrar resultados
print(df.to_string(index=False))

# Guardar en CSV
# df.to_csv('world_bank_us_key_indicators.csv', index=False, encoding='utf-8-sig')
# print("\n✅ Datos guardados en: world_bank_us_key_indicators.csv")
