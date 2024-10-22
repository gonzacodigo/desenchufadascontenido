from concurrent.futures import ThreadPoolExecutor
import random
from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

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
def obtener_noticias_caras():
    url = "https://caras.perfil.com/ultimo-momento"
    
    # Realizar la solicitud usando requests directamente
    try:
        response = session.get(url)
        response.raise_for_status()  # Lanza excepción si falla
    except requests.RequestException as e:
        app.logger.error(f"Error en la solicitud: {e}")
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

        # Realizar la solicitud del artículo
        try:
            response_articulo = session.get(link_href)
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
        imagen_url = imagen['src'] if imagen else None

        if title:
            resultado.append({
                'title': title.text.strip() if title else None,
                'parrafo': parrafo.text.strip() if parrafo else None,
                'imageUrl': imagen_url,
                'urls_imagenes': urls_imagenes,
                'link_href': link_href,
                'seccion': 'CARAS | ' + (seccion.text.strip() if seccion else 'SIN SECCIÓN'),
                'date': date.text.strip() if date else None,
                'contenido': contenido.text.strip() if contenido else None,
            })

    return jsonify(resultado)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Puerto asignado por Render
    app.run(host='0.0.0.0', port=port)

