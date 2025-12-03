import requests
import pandas as pd
import time
from pathlib import Path

# Definición de bounding boxes para cada departamento costero
DEPARTAMENTOS_COSTA = {
    'TUMBES': {
        'bbox': "-4.25, -81.10, -3.40, -80.00",
        'nombre': "Tumbes"
    },
    'PIURA': {
        'bbox': "-6.40, -81.30, -4.05, -79.20",
        'nombre': "Piura"
    },
    'LAMBAYEQUE': {
        'bbox': "-7.25, -80.70, -5.90, -78.90",
        'nombre': "Lambayeque"
    },
    'LA LIBERTAD': {
        'bbox': "-8.90, -79.90, -6.80, -77.80",
        'nombre': "La Libertad"
    },
    'ANCASH': {
        'bbox': "-10.80, -78.70, -8.10, -76.90",
        'nombre': "Ancash"
    },
    'LIMA': {
        'bbox': "-13.20, -77.70, -10.80, -75.80",
        'nombre': "Lima"
    },
    'CALLAO': {
        'bbox': "-12.15, -77.25, -11.75, -76.95",
        'nombre': "Callao"
    },
    'ICA': {
        'bbox': "-15.40, -76.60, -13.00, -74.80",
        'nombre': "Ica"
    },
    'AREQUIPA': {
        'bbox': "-17.20, -73.80, -15.10, -71.00",
        'nombre': "Arequipa"
    },
    'MOQUEGUA': {
        'bbox': "-17.90, -71.50, -16.60, -70.20",
        'nombre': "Moquegua"
    },
    'TACNA': {
        'bbox': "-18.40, -71.10, -17.25, -69.70",
        'nombre': "Tacna"
    }
}


def obtener_estaciones_departamento(departamento, bbox, reintentos=3):
    """
    Obtiene estaciones de servicio y GNV REALES de un departamento específico
    Con manejo de errores y reintentos
    """
    overpass_url = "http://overpass-api.de/api/interpreter"

    overpass_query = f"""
    [out:json][timeout:120];
    (
      node["amenity"="fuel"]({bbox});
      way["amenity"="fuel"]({bbox});
      relation["amenity"="fuel"]({bbox});
      node["fuel:cng"="yes"]({bbox});
      way["fuel:cng"="yes"]({bbox});
    );
    out center;
    """

    for intento in range(reintentos):
        if intento > 0:
            pausa = 15 * intento  # Pausa incremental: 15, 30, 45 segundos
            print(f"      ⏳ Reintentando en {pausa}s...", end=" ")
            time.sleep(pausa)

        print(f"   🔍 Consultando {departamento}... (intento {intento + 1}/{reintentos})", end=" ")

        try:
            response = requests.post(
                overpass_url,
                data={'data': overpass_query},
                timeout=150
            )
            response.raise_for_status()
            data = response.json()

            estaciones = []
            elementos = data.get('elements', [])

            for elemento in elementos:
                # Obtener coordenadas
                if elemento['type'] == 'node':
                    lat = elemento.get('lat')
                    lon = elemento.get('lon')
                elif 'center' in elemento:
                    lat = elemento['center'].get('lat')
                    lon = elemento['center'].get('lon')
                else:
                    continue

                tags = elemento.get('tags', {})

                # Determinar tipo de estación
                es_gnv = tags.get('fuel:cng') == 'yes'

                # Construir razón social
                nombre = tags.get('name', 'Sin nombre')
                marca = tags.get('brand', '')
                operador = tags.get('operator', '')

                if es_gnv and not marca:
                    marca = 'GNV'

                if marca and marca != '':
                    razon_social = f"{marca} - {nombre}" if nombre != 'Sin nombre' else marca
                elif operador:
                    razon_social = operador
                else:
                    razon_social = nombre

                # Agregar indicador GNV si aplica
                if es_gnv and 'GNV' not in razon_social.upper():
                    razon_social = f"{razon_social} (GNV)"

                # Construir dirección operativa
                calle = tags.get('addr:street', '')
                numero = tags.get('addr:housenumber', '')
                ciudad = tags.get('addr:city', '')

                if calle and numero:
                    direccion_operativa = f"{calle} {numero}"
                elif calle:
                    direccion_operativa = calle
                elif ciudad:
                    direccion_operativa = f"Zona {ciudad}"
                else:
                    direccion_operativa = "Sin dirección"

                # Obtener distrito
                distrito = tags.get('addr:district',
                                    tags.get('addr:suburb',
                                             tags.get('addr:city', 'Sin distrito')))

                estacion = {
                    'RAZON SOCIAL': razon_social,
                    'DIRECCION OPERATIVA': direccion_operativa,
                    'DISTRITO': distrito,
                    'DEPARTAMENTO': departamento,
                    'lat': round(lat, 6),
                    'lng': round(lon, 6),
                }

                estaciones.append(estacion)

            print(f"✅ {len(estaciones)} estaciones")

            # Pausa entre consultas exitosas
            time.sleep(5)

            return estaciones

        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout")
            if intento < reintentos - 1:
                continue
            else:
                print(f"      ❌ {departamento}: No se pudo obtener datos después "
                      f"de {reintentos} intentos (Timeout)")
                return []

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                print(f"🚫 Límite de consultas alcanzado")
                if intento < reintentos - 1:
                    continue
                else:
                    print(f"      ❌ {departamento}: Límite de consultas alcanzado")
                    return []
            elif e.response.status_code == 504:  # Gateway Timeout
                print(f"⏱️ Gateway Timeout")
                if intento < reintentos - 1:
                    continue
                else:
                    print(f"      ❌ {departamento}: Gateway Timeout persistente")
                    return []
            else:
                print(f"❌ Error HTTP {e.response.status_code}")
                return []

        except Exception as e:
            print(f"❌ Error: {e}")
            if intento < reintentos - 1:
                continue
            else:
                return []

    return []


