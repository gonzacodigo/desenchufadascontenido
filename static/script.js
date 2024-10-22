let urlInfobae = "http://desenchufadascontenido.onrender.com/api/noticias/infobae";
let urlCaras = "http://desenchufadascontenido.onrender.com/api/noticias/caras"; // Asegúrate de que este endpoint exista
let cargando = document.getElementById('cargando');
let cargando2 = document.getElementById('cargando2');

function getNoticias(url) {
  cargando.textContent = "Cargando ..."; // Mostrar mensaje de carga
  cargando2.textContent = "Cargando ..."; // Mostrar mensaje de carga

  fetch(url)
    .then((response) => {
      if (!response.ok) {
        return response.text().then((text) => {
          throw new Error(`Error en noticias: ${response.status} ${response.statusText}: ${text}`);
        });
      }
      return response.json();
    })
    .then((data) => {
      getNoticiasHTML(data);
    })
    .catch((error) => {
      console.error("Error al obtener las noticias:", error);
      if (cargando) {
        cargando.textContent = `Error al cargar las noticias: ${error.message}`;
      }
    });
}

function getNoticiasHTML(noticias) {
  let divResultados = document.getElementById("noticias");

  if (!divResultados) {
    console.error('El elemento con id "noticias" no se encontró.');
    return;
  }

  cargando.innerHTML = ""; // Limpiar mensaje de carga
  cargando2.innerHTML = ""; // Limpiar mensaje de carga
  divResultados.innerHTML = ""; // Limpiar contenido anterior

  noticias.forEach((noticia) => {
    let noticiaDiv = document.createElement("div");
    noticiaDiv.classList.add("noticia");

    // Crear los elementos
    let date = document.createElement("p");
    date.textContent = noticia.date;

    let script = document.createElement("script");
    script.src = "https://cse.google.com/cse.js?cx=87467d5905d784a95";
    script.async = true;
    document.head.appendChild(script); // Lo agregas al head del documento

    let inputBusquedaImagenes = document.createElement("div");
    inputBusquedaImagenes.classList.add("gcse-search");

    let seccion = document.createElement("p");
    seccion.textContent = noticia.seccion;

    let title = document.createElement("h2");
    title.textContent = noticia.title;

    let parrafo = document.createElement("h4");
    parrafo.textContent = noticia.parrafo;

    let link = document.createElement("a");
    link.textContent = "Ver nota completa";
    link.href = noticia.link_href;
    link.target = "_blank";

    // Crear la imagen principal con lazy loading
    let imagenUrl = noticia.imageUrl;
    let imagen = document.createElement("img");
    imagen.dataset.src = imagenUrl;
    imagen.classList.add("lazy-load");

    // Crear botón y contenido acordeón
    let contenido = document.createElement("p");
    contenido.textContent = noticia.contenido;
    contenido.style.display = "none";

    let botonAcordeon = document.createElement("button");
    botonAcordeon.textContent = "Mostrar contenido";
    botonAcordeon.classList.add("acordeon-button");

    botonAcordeon.addEventListener("click", function () {
      contenido.style.display = contenido.style.display === "none" ? "block" : "none";
      botonAcordeon.textContent = contenido.style.display === "none" ? "Mostrar contenido" : "Ocultar contenido";
    });

    // Añadir los elementos al div
    noticiaDiv.appendChild(link);
    noticiaDiv.appendChild(date);
    noticiaDiv.appendChild(seccion);
    noticiaDiv.appendChild(title);
    noticiaDiv.appendChild(parrafo);
    noticiaDiv.appendChild(imagen);
    noticiaDiv.appendChild(botonAcordeon);
    noticiaDiv.appendChild(contenido);

    // Verificar y agregar imágenes adicionales si las hay
    if (Array.isArray(noticia.urls_imagenes) && noticia.urls_imagenes.length > 0) {
      let imagenesDiv = document.createElement("div");
      imagenesDiv.style.display = "none";

      noticia.urls_imagenes.forEach((imgUrl) => {
        let img = document.createElement("img");
        img.dataset.src = imgUrl;
        img.style.width = "100px";
        img.classList.add("lazy-load");
        imagenesDiv.appendChild(img);
      });

      let botonMostrarImagenes = document.createElement("button");
      botonMostrarImagenes.textContent = "Mostrar fotos adicionales";
      botonMostrarImagenes.classList.add("boton-imagenes");
      botonMostrarImagenes.addEventListener("click", function () {
        imagenesDiv.style.display = imagenesDiv.style.display === "none" ? "block" : "none";
        botonMostrarImagenes.textContent = imagenesDiv.style.display === "none" ? "Mostrar fotos adicionales" : "Ocultar fotos adicionales";
      });

      noticiaDiv.appendChild(botonMostrarImagenes);
      noticiaDiv.appendChild(imagenesDiv);
      noticiaDiv.appendChild(inputBusquedaImagenes);

    }

    divResultados.appendChild(noticiaDiv);
  });

  lazyLoadImages();
}

// Lazy loading de imágenes
function lazyLoadImages() {
  const lazyImages = document.querySelectorAll("img.lazy-load");

  if ("IntersectionObserver" in window) {
    let lazyImageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          let lazyImage = entry.target;
          lazyImage.src = lazyImage.dataset.src;
          lazyImage.classList.remove("lazy-load");
          lazyImageObserver.unobserve(lazyImage);
        }
      });
    });

    lazyImages.forEach((lazyImage) => {
      lazyImageObserver.observe(lazyImage);
    });
  } else {
    lazyImages.forEach((img) => {
      img.src = img.dataset.src;
    });
  }
}

// Eventos de los botones
document.getElementById('infobaeBtn').addEventListener('click', function() {
  getNoticias(urlInfobae);
});

document.getElementById('carasBtn').addEventListener('click', function() {
  getNoticias(urlCaras); // Cambia este endpoint según sea necesario
});

// Llamar a la función para cargar las noticias de Infobae al cargar la página
document.addEventListener("DOMContentLoaded", function() {
  getNoticias(urlInfobae);
});
