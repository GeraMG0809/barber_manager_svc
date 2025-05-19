document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('date');
    const timeSelect = document.getElementById('time');
    const barberSelect = document.getElementById('barber');
    const bookingForm = document.getElementById('bookingForm');

    // Generar horarios disponibles (de 9 AM a 6 PM)
    function generateTimeSlots() {
        const slots = [];
        for (let hour = 9; hour <= 18; hour++) {
            const time = `${hour.toString().padStart(2, '0')}:00`;
            slots.push(time);
        }
        return slots;
    }

    // Actualizar horarios disponibles
    async function updateAvailableTimes() {
        const date = dateInput.value;
        const barber = barberSelect.value;

        if (!date || !barber) {
            timeSelect.innerHTML = '<option value="" selected disabled>Selecciona un horario</option>';
            return;
        }

        try {
            // Obtener citas existentes para la fecha y barbero seleccionados
            const response = await fetch(`/api/appointments/available?date=${date}&barber=${barber}`);
            const bookedTimes = await response.json();

            // Generar todos los horarios posibles
            const allTimeSlots = generateTimeSlots();
            
            // Filtrar horarios disponibles
            const availableSlots = allTimeSlots.filter(time => !bookedTimes.includes(time));

            // Actualizar el select de horarios
            timeSelect.innerHTML = '<option value="" selected disabled>Selecciona un horario</option>';
            availableSlots.forEach(time => {
                const option = document.createElement('option');
                option.value = time;
                option.textContent = time;
                timeSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error al obtener horarios disponibles:', error);
            alert('Error al cargar los horarios disponibles');
        }
    }

    // Event listeners para actualizar horarios
    dateInput.addEventListener('change', updateAvailableTimes);
    barberSelect.addEventListener('change', updateAvailableTimes);

    // Manejar el envío del formulario de reserva
    bookingForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Verificar si el usuario está autenticado
        const token = localStorage.getItem('token');
        if (!token) {
            alert('Por favor, inicia sesión para reservar una cita');
            window.location.href = '/login';
            return;
        }

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
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                alert('¡Cita reservada exitosamente!');
                bookingForm.reset();
                timeSelect.innerHTML = '<option value="" selected disabled>Selecciona un horario</option>';
            } else {
                alert(result.error || 'Error al reservar la cita');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al conectar con el servidor');
        }
    });
});