def main():
    print("=" * 70)
    print("🚗 EXTRACTOR DE GRIFOS REALES - COSTA PERUANA")
    print("   (Consulta departamento por departamento)")
    print("=" * 70)
    print()

    inicio = time.time()

    todas_estaciones = []
    resumen_departamentos = {}

    print("📍 Extrayendo grifos por departamento:\n")
    print("⚠️  Este proceso puede tardar varios minutos debido a las pausas entre consultas\n")

    # Consultar cada departamento costero
    for depto, info in DEPARTAMENTOS_COSTA.items():
        estaciones = obtener_estaciones_departamento(depto, info['bbox'])
        todas_estaciones.extend(estaciones)
        resumen_departamentos[depto] = len(estaciones)

    if not todas_estaciones:
        print("\n❌ No se pudieron obtener datos de ningún departamento")
        return

    print(f"\n📊 Total de estaciones extraídas: {len(todas_estaciones)}")

    # Crear DataFrame
    df = pd.DataFrame(todas_estaciones)

    # Eliminar duplicados basados en coordenadas muy cercanas
    print(f"\n🔄 Eliminando duplicados...")
    df['lat_round'] = df['lat'].round(4)  # ~11 metros de precisión
    df['lng_round'] = df['lng'].round(4)

    antes = len(df)
    df = df.drop_duplicates(subset=['lat_round', 'lng_round'], keep='first')
    df = df.drop(columns=['lat_round', 'lng_round'])

    duplicados_removidos = antes - len(df)
    print(f"   Duplicados removidos: {duplicados_removidos}")
    print(f"✅ Estaciones únicas: {len(df)}")

    # Guardar CSV
    output_dir = Path("../backend/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "grifos_costa_peruana.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    fin = time.time()
    tiempo_total = fin - inicio

    print("\n" + "=" * 70)
    print(f"✅ Archivo guardado: {output_file}")
    print(f"📁 Total de registros REALES: {len(df)}")
    print(f"⏱️  Tiempo de ejecución: {tiempo_total:.2f} segundos")
    print("=" * 70)

    # Estadísticas
    print("\n📈 Estadísticas generales:")
    print(f"   - Con razón social: {df['RAZON SOCIAL'].ne('Sin nombre').sum()}")
    print(f"   - Con dirección: {df['DIRECCION OPERATIVA'].ne('Sin dirección').sum()}")
    print(f"   - Con distrito identificado: {df['DISTRITO'].ne('Sin distrito').sum()}")

    # Rango de coordenadas
    print("\n🗺️  Rango geográfico:")
    print(f"   - Latitud: {df['lat'].min():.4f} a {df['lat'].max():.4f}")
    print(f"   - Longitud: {df['lng'].min():.4f} a {df['lng'].max():.4f}")

    # Distribución por departamento
    print("\n🏖️  Distribución por departamento costero:")
    departamentos = df['DEPARTAMENTO'].value_counts()
    deptos_sin_datos = []
    for depto in DEPARTAMENTOS_COSTA.keys():
        count = departamentos.get(depto, 0)
        if count > 0:
            print(f"   - {depto}: {count}")
        else:
            deptos_sin_datos.append(depto)

    if deptos_sin_datos:
        print(f"\n⚠️  Departamentos sin datos obtenidos: {', '.join(deptos_sin_datos)}")
        print("   (Puede deberse a timeouts o límites de la API de Overpass)")

    # Principales distritos
    print("\n📍 Principales distritos (Top 20):")
    distritos = df[df['DISTRITO'] != 'Sin distrito']['DISTRITO'].value_counts().head(20)
    for distrito, count in distritos.items():
        print(f"   - {distrito}: {count}")

    # Top marcas
    print("\n🏢 Principales marcas:")
    # Extraer marca de la razón social
    df_temp = df[df['RAZON SOCIAL'] != 'Sin nombre'].copy()
    df_temp['marca_simple'] = df_temp['RAZON SOCIAL'].str.split(' - ').str[0].str.split('(').str[0].str.strip()
    marcas = df_temp['marca_simple'].value_counts().head(10)
    for marca, count in marcas.items():
        print(f"   - {marca}: {count}")

    print("\n✨ ¡Proceso completado exitosamente!")
    print(f"💡 Total de grifos REALES en la costa peruana: {len(df)}")


if __name__ == "__main__":
    main()