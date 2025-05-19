function filtroCitas(){

  const filtroBarbero = document.getElementById('filtroBarbero');
  const filtroHora = document.getElementById('filtroHora');
  const filtroFecha = document.getElementById('filtroFecha');
  const btnLimpiarFiltros = document.getElementById('limpiarFiltros');
  const citas = document.querySelectorAll('.cita-card');
  const mensajeNoResultados = document.getElementById('mensajeNoResultados');

  function filtrarCitas() {
  const barbero = filtroBarbero.value.toLowerCase();
  const hora = filtroHora.value;
  const fecha = filtroFecha.value;

  let hayResultados = false;

  citas.forEach(cita => {
    const citaBarbero = cita.getAttribute('data-barbero');
    const citaHora = cita.getAttribute('data-hora').substring(0, 5); // <<< cortar solo HH:MM
    const citaFecha = cita.getAttribute('data-fecha');

    const matchBarbero = !barbero || citaBarbero.toLowerCase() === barbero;
    const matchHora = !hora || citaHora === hora;
    const matchFecha = !fecha || citaFecha === fecha;

    if (matchBarbero && matchHora && matchFecha) {
      cita.style.display = 'block';
      hayResultados = true;
    } else {
      cita.style.display = 'none';
    }
  });

  mensajeNoResultados.style.display = hayResultados ? 'none' : 'block';

  }

  filtroBarbero.addEventListener('change', filtrarCitas);
  filtroHora.addEventListener('change', filtrarCitas);
  filtroFecha.addEventListener('input', filtrarCitas);

  btnLimpiarFiltros.addEventListener('click', () => {
    filtroBarbero.value = '';
    filtroHora.value = '';
    filtroFecha.value = '';
    filtrarCitas();
  });
}

function abrirModalPago(idCita, cliente, barbero, servicio, monto) {
  document.getElementById('modalCliente').textContent = cliente;
  document.getElementById('modalBarbero').textContent = barbero;
  document.getElementById('modalServicio').textContent = servicio;
  document.getElementById('modalMonto').textContent = monto.toFixed(2);
}



function configModal() {
    const modalPago = document.getElementById('modalPago');
    const selectorProductos = document.getElementById('selectorProductos');
    let montoServicio = 0;

    modalPago.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        const cliente = button.getAttribute('data-cliente');
        const idCita = button.getAttribute('data-idcita');
        const barbero = button.getAttribute('data-barbero');
        const servicio = button.getAttribute('data-servicio');
        const monto = button.getAttribute('data-monto');

        montoServicio = parseFloat(monto);

        document.getElementById('modalCliente').textContent = cliente;
        document.getElementById('modalBarbero').textContent = barbero;
        document.getElementById('modalServicio').textContent = servicio;
        document.getElementById('modalMonto').textContent = monto;
        document.getElementById('montoFinal').textContent = monto;

        // Resetear el selector de productos
        selectorProductos.value = '';
        document.getElementById('precioProducto').textContent = '0.00';
    });

    // Manejar cambios en el selector de productos
    selectorProductos.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const precioProducto = selectedOption.value ? parseFloat(selectedOption.dataset.precio) : 0;
        const montoFinal = montoServicio + precioProducto;

        document.getElementById('precioProducto').textContent = precioProducto.toFixed(2);
        document.getElementById('montoFinal').textContent = montoFinal.toFixed(2);
    });

    // Manejar el botón de confirmar pago
    document.getElementById('btnConfirmarPago').addEventListener('click', function() {
        const idCita = document.querySelector('[data-idcita]').getAttribute('data-idcita');
        const metodoPago = document.getElementById('metodoPago').value;
        const montoFinal = parseFloat(document.getElementById('montoFinal').textContent);
        
        // Obtener el producto seleccionado
        const selectorProductos = document.getElementById('selectorProductos');
        const idProducto = selectorProductos.value;

        if (!idCita || !metodoPago || !idProducto || isNaN(montoFinal)) {
            alert('Por favor, complete todos los campos');
            return;
        }

        // Enviar datos al servidor
        fetch('/crear_venta', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id_cita: idCita,
                id_producto: idProducto,
                tipo_pago: metodoPago,
                monto_final: montoFinal
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                // Cerrar el modal y recargar la página
                const modal = bootstrap.Modal.getInstance(modalPago);
                modal.hide();
                window.location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al procesar el pago');
    });
  });
}



function montoFinal(){
  document.addEventListener("DOMContentLoaded", function () {
    const productoSelect = document.getElementById("producto");
    const precioProductoInput = document.getElementById("precioProducto");
    const montoServicioSpan = document.getElementById("modalMonto");
    const montoFinalSpan = document.getElementById("montoFinal");

    // Actualiza el precio del producto seleccionado al cargar el modal
    const productoSeleccionado = productoSelect.options[productoSelect.selectedIndex];
    precioProductoInput.value = productoSeleccionado ? productoSeleccionado.dataset.precio : '0.00';

    // Actualiza el monto final al cambiar el producto
    productoSelect.addEventListener("change", function () {
        const precioProducto = parseFloat(this.options[this.selectedIndex].dataset.precio);
        const montoServicio = parseFloat(montoServicioSpan.textContent) || 0;

        // Actualiza el campo de precio del producto
        precioProductoInput.value = precioProducto.toFixed(2);

        // Calcula el monto final
        const montoFinal = montoServicio + precioProducto;
        montoFinalSpan.textContent = montoFinal.toFixed(2);
    });
});

}


function new_venta(){
  document.addEventListener('DOMContentLoaded', () => {
    configModal();
  
    // Evento al confirmar el pago
    document.getElementById('btnConfirmarPago').addEventListener('click', async () => {
      const idCita = document.getElementById('modalPago').dataset.idcita;
      const metodoPago = document.getElementById('metodoPago').value;
  
      try {
        const response = await fetch('/finalizar_venta', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            id_cita: idCita,
            metodo_pago: metodoPago
          }),
        });
  
        const result = await response.json();
        if (result.success) {
          alert('Venta registrada correctamente');
          location.reload();
        } else {
          alert('Error al registrar la venta');
        }
      } catch (error) {
        console.error('Error:', error);
        alert('Error en la solicitud');
      }
    });
  });
  
}

