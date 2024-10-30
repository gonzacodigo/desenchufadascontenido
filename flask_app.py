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


@app.route('/api/noticias/caras', methods=['GET'])
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
        noticias_article = soup_article.find_all(
            'main', class_='main-container max-width margin-auto container-white considebar')

        if noticias_article:
            date = noticias_article[0].find('span', class_="hat__fecha")
            seccion = noticias_article[0].find('a')

            contenido = noticias_article[0].find("div", class_="news-content")
            urls_imagenes = [img['src']
                             for img in contenido.find_all('img') if 'src' in img.attrs]
            # Si no hay imágenes, mostrar un mensaje
            if not urls_imagenes:
                urls_imagenes = [imagen_url]
                
        else:
            date, seccion, urls_imagenes = None, None, []

        picture = noticia.find(
            'picture', class_='cls-optimized') or noticia.find('img')
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


@app.route('/api/noticias/infobae', methods=['GET'])
def obtener_noticias_infobae():
    url = "https://www.infobae.com/teleshow/"

    # Realizar la solicitud usando requests directamente
    try:
        response = session.get(url)
        response.raise_for_status()  # Lanza excepción si falla
    except requests.RequestException as e:
        app.logger.error(f"Error en la solicitud: {e}")
        return jsonify({'error': 'No se pudo obtener las noticias'}), 500

    soup = BeautifulSoup(response.text, 'html.parser')
    noticias = soup.find_all('a', class_='story-card-ctn')

    resultado = []

    for noticia in noticias:
        title = noticia.find('h2', class_="story-card-hl")
        parrafo = noticia.find('div', class_='deck')
        imagen = noticia.find('img', class_="global-image")
        imagen_url = imagen['src'] if imagen and 'src' in imagen.attrs else None
        link_href = noticia['href'] if noticia and 'href' in noticia.attrs else None

        if link_href and not link_href.startswith('http'):
            link_href = urljoin("https://www.infobae.com", link_href)

        # Sección de llamado al artículo
        # Realizar la solicitud del artículo
        try:
            response_articulo = session.get(link_href)
            response_articulo.raise_for_status()
        except requests.RequestException as e:
            app.logger.error(f"Error en la solicitud al artículo: {e}")
            continue

        soup_article = BeautifulSoup(response_articulo.text, 'html.parser')
        noticias_article = soup_article.find_all('article', class_='article')

        # Reiniciar la lista de URLs de imágenes para cada noticia
        urls_imagenes = []
        noticias_article_img = soup_article.find_all('div', class_='visual__image')
        
        if noticias_article_img:
            # Iterar sobre cada div con la clase 'visual__image'
            for article in noticias_article_img:
                # Buscar todas las imágenes dentro de cada div
                imgs = article.find_all('img', class_="global-image")
                
                # Añadir las URLs de las imágenes a la lista si tienen el atributo 'src'
                urls_imagenes.extend([img['src'] for img in imgs if 'src' in img.attrs])
                # Si no hay imágenes, mostrar un mensaje
                if not urls_imagenes:
                    urls_imagenes = [imagen_url]
                
                
                

            if noticias_article:
                # Procesar el primer artículo (o iterar sobre todos si hay más de uno)
                for article in noticias_article:
                    date = article.find(
                        'span', class_="sharebar-article-date")
                    seccion = "INFOBAE | ESPECTACULOS"
                    parrafos = article.find_all('p', class_="paragraph")
                    contenido = [parrafo.get_text().strip() for parrafo in parrafos]


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


@app.route('/api/noticias/telefe', methods=['GET'])
def obtener_noticias_telefe():
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
                    imagen_url = data_interchange.split(',')[
                        0].strip().split('[')[1]

        if link_href and not link_href.startswith('http'):
            link_href = urljoin(
                "https://noticias.mitelefe.com/espectaculos", link_href)

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
            # Procesar el primer artículo (o iterar sobre todos si hay más de uno)
            for article in noticias_article:
                date = article.find('span', class_="e-post-time")
                seccion = "TELEFE | ESPECTACULOS"
                parrafo = article.find('div', class_='e-post-subtitle')
                parrafos = article.find_all('div', class_="e-post-text")
                contenido = [parrafo.get_text().strip() for parrafo in parrafos]

                            # Obtener imágenes desde el artículo
            urls_imagenes = [img['src'] for img in article.find_all('img') if 'src' in img.attrs]

            # Si no hay imágenes, mostrar un mensaje
            if not urls_imagenes:
                urls_imagenes = [imagen_url]

                # Aquí puedes agregar la lógica para manejar la noticia actual
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

@app.route('/api/noticias/tn', methods=['GET'])
def obtener_noticias_tn():
    url = "https://tn.com.ar/show"
    
    # Realizar la solicitud usando requests directamente
    try:
        response = session.get(url)
        response.raise_for_status()  # Lanza excepción si falla
    except requests.RequestException as e:
        app.logger.error(f"Error en la solicitud: {e}")
        return jsonify({'error': 'No se pudo obtener las noticias'}), 500

    soup = BeautifulSoup(response.text, 'html.parser')
    noticias = soup.find_all('article', class_='card__container')
    
    resultado = []

    for noticia in noticias:
        title = noticia.find('h2', class_="card__headline")
        link = noticia.find('a')
        link_href = link['href'] if link and 'href' in link.attrs else None
        # Buscar el div de la imagen dentro de la noticia actual
        div_imagen = noticia.find('picture', class_="responsive-image")
        imagen_url = None
        
        if div_imagen:
            # Buscar la etiqueta img dentro del div
            imagen = div_imagen.find('img', class_="image image_placeholder")
            
            if imagen:
                # Obtener el 'src' o intentar extraer desde 'data-interchange'
                imagen_url = imagen['src'] if 'src' in imagen.attrs else None
                
                if not imagen_url and 'data-interchange' in imagen.attrs:
                    # Extraer la URL del 'data-interchange'
                    data_interchange = imagen['data-interchange']
                    imagen_url = data_interchange.split(',')[0].strip().split('[')[1]
                    
        if link_href and not link_href.startswith('http'):
            link_href = urljoin("https://tn.com.ar/show/", link_href)
            
        # Sección de llamado al artículo
        # Realizar la solicitud del artículo
        try:
            response_articulo = session.get(link_href)
            response_articulo.raise_for_status()
        except requests.RequestException as e:
            app.logger.error(f"Error en la solicitud al artículo: {e}")
            continue

        soup_article = BeautifulSoup(response_articulo.text, 'html.parser')
        noticias_article = soup_article.find_all('div', class_='col-content')
        
        # Reiniciar la lista de URLs de imágenes para cada noticia
        urls_imagenes = []

        if noticias_article:
            # Procesar el primer artículo (o iterar sobre todos si hay más de uno)
            for article in noticias_article:
                date = article.find('span', class_="time__value font__subtitle-regular")
                seccion = "TN | ESPECTACULOS"
                parrafo = article.find('h2', class_='article__dropline font__body')
                parrafos = article.find_all('p', class_="paragraph")
                contenido = [parrafo.get_text().strip() for parrafo in parrafos]
            
            # Obtener imágenes desde el artículo
            urls_imagenes = [img['src'] for img in article.find_all('img') if 'src' in img.attrs]
            
           # Si no hay imágenes, mostrar un mensaje
            if not urls_imagenes:
                urls_imagenes = [imagen_url]
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
