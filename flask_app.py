from concurrent.futures import ThreadPoolExecutor
import os
from flask import Flask, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
CORS(app)

# Configuración para manejar múltiples hilos
executor = ThreadPoolExecutor(max_workers=5)

# Configurar Selenium de manera dinámica
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ejecutar en modo headless (sin interfaz gráfica)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

@app.route('/api/noticias', methods=['GET'])
def obtener_noticias():
    url = "https://www.ciudad.com.ar/espectaculos/2024/10/18/santiago-del-moro-adelanto-como-sera-gran-hermano-y-revelo-que-fue-lo-que-mas-le-molesto-de-la-ultima-edicion/"
    
    # Ejecutar en un hilo separado para evitar bloqueos
    future = executor.submit(scrape_noticias, url)
    noticias = future.result()
    
    if noticias:
        return jsonify({"noticias": noticias}), 200
    else:
        return jsonify({"error": "No se encontraron noticias"}), 404

def scrape_noticias(url):
    driver = get_driver()
    try:
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        noticias_elements = soup.find_all('div', class_='content-article-title')

        # Extraer el texto de las noticias
        noticias = [noticia.get_text(strip=True) for noticia in noticias_elements]
        return noticias
    finally:
        # Cerrar el driver de Selenium para liberar recursos
        driver.quit()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Puerto asignado por Render
    app.run(host='0.0.0.0', port=port)
