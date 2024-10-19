from concurrent.futures import ThreadPoolExecutor
import os
from urllib.parse import urljoin
from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
CORS(app)

# Configurar Selenium con Chrome
chrome_options = Options()
# Para ejecutar en modo headless (sin interfaz gráfica)
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# Asegúrate de que esta sea la ruta correcta a Chromium en Render
chrome_options.binary_location = "/usr/bin/chromium"

# Inicializar el driver de Selenium
driver = webdriver.Chrome(service=ChromeService(
    ChromeDriverManager().install()), options=chrome_options)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


@app.route('/api/noticias', methods=['GET'])
def obtener_noticias():
    url = "https://www.ciudad.com.ar/espectaculos/"
    # Usar Selenium para cargar la página
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    noticias = soup.find_all(
        'article', class_='card__container card__horizontal')[:15]

    resultado = []

    # Realizar las solicitudes en paralelo para obtener detalles de los artículos
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_article = {executor.submit(
            fetch_article, noticia): noticia for noticia in noticias}
        for future in future_to_article:
            articulo_data = future.result()
            if articulo_data:
                resultado.append(articulo_data)

    return jsonify(resultado)


def fetch_article(noticia):
    title = noticia.find('h2', class_='card__headline')
    parrafo = noticia.find('p', class_='card__subheadline')
    picture = noticia.find('picture', class_='responsive-image')
    link = noticia.find('a')
    link_href = link['href'] if link else None
    imagen = picture.find('img') if picture else None
    imagen_url = imagen['src'] if imagen else None

    if imagen_url and not imagen_url.startswith('http'):
        imagen_url = urljoin("https://www.ciudad.com.ar", imagen_url)

    # Usar Selenium para cargar el artículo completo
    if link_href:
        driver.get(urljoin("https://www.ciudad.com.ar", link_href))
        soup_article = BeautifulSoup(driver.page_source, 'html.parser')
        noticias_article = soup_article.find_all('div', class_='fusion-app')

        if noticias_article:
            date = noticias_article[0].find('span', class_="time__value")
            seccion_div = noticias_article[0].find('div', class_="breadcrumb")
            seccion = seccion_div.find('a') if seccion_div else None

            parrafos = noticias_article[0].find_all('p', class_="paragraph")
            contenido = [parrafo.get_text().strip() for parrafo in parrafos]
            imagenes = noticias_article[0].find_all('img')
            urls_imagenes = [img['src']
                             for img in imagenes if 'src' in img.attrs]
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

    # Usar Selenium para cargar la página
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

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

        # Usar Selenium para cargar el artículo completo
        if link_href:
            driver.get(link_href)
            soup_article = BeautifulSoup(driver.page_source, 'html.parser')
            noticias_article = soup_article.find_all(
                'main', class_='main-container max-width margin-auto container-white considebar')

            if noticias_article:
                date = noticias_article[0].find('span', class_="hat__fecha")
                seccion = noticias_article[0].find('a')
                contenido = noticias_article[0].find(
                    "div", class_="news-content")
                urls_imagenes = [img['src'] for img in contenido.find_all(
                    'img') if 'src' in img.attrs]
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Puerto asignado por Render
    app.run(host='0.0.0.0', port=port)
