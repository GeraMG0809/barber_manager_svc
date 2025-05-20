async function loadBarbers() {
    try {
        const response = await fetch('http://localhost:5000/api/barbers', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Error al obtener los barberos');
        }

        const barbers = await response.json();
        const barberSelect = document.getElementById('barberSelect');
        
        // Limpiar opciones existentes
        barberSelect.innerHTML = '<option value="">Seleccione un barbero</option>';
        
        // Agregar los barberos al selector
        barbers.forEach(barber => {
            const option = document.createElement('option');
            option.value = barber.id;
            option.textContent = barber.name;
            barberSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar los barberos');
    }
}

async function loadAppointments() {
    try {
        const response = await fetch('http://localhost:5000/api/appointments/user', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!response.ok) {
            throw new Error('Error al obtener las citas');
        }

        const appointments = await response.json();
        const appointmentsContainer = document.getElementById('appointmentsContainer');
        
        // Limpiar contenedor
        appointmentsContainer.innerHTML = '';
        
        // Crear tarjetas para cada cita
        appointments.forEach(appointment => {
            const appointmentCard = document.createElement('div');
            appointmentCard.className = 'appointment-card';
            appointmentCard.innerHTML = `
                <h3>Cita con ${appointment.barber_name}</h3>
                <p>Fecha: ${new Date(appointment.date).toLocaleDateString()}</p>
                <p>Hora: ${appointment.time}</p>
                <p>Estado: ${appointment.status}</p>
                <button onclick="cancelAppointment(${appointment.id})">Cancelar cita</button>
            `;
            appointmentsContainer.appendChild(appointmentCard);
        });
    } catch (error) {
        console.error('Error:', error);
        alert('Error al cargar las citas');
    }
}

// Cargar los barberos y las citas cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    loadBarbers();
    loadAppointments();
}); 