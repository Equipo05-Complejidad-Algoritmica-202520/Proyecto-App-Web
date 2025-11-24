# scripts/geocoding_google.py
import pandas as pd
from geopy.geocoders import GoogleV3
import time
import os
from dotenv import load_dotenv

# Carga tu API Key de Google Maps
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Carga tu CSV original y prepara salida
input_file = "../backend/data/grifos_original.csv"  # Ajusta el nombre exacto
output_file = "../backend/data/grifos_geocoded.csv"

df = pd.read_csv(input_file, sep=";", nrows=1500)  # Prueba con 500; quita nrows para todo

geolocator = GoogleV3(api_key=GOOGLE_API_KEY)


def geocode_address(row):
    # Construye dirección completa para mejor precisión
    address = f"{row['DIRECCION OPERATIVA']}, {row['DISTRITO']}, {row['PROVINCIA']}, {row['DEPARTAMENTO']}, Perú"
    address = address.replace(";;", ";").strip()  # Limpia duplicados de ;

    try:
        location = geolocator.geocode(address, timeout=10)
        time.sleep(0.1)  # Rate limit: 1 req/segundo (gratis)
        if location:
            print(f"Éxito: {row['RAZON SOCIAL'][:30]}... -> {location.address}")
            return location.latitude, location.longitude
        else:
            print(f"Falló: {row['RAZON SOCIAL'][:30]}...")
            return None, None
    except Exception as e:
        print(f"Error en {row['RAZON SOCIAL'][:30]}: {e}")
        return None, None


# Añade columnas lat/lng
print("Iniciando geocodificación con Google Maps...")
df[['lat', 'lng']] = df.apply(geocode_address, axis=1, result_type='expand')

# Limpia nulos y guarda
df_clean = df.dropna(subset=['lat', 'lng']).reset_index(drop=True)
df_clean.to_csv(output_file, index=False)

print(f"\n¡Listo! {len(df_clean)}/{len(df)} grifos geocodificados exitosamente (~95% esperado).")
print(f"Archivo guardado: {output_file}")
print("Ejemplo de éxito:")
print(df_clean[['RAZON SOCIAL', 'lat', 'lng']].head())