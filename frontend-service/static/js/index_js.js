document.addEventListener('DOMContentLoaded', () => {
  const productCarousel = document.getElementById('product-carousel');
  const productItems = document.querySelectorAll('.product-item');
  const prevButton = document.getElementById('prev');
  const nextButton = document.getElementById('next');
  
  const totalProducts = productItems.length;
  const visibleItems = 3;
  let currentIndex = 0;

  // Mostrar solo los productos visibles (3 a la vez)
  const showProducts = () => {
    const startIndex = currentIndex;
    const endIndex = startIndex + visibleItems;
    
    // Cambia la posición del carrusel
    productCarousel.style.transform = `translateX(-${startIndex * (100 / visibleItems)}%)`;

    // Desactivar los botones de navegación si llegamos al principio o al final
    prevButton.disabled = currentIndex === 0;
    nextButton.disabled = currentIndex + visibleItems >= totalProducts;
  };

  // Evento para el botón "Anterior"
  prevButton.addEventListener('click', () => {
    if (currentIndex > 0) {
      currentIndex--;
      showProducts();
    }
  });

  // Evento para el botón "Siguiente"
  nextButton.addEventListener('click', () => {
    if (currentIndex + visibleItems < totalProducts) {
      currentIndex++;
      showProducts();
    }
  });

  // Inicializar el carrusel
  showProducts();
});
