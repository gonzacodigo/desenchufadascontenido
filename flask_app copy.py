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


@app.route('/api/noticias/telefe', methods=['GET'])
def obtener_noticias_infobae():
    url = "https://noticias.mitelefe.com/espectaculos"
    
    # Realizar la solicitud usando requests directamente
    try:
        response = session.get(url)
        response.raise_for_status()  # Lanza excepción si falla
    except requests.RequestException as e:
        app.logger.error(f"Error en la solicitud: {e}")
        return jsonify({'error': 'No se pudo obtener las noticias'}), 500

    soup = BeautifulSoup(response.text, 'html.parser')
    noticias = soup.find_all('a', class_='e-card-link')
    
    resultado = []

    for noticia in noticias:
        title = noticia.find('h2', class_="e-card-title")
        link_href = noticia['href'] if noticia and 'href' in noticia.attrs else None
        # Buscar el div de la imagen dentro de la noticia actual
        div_imagen = noticia.find('div', class_="e-card-img-container")
        imagen_url = None
        
        if div_imagen:
            # Buscar la etiqueta img dentro del div
            imagen = div_imagen.find('img', class_="e-card-img")
            
            if imagen:
                # Obtener el 'src' o intentar extraer desde 'data-interchange'
                imagen_url = imagen['src'] if 'src' in imagen.attrs else None
                
                if not imagen_url and 'data-interchange' in imagen.attrs:
                    # Extraer la URL del 'data-interchange'
                    data_interchange = imagen['data-interchange']
                    imagen_url = data_interchange.split(',')[0].strip().split('[')[1]
        
        if link_href and not link_href.startswith('http'):
            link_href = urljoin("https://noticias.mitelefe.com/espectaculos", link_href)
            
        # Sección de llamado al artículo
        # Realizar la solicitud del artículo
        try:
            response_articulo = session.get(link_href)
            response_articulo.raise_for_status()
        except requests.RequestException as e:
            app.logger.error(f"Error en la solicitud al artículo: {e}")
            continue

        soup_article = BeautifulSoup(response_articulo.text, 'html.parser')
        noticias_article = soup_article.find_all('article', class_='b-post')
        
        # Reiniciar la lista de URLs de imágenes para cada noticia
        urls_imagenes = []

        if noticias_article:
            date = noticias_article[0].find('span', class_="e-post-time")
            seccion = "TELEFE | ESPECTACULOS"
            parrafo = noticias_article[0].find('div', class_='e-post-subtitle')
            parrafos = noticias_article[0].find_all('div', class_="e-post-text")
            contenido = [parrafo.get_text().strip() for parrafo in parrafos]
            
            # Obtener imágenes desde el artículo
            urls_imagenes = [img['src'] for img in soup_article.find_all('img') if 'src' in img.attrs]
        else:
            date, seccion, contenido, urls_imagenes = None, None, [], []

        # Sección de agregados
        if title:
            resultado.append({
                'title': title.text.strip() if title else None,
                'parrafo': parrafo.text.strip() if parrafo else None,
                'imageUrl': imagen_url,
                'urls_imagenes': urls_imagenes,
                'link_href': link_href,
                'seccion': seccion,
                'date': date.text.strip() if date else None,
                'contenido': " ".join(contenido),
            })

    return jsonify(resultado)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Puerto asignado por Render
    app.run(host='0.0.0.0', port=port)

