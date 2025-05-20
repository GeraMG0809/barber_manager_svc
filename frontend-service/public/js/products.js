async function loadProducts() {
    try {
        const response = await fetch('http://localhost:5000/api/products', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!response.ok) {
            throw new Error('Error al obtener los productos');
        }

        const products = await response.json();
        const productsContainer = document.getElementById('productsContainer');
        
        // Limpiar contenedor
        productsContainer.innerHTML = '';
        
        // Crear tarjetas para cada producto
        products.forEach(product => {
            const productCard = document.createElement('div');
            productCard.className = 'product-card';
            productCard.innerHTML = `
                <h3>${product.name}</h3>
                <p>Precio: $${product.price}</p>
                <p>Stock: ${product.stock}</p>
                <button onclick="addToCart(${product.id})">Agregar al carrito</button>
            `;
            productsContainer.appendChild(productCard);
        });
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar los productos');
    }
}

// Cargar los productos cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
}); 