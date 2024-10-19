let url = "https://desenchufadascontenido.onrender.com/api/noticias";
let url_caras = "https://desenchufadascontenido.onrender.com/api/noticias/caras";
let cargando = document.getElementById("cargando");

function getNoticias() {
  // Hacer fetch a ambas APIs en paralelo
  Promise.all([
    fetch(url).then((response) => {
      if (!response.ok) {
        return response.text().then((text) => {
          throw new Error(
            `Error en noticias: ${response.status} ${response.statusText}: ${text}`
          );
        });
      }
      return response.json();
    }),
    fetch(url_caras).then((response) => {
      if (!response.ok) {
        return response.text().then((text) => {
          throw new Error(
            `Error en noticias/caras: ${response.status} ${response.statusText}: ${text}`
          );
        });
      }
      return response.json();
    }),
  ])
    .then(([data, dataCaras]) => {
      // Procesar los datos de ambas APIs
      getNoticiasHTML(data, dataCaras);
    })
    .catch((error) => {
      console.error("Error al obtener las noticias:", error);
      if (cargando) {
        cargando.textContent = `Error al cargar las noticias: ${error.message}`;
      }
    });
}

function getNoticiasHTML(noticias, noticiasCaras) {
  let divResultados = document.getElementById("noticias");

  if (!divResultados) {
    console.error('El elemento con id "noticias" no se encontró.');
    return;
  }

  if (cargando) {
    cargando.innerHTML = ""; // Limpiar mensaje de carga
  }

  divResultados.innerHTML = ""; // Limpiar contenido anterior

  // Combinar los datos de ambas APIs
  let allNoticias = noticias.concat(noticiasCaras);

  allNoticias.forEach((noticia) => {
    let noticiaDiv = document.createElement("div");
    noticiaDiv.classList.add("noticia");

    let script = document.createElement("script");
    script.src = "https://cse.google.com/cse.js?cx=87467d5905d784a95";
    script.async = true;
    document.head.appendChild(script); // Lo agregas al head del documento

    let inputBusquedaImagenes = document.createElement("div");
    inputBusquedaImagenes.classList.add("gcse-search");

    let date = document.createElement("p");
    date.textContent = noticia.date;

    let seccion = document.createElement("p");
    seccion.textContent = noticia.seccion;

    let title = document.createElement("h2");
    title.textContent = noticia.title;

    let parrafo = document.createElement("h4");
    parrafo.textContent = noticia.parrafo;

    // Contenedor para el contenido que se ocultará y mostrará
    let contenido = document.createElement("p");
    contenido.textContent = noticia.contenido;
    contenido.style.display = "none"; // Ocultar por defecto

    let link = document.createElement("a");
    link.textContent = "Ver nota completa";
    link.href = noticia.link_href;
    link.target = "_blank"; // Abrir el enlace en una nueva pestaña

    // Verificar la URL de la imagen principal
    let imagenUrl = noticia.imageUrl;
    console.log(
      `Verificando imagen de: ${noticia.title} - Imagen URL: ${imagenUrl}`
    );

    let imagen = document.createElement("img");
    imagen.dataset.src = imagenUrl; // Lazy load usando dataset
    imagen.classList.add("lazy-load"); // Añadir clase para lazy loading

    // Crear un botón que funcionará como acordeón
    let botonAcordeon = document.createElement("button");
    botonAcordeon.textContent = "Mostrar contenido";
    botonAcordeon.classList.add("acordeon-button");

    // Función que alterna el contenido visible/oculto
    botonAcordeon.addEventListener("click", function () {
      if (contenido.style.display === "none") {
        contenido.style.display = "block"; // Mostrar contenido
        botonAcordeon.textContent = "Ocultar contenido";
      } else {
        contenido.style.display = "none"; // Ocultar contenido
        botonAcordeon.textContent = "Mostrar contenido";
      }
    });

    // Crear el contenedor de imágenes adicionales (inicialmente oculto)
    let imagenesDiv = document.createElement("div");
    imagenesDiv.style.display = "none"; // Oculto por defecto

    // Verificar si `urls_imagenes` existe y contiene imágenes
    if (
      Array.isArray(noticia.urls_imagenes) &&
      noticia.urls_imagenes.length > 0
    ) {
      console.log(
        `Se encontraron imágenes adicionales para: ${noticia.title} - Cantidad de imágenes: ${noticia.urls_imagenes.length}`
      );

      noticia.urls_imagenes.forEach((imgUrl) => {
        let img = document.createElement("img");
        img.dataset.src = imgUrl; // Lazy load
        img.style.width = "100px"; // Tamaño pequeño para cada imagen
        img.style.margin = "5px";
        img.classList.add("lazy-load"); // Añadir clase para lazy load
        imagenesDiv.appendChild(img);
      });

      // Crear el botón para mostrar imágenes adicionales
      let botonMostrarImagenes = document.createElement("button");
      botonMostrarImagenes.textContent = "Mostrar fotos adicionales";
      botonMostrarImagenes.classList.add("boton-imagenes");

      // Alternar visibilidad de las imágenes adicionales
      botonMostrarImagenes.addEventListener("click", function () {
        if (imagenesDiv.style.display === "none") {
          imagenesDiv.style.display = "block"; // Mostrar imágenes
          botonMostrarImagenes.textContent = "Ocultar fotos adicionales";
        } else {
          imagenesDiv.style.display = "none"; // Ocultar imágenes
          botonMostrarImagenes.textContent = "Mostrar fotos adicionales";
        }
      });

      noticiaDiv.appendChild(date);
      noticiaDiv.appendChild(seccion);
      noticiaDiv.appendChild(title);
      noticiaDiv.appendChild(parrafo);
      noticiaDiv.appendChild(imagen);
      noticiaDiv.appendChild(botonAcordeon); // Botón para mostrar/ocultar contenido
      noticiaDiv.appendChild(contenido); // Contenido oculto/visible
      noticiaDiv.appendChild(botonMostrarImagenes); // Agregar el botón solo si hay imágenes
    } else {
      console.log(
        `No se encontraron imágenes adicionales para: ${noticia.title}`
      );
    }
    noticiaDiv.appendChild(imagenesDiv); // Contenedor de imágenes adicionales
    noticiaDiv.appendChild(link);
    noticiaDiv.appendChild(inputBusquedaImagenes);

    divResultados.appendChild(noticiaDiv);
  });

  // Aplicar lazy loading a las imágenes
  lazyLoadImages();
}

// Función para aplicar lazy loading
function lazyLoadImages() {
  const lazyImages = document.querySelectorAll("img.lazy-load");

  if ("IntersectionObserver" in window) {
    let lazyImageObserver = new IntersectionObserver(function (
      entries,
      observer
    ) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          let lazyImage = entry.target;
          console.log(`Cargando imagen: ${lazyImage.dataset.src}`);
          lazyImage.src = lazyImage.dataset.src;
          lazyImage.classList.remove("lazy-load");
          lazyImageObserver.unobserve(lazyImage);
        }
      });
    });

    lazyImages.forEach(function (lazyImage) {
      lazyImageObserver.observe(lazyImage);
    });
  } else {
    // Fallback para navegadores sin soporte de IntersectionObserver
    lazyImages.forEach(function (img) {
      img.src = img.dataset.src;
    });
  }
}

// Llamar a la función para cargar las noticias al cargar la página
document.addEventListener("DOMContentLoaded", getNoticias);
