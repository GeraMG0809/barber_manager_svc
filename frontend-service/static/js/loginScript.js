document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const btnSignUp = document.getElementById('btn-sign-up');
    const btnSignIn = document.getElementById('btn-sign-in');
    const container = document.querySelector('.container');

    // Función para mostrar mensajes de error
    function showError(element, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        errorDiv.style.color = '#ff4444';
        errorDiv.style.fontSize = '12px';
        errorDiv.style.marginTop = '5px';
        element.parentNode.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 3000);
    }

    // Función para validar email
    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    // Función para validar teléfono
    function isValidPhone(phone) {
        return /^[0-9]{10}$/.test(phone);
    }

    // Función para validar contraseña
    function isValidPassword(password) {
        return password.length >= 6;
    }

    // Manejar el formulario de login
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(loginForm);
        const email = formData.get('email');
        const password = formData.get('password');

        // Validaciones
        if (!isValidEmail(email)) {
            showError(loginForm.querySelector('input[name="email"]'), 'Ingresa un email válido');
            return;
        }

        if (!isValidPassword(password)) {
            showError(loginForm.querySelector('input[name="password"]'), 'La contraseña debe tener al menos 6 caracteres');
            return;
        }

        const data = { email, password };

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                // Guardar el token y datos del usuario
                console.log('Respuesta del servidor:', result);
                localStorage.setItem('token', result.access_token);
                localStorage.setItem('user', JSON.stringify(result.user));
                
                // Mostrar mensaje de éxito
                const successMessage = document.createElement('div');
                successMessage.className = 'success-message';
                successMessage.textContent = '¡Inicio de sesión exitoso!';
                successMessage.style.color = '#00C851';
                successMessage.style.fontSize = '14px';
                successMessage.style.marginTop = '10px';
                loginForm.appendChild(successMessage);

                // Redirigir después de un breve delay
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            } else {
                showError(loginForm, result.error || 'Error al iniciar sesión');
            }
        } catch (error) {
            console.error('Error:', error);
            showError(loginForm, 'Error al conectar con el servidor');
        }
    });

    // Manejar el formulario de registro
    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(registerForm);
        const nombre = formData.get('nombre');
        const telefono = formData.get('telefono');
        const email = formData.get('email');
        const password = formData.get('password');

        // Validaciones
        if (nombre.length < 3) {
            showError(registerForm.querySelector('input[name="nombre"]'), 'El nombre debe tener al menos 3 caracteres');
            return;
        }

        if (!isValidPhone(telefono)) {
            showError(registerForm.querySelector('input[name="telefono"]'), 'Ingresa un número de teléfono válido (10 dígitos)');
            return;
        }

        if (!isValidEmail(email)) {
            showError(registerForm.querySelector('input[name="email"]'), 'Ingresa un email válido');
            return;
        }

        if (!isValidPassword(password)) {
            showError(registerForm.querySelector('input[name="password"]'), 'La contraseña debe tener al menos 6 caracteres');
            return;
        }

        const data = { 
            name: nombre,
            phone: telefono,
            email: email,
            password: password
        };

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                // Mostrar mensaje de éxito
                const successMessage = document.createElement('div');
                successMessage.className = 'success-message';
                successMessage.textContent = '¡Registro exitoso! Redirigiendo al login...';
                successMessage.style.color = '#00C851';
                successMessage.style.fontSize = '14px';
                successMessage.style.marginTop = '10px';
                registerForm.appendChild(successMessage);

                // Cambiar a la vista de login después de un breve delay
                setTimeout(() => {
                    container.classList.remove('active');
                    registerForm.reset();
                }, 2000);
            } else {
                showError(registerForm, result.error || 'Error al registrar usuario');
            }
        } catch (error) {
            console.error('Error:', error);
            showError(registerForm, 'Error al conectar con el servidor');
        }
    });

    // Botones para cambiar entre login y registro
    btnSignUp.addEventListener('click', () => {
        container.classList.add('active');
        loginForm.reset();
    });

    btnSignIn.addEventListener('click', () => {
        container.classList.remove('active');
        registerForm.reset();
    });

    // Limpiar mensajes de error al cambiar de formulario
    container.addEventListener('transitionend', () => {
        const errorMessages = document.querySelectorAll('.error-message');
        errorMessages.forEach(msg => msg.remove());
    });
});