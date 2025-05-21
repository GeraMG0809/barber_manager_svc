document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('date');
    const timeSelect = document.getElementById('time');
    const barberSelect = document.getElementById('barber');
    const bookingForm = document.getElementById('bookingForm');

    // Establecer la fecha mínima como hoy
    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;

    // Función para cargar y mostrar los barberos disponibles
    async function loadBarbers() {
        try {
            const response = await fetch('/api/barbers');
            if (!response.ok) {
                throw new Error('Error al obtener barberos');
            }
            const data = await response.json();
            console.log('Barberos disponibles:', data);
            
            // Limpiar el select de barberos
            barberSelect.innerHTML = '<option value="" selected disabled>Selecciona un barbero</option>';
            
            // Agregar los barberos al select
            data.data.forEach(barber => {
                const option = document.createElement('option');
                option.value = barber.id;
                option.textContent = barber.nombre;
                barberSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error:', error);
            barberSelect.innerHTML = '<option value="" selected disabled>Error al cargar barberos</option>';
        }
    }

    // Cargar barberos al iniciar
    loadBarbers();

    // Actualizar horarios disponibles
    function updateAvailableTimes() {
        const date = dateInput.value;
        const barberId = barberSelect.value;

        if (!date || !barberId) {
            timeSelect.innerHTML = '<option value="" selected disabled>Selecciona un horario</option>';
            return;
        }

        // Generar slots de tiempo fijos de 10 AM a 8 PM
        const slots = [];
        for (let hour = 10; hour <= 20; hour++) {
            const time = `${hour.toString().padStart(2, '0')}:00`;
            slots.push(time);
        }

        // Actualizar el select de horarios
        timeSelect.innerHTML = '<option value="" selected disabled>Selecciona un horario</option>';
        slots.forEach(time => {
            const option = document.createElement('option');
            option.value = time;
            option.textContent = time;
            timeSelect.appendChild(option);
        });
    }

    // Event listeners para actualizar horarios
    dateInput.addEventListener('change', updateAvailableTimes);
    barberSelect.addEventListener('change', updateAvailableTimes);

    // Manejar el envío del formulario de reserva
    bookingForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData(bookingForm);
        const data = {
            nombre: formData.get('nombre'),
            telefono: formData.get('telefono'),
            fecha: formData.get('fecha'),
            hora: formData.get('hora'),
            barbero: formData.get('barbero'),
            servicio: formData.get('servicio')
        };

        try {
            const response = await fetch('/api/appointments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                alert('¡Cita reservada exitosamente!');
                bookingForm.reset();
                timeSelect.innerHTML = '<option value="" selected disabled>Selecciona un horario</option>';
            } else {
                throw new Error(result.error || 'Error al reservar la cita');
            }
        } catch (error) {
            console.error('Error:', error);
            alert(error.message || 'Error al conectar con el servidor');
        }
    });
});
