from concurrent.futures import ThreadPoolExecutor
import os
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin


app = Flask(__name__)
CORS(app)

# Configurar Selenium con Chrome
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ejecutar en modo headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/noticias', methods=['GET'])
def obtener_noticias():
    try:
        url = "https://www.ciudad.com.ar/espectaculos/"
        driver = get_driver()  # inicializa Selenium
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        noticias = soup.find_all('article', class_='card__container card__horizontal')[:5]
        
        resultado = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_article = {executor.submit(fetch_article, noticia, driver): noticia for noticia in noticias}
            for future in future_to_article:
                articulo_data = future.result()
                if articulo_data:
                    resultado.append(articulo_data)
        
        return jsonify(resultado)
    
    except Exception as e:
        # Imprimir el error en los logs de Render para que puedas depurarlo
        print(f"Error al obtener noticias: {e}")
        return jsonify({"error": "Error al obtener noticias"}), 500
    
    finally:
        driver.quit()


def fetch_article(noticia, driver):
    title = noticia.find('h2', class_='card__headline')
    parrafo = noticia.find('p', class_='card__subheadline')
    picture = noticia.find('picture', class_='responsive-image')
    link = noticia.find('a')
    link_href = link['href'] if link else None
    imagen = picture.find('img') if picture else None
    imagen_url = imagen['src'] if imagen else None

    if imagen_url and not imagen_url.startswith('http'):
        imagen_url = urljoin("https://www.ciudad.com.ar", imagen_url)

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
            urls_imagenes = [img['src'] for img in imagenes if 'src' in img.attrs]
        else:
            date, seccion, contenido, urls_imagenes = None, None, [], []

        return {
            'title': title.text.strip(),
            'parrafo': parrafo.text.strip() if parrafo else None,
            'imageUrl': imagen_url,
            'urls_imagenes': urls_imagenes,
            'link_href': urljoin("https://www.ciudad.com.ar", link_href),
            'seccion': (seccion.text.strip() + ' | ESPECTACULOS') if seccion else 'ESPECTACULOS',
            'date': date.text.strip() if date else None,
            'contenido': " ".join(contenido)
        }
    return None

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Puerto asignado por Render
    app.run(host='0.0.0.0', port=port)
