from concurrent.futures import ThreadPoolExecutor
import os
from flask import Flask, render_template, send_from_directory, jsonify
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
chrome_options = Options()
chrome_options.add_argument("--headless")  # Para ejecutar en modo headless (sin interfaz gráfica)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Inicializar el driver de Selenium
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/noticias', methods=['GET'])
def obtener_noticias():
    url = "https://www.ciudad.com.ar/espectaculos/2024/10/18/santiago-del-moro-adelanto-como-sera-gran-hermano-y-revelo-que-fue-lo-que-mas-le-molesto-de-la-ultima-edicion/"
    # Usar Selenium para cargar la página
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    noticias = soup.find_all('div', class_='common-layout wrapper-layout center-content center_story max-width story article')
    
    print([noticias])




if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Puerto asignado por Render
    app.run(host='0.0.0.0', port=port)
