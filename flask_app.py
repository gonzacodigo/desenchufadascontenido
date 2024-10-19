import os
from concurrent.futures import ThreadPoolExecutor
import random
from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Tu clave de ScraperAPI
api_keys = ['8bfe37b334e6b7034eab0ec0529550f9', '56987acc583925f1f15194da140305f5',
            'f583187a3d581888a8932050f35f87ad', '3c3aab584b0f0a3ad5599b46459469f2']

app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas
session = requests.Session()  # Reutilizar la sesión HTTP

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/noticias', methods=['GET'])
def obtener_noticias():
    url = "https://www.ciudad.com.ar/espectaculos/"
    random.shuffle(api_keys)  # Mezclar las claves API para intentar una diferente cada vez

    # Intentar obtener la respuesta usando cualquiera de las API keys
    response, api_key_valido = obtener_respuesta_api(url, api_keys)

    if not response:
        return jsonify({'error': 'No se pudo obtener las noticias'}), 500

    app.logger.info(f"API válida encontrada: {api_key_valido}")

    # Procesar el contenido de la respuesta para extraer noticias
    soup = BeautifulSoup(response.text, 'html.parser')
    noticias = soup.find_all('article', class_='card__container card__horizontal')[:15]

    resultado = []

    # Realizar las solicitudes en paralelo para obtener detalles de los artículos
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_article = {executor.submit(fetch_article, api_key_valido, noticia): noticia for noticia in noticias}
        for future in future_to_article:
            articulo_data = future.result()
            if articulo_data:
                resultado.append(articulo_data)

    return jsonify(resultado)

def obtener_respuesta_api(url, api_keys):
    """
    Intenta realizar una solicitud a una URL usando múltiples claves API.
    """
    for key in api_keys:
        scraperapi_url = f'http://api.scraperapi.com?api_key={key}&url={url}'
        try:
            response = session.get(scraperapi_url)
            response.raise_for_status()
            return response, key
        except requests.RequestException as e:
            app.logger.error(f"Error en la solicitud con api_key {key}: {e}")
    return None, None

def fetch_article(api_key_valido, noticia):
    title = noticia.find('h2', class_='card__headline')
    parrafo = noticia.find('p', class_='card__subheadline')
    picture = noticia.find('picture', class_='responsive-image')
    link = noticia.find('a')
    link_href = link['href'] if link else None
    imagen = picture.find('img') if picture else None
    imagen_url = imagen['src'] if imagen else None

    if imagen_url and not imagen_url.startswith('http'):
        imagen_url = urljoin("https://www.ciudad.com.ar", imagen_url)

    # Extraer detalles del artículo
    url_articulo = link_href
    scraperapi_url_articulo = f'http://api.scraperapi.com?api_key={api_key_valido}&url=https://www.ciudad.com.ar{url_articulo}'

    try:
        response_articulo = session.get(scraperapi_url_articulo)
        response_articulo.raise_for_status()
    except requests.RequestException as e:
        app.logger.error(f"Error en la solicitud al artículo: {e}")
        return None

    soup_article = BeautifulSoup(response_articulo.text, 'html.parser')
    noticias_article = soup_article.find_all('div', class_='fusion-app')

    if noticias_article:
        date = noticias_article[0].find('span', class_="time__value")
        seccion_div = noticias_article[0].find('div', class_="breadcrumb")
        seccion = seccion_div.find('a') if seccion_div else None

        parrafos = noticias_article[0].find_all('p', class_="paragraph")
        contenido = [parrafo.get_text().strip() for parrafo in parrafos]
        imagenes = noticias_article[0].find_all('img')
        urls_imagenes = [img['src'] for img in imagenes if 'src' in img.attrs]
    else:
        date, seccion, contenido, urls_imagenes = None, None, [], []

    if title and imagen_url:
        return {
            'title': title.text.strip(),
            'parrafo': parrafo.text.strip() if parrafo else None,
            'imageUrl': imagen_url,
            'urls_imagenes': urls_imagenes,
            'link_href': urljoin("https://www.ciudad.com.ar", link_href) if link_href else None,
            'seccion': (seccion.text.strip() + ' | ESPECTACULOS') if seccion else 'ESPECTACULOS',
            'date': date.text.strip() if date else None,
            'contenido': " ".join(contenido)
        }
    return None

@app.route('/api/noticias/caras', methods=['GET'])
def obtener_noticias_caras():
    url = "https://caras.perfil.com/ultimo-momento"
    random.shuffle(api_keys)  # Mezclar las claves API para intentar una diferente cada vez

    # Intentar obtener la respuesta usando cualquiera de las API keys
    response, api_key_valido = obtener_respuesta_api(url, api_keys)

    if not response:
        return jsonify({'error': 'No se pudo obtener las noticias'}), 500

    soup = BeautifulSoup(response.text, 'html.parser')
    todas_las_noticias = (
        soup.find_all('article', class_='articulo nota-1') +
        soup.find_all('article', class_='articulo nota-2') +
        soup.find_all('article', class_='articulo nota-3') +
        soup.find_all('article', class_='articulo nota-4') +
        soup.find_all('article', class_='articulo nota-6') +
        soup.find_all('article', class_='articulo nota-7') +
        soup.find_all('article', class_='articulo nota-8') +
        soup.find_all('article', class_='articulo nota-9') +
        soup.find_all('article', class_='articulo nota-10')
    )

    resultado = []
    for noticia in todas_las_noticias:
        title = noticia.find('h2')
        parrafo = noticia.find('p', class_='headline')
        link = noticia.find('a')
        link_href = link['href'] if link else None
        
        if link_href and not link_href.startswith('http'):
            link_href = urljoin("https://caras.perfil.com", link_href)

        # Extraer detalles del artículo
        url_articulo = link_href
        scraperapi_url_articulo = f'http://api.scraperapi.com?api_key={api_key_valido}&url={url_articulo}'

        try:
            response_articulo = session.get(scraperapi_url_articulo)
            response_articulo.raise_for_status()
        except requests.RequestException as e:
            app.logger.error(f"Error en la solicitud al artículo: {e}")
            continue

        soup_article = BeautifulSoup(response_articulo.text, 'html.parser')
        noticias_article = soup_article.find_all('main', class_='main-container max-width margin-auto container-white considebar')

        if noticias_article:
            date = noticias_article[0].find('span', class_="hat__fecha")
            seccion = noticias_article[0].find('a')
            contenido = noticias_article[0].find("div", class_="news-content")
            urls_imagenes = [img['src'] for img in contenido.find_all('img') if 'src' in img.attrs]
        else:
            date, seccion, urls_imagenes = None, None, []

        picture = noticia.find('picture', class_='cls-optimized') or noticia.find('img')
        imagen = picture.find('img') if picture else None
        imagen_url = imagen['data-src'] if imagen and 'data-src' in imagen.attrs else None

        if title and imagen_url:
            resultado.append({
                'title': title.text.strip(),
                'parrafo': parrafo.text.strip() if parrafo else None,
                'imageUrl': imagen_url,
                'urls_imagenes': urls_imagenes,
                'link_href': link_href,
                'seccion': (seccion.text.strip() + ' | ESPECTACULOS') if seccion else 'ESPECTACULOS',
                'date': date.text.strip() if date else None,
            })

    return jsonify(resultado)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Puerto asignado por Render
    app.run(host='0.0.0.0', port=port)
