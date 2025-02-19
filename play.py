import requests
import re
import subprocess
import os
import shutil

url_base = "jkanime.bz"
url_hentai = "hentaijk.com"
url_local = url_base
directorio = "jkanime.bz"

def descargar_pagina_completa(url, output_dir="."):
    try:
        comando = [
            "wget",
            "-e", "robots=off",
            "-p",
            "-k",
            "-nc",
            "--wait=2",
            "--random-wait",
            "--user-agent=Mozilla/5.0",
            "-E",
            "-P", output_dir,
            url,
        ]
        print(f"Descargando {url}...")
        subprocess.run(comando, check=True)
        print("Descarga completada.")
    except subprocess.CalledProcessError as e:
        print(f"Error al descargar: {e}")
        exit()
    except FileNotFoundError:
        print("Instala wget para continuar.")
        exit()

def buscar_urls_video(directorio_base):
    patron = r"video:\s*{[\s\S]*?url:\s*'([^']+)'"
    urls_video = []

    for root, _, files in os.walk(directorio_base):
        for file in files:
            if file.startswith("um.php?"):
                ruta_archivo = os.path.join(root, file)
                try:
                    with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
                        contenido = f.read()
                    coincidencias = re.findall(patron, contenido)
                    if coincidencias:
                        urls_video.extend(coincidencias)
                except Exception as e:
                    print(f"Error leyendo {file}: {str(e)}")

    # Eliminar duplicados manteniendo el orden
    seen = set()
    return [x for x in urls_video if not (x in seen or seen.add(x))]

def eliminar_carpeta(directorio):
    if os.path.exists(directorio):
        shutil.rmtree(directorio)

def reproducir_video(url_video):
    try:
        subprocess.run(["vlc", url_video], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Instala VLC o revisa la URL del video:", url_video)

def main():
    # Configurar reintentos para requests
    session = requests.Session()
    session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))

    # Buscar anime
    busqueda = input("Buscar anime>> ")
    try:
        response = session.get(
            "https://api.jikan.moe/v4/anime",
            params={"q": busqueda, "limit": 10},
            timeout=15
        )
        response.raise_for_status()
        resultados = response.json().get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {str(e)}")
        exit()

    if not resultados:
        print("No se encontraron resultados")
        exit()

    # Mostrar opciones
    print("\nResultados:")
    for i, anime in enumerate(resultados, 1):
        titulo = re.sub(r'[^a-zA-Z0-9 ]', '', anime['title']).strip()
        titulo_formateado = re.sub(r'\s+', '-', titulo).lower()
        genres = [genre['name'].lower() for genre in anime['genres']]
        hentai_warning = "🔞" if 'hentai' in genres else ""
        url_local = url_hentai if 'hentai' in genres else url_base
        print(f"{i}. {titulo} ({anime['type']}) - {anime['episodes'] or '?'} episodios {hentai_warning}")
        print("Géneros:", ", ".join(genres))
        print(f"   Fuente: {url_local}/{titulo_formateado}")
        print("─" * 50)

    # Seleccionar anime
    try:
        seleccion = int(input("\nIngresa el número del anime: ")) - 1
        anime = resultados[seleccion]
    except (ValueError, IndexError):
        print("Selección inválida")
        exit()

    # Determinar URL base
    genres = [genre['name'].lower() for genre in anime['genres']]
    url_local = url_hentai if 'hentai' in genres else url_base

    # Formatear título para URL
    titulo = re.sub(r'[^a-zA-Z0-9 ]', '', anime['title']).strip()
    titulo_url = re.sub(r'\s+', '-', titulo).lower()
# Seleccionar capítulo
    try:
        capitulo = int(input("Número de capítulo: "))
        if capitulo < 1:
            raise ValueError
    except ValueError:
        print("Número inválido")
        exit()

    # Construir URL
    url = f"https://{url_local}/{titulo_url}/{capitulo}/"
    output_dir = "temp_descarga"

    # Descargar y buscar video
    descargar_pagina_completa(url, output_dir)

    # Buscar en TODA la estructura de carpetas
    urls_video = buscar_urls_video(output_dir)

    if urls_video:
        eliminar_carpeta(output_dir)
        print(f"\nEncontradas {len(urls_video)} fuentes de video:")
        for i, url in enumerate(urls_video, 1):
            print(f"Fuente {i}: {url}")

        print("\nReproduciendo con la primera fuente... (Ctrl+C para salir)")
        reproducir_video(urls_video[0])
    else:
        print("No se encontraron videos")
        #eliminar_carpeta(output_dir)

main()
