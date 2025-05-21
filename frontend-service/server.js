const express = require('express');
const path = require('path');
const cors = require('cors');
const axios = require('axios');
const session = require('express-session');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5005;

// Configuración de las rutas de los servicios
const API_URL = process.env.API_URL || 'http://api-gateway:5000';
const SERVICES = {
  auth: `${API_URL}/api/auth`,
  appointments: `${API_URL}/api/appointments`,
  barbers: `${API_URL}/api/barbers`,
  products: `${API_URL}/api/products`
};

// Configuración de CORS
app.use(cors({
    origin: ['http://localhost:5000', 'http://localhost:5005'],
    credentials: true
}));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Configuración de sesión
app.use(session({
  secret: process.env.SESSION_SECRET || 'your-secret-key',
  resave: true,
  saveUninitialized: true,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    maxAge: 24 * 60 * 60 * 1000, // 24 horas
    httpOnly: true
  }
}));

// Middleware para servir archivos estáticos
app.use(express.static(path.join(__dirname, 'public')));
app.use('/css', express.static(path.join(__dirname, 'static/css')));
app.use('/js', express.static(path.join(__dirname, 'static/js')));
app.use('/images', express.static(path.join(__dirname, 'static/images')));

// Configurar el motor de plantillas
app.set('views', path.join(__dirname, 'templates'));
app.set('view engine', 'html');
app.engine('html', require('ejs').renderFile);

// Middleware para agregar variables globales a las plantillas
app.use((req, res, next) => {
  res.locals.staticPath = '/static';
  res.locals.stylesPath = '/css';
  res.locals.jsPath = '/js';
  res.locals.imagesPath = '/images';
  res.locals.user = req.session.user || null;
  next();
});

// Middleware para verificar autenticación
const verifyToken = async (req, res, next) => {
  console.log('Sesión actual:', req.session);
  const token = req.session?.token;
  
  if (!token) {
    console.log('No hay token en la sesión');
    return res.status(401).json({ error: 'Token no proporcionado' });
  }

  try {
    console.log('Verificando token:', token);
    const response = await axios.post(`${SERVICES.auth}/auth/verify`, { token });
    req.user = response.data;
    next();
  } catch (error) {
    console.error('Error verificando token:', error.response?.data || error.message);
    res.status(401).json({ error: 'Token inválido' });
  }
};

// Middleware para verificar rol de administrador
const isAdmin = (req, res, next) => {
  if (!req.session.user || req.session.user.role !== 'admin') {
    return res.redirect('/admin');
  }
  next();
};

// Rutas principales
app.get('/', async (req, res) => {
  try {
    console.log('Intentando obtener barberos de:', `${SERVICES.barbers}`);
    const barberosResponse = await axios.get(`${SERVICES.barbers}`);
    console.log('Respuesta de barberos:', barberosResponse.data);
    
    const productosResponse = await axios.get(`${SERVICES.products}`);
    console.log('Respuesta de productos:', productosResponse.data);

    // Asegurarnos de que barberos sea siempre un array
    const barberos = Array.isArray(barberosResponse.data) 
      ? barberosResponse.data 
      : (barberosResponse.data.data || []);

    res.render('index', {
      barberos: barberos,
      productos: productosResponse.data || [],
      user: req.session.user || null,
      error: null
    });
  } catch (error) {
    console.error('Error detallado:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status
    });
    res.render('index', { 
      barberos: [], 
      productos: [], 
      user: null,
      error: 'Error al cargar los datos'
    });
  }
});

app.get('/login', (req, res) => {
  if (req.session.user) {
    return res.redirect('/');
  }
  res.render('loginUser');
});

app.get('/admin', (req, res) => {
  if (req.session.user && req.session.user.role === 'admin') {
    return res.redirect('/adminManager');
  }
  res.render('loginAdmin');
});

app.get('/adminManager', isAdmin, (req, res) => {
  res.render('AdminManager', { user: req.session.user });
});

app.get('/barber', verifyToken, (req, res) => {
  res.render('barberPage', { user: req.session.user });
});

app.get('/productos', (req, res) => {
  res.render('productos', { user: req.session.user });
});

app.get('/venta', verifyToken, (req, res) => {
  res.render('venta', { user: req.session.user });
});

// API Proxy para autenticación
app.post('/api/auth/login', async (req, res) => {
  try {
    const response = await axios.post(`${SERVICES.auth}/auth/login`, req.body);
    console.log('Respuesta de login:', response.data);
    
    // Guardar en la sesión
    req.session.user = response.data.user;
    req.session.token = response.data.access_token;
    
    // Guardar cambios en la sesión
    req.session.save((err) => {
      if (err) {
        console.error('Error guardando sesión:', err);
        return res.status(500).json({ error: 'Error al iniciar sesión' });
      }
      console.log('Sesión guardada:', req.session);
      res.json(response.data);
    });
  } catch (error) {
    console.error('Error en login:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Error interno del servidor' });
  }
});

app.post('/api/auth/register', async (req, res) => {
  try {
    const response = await axios.post(`${SERVICES.auth}/auth/register`, req.body);
    req.session.user = response.data.user;
    req.session.token = response.data.access_token;
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Error interno del servidor' });
  }
});

app.get('/api/auth/logout', (req, res) => {
  req.session.destroy();
  res.json({ message: 'Sesión cerrada exitosamente' });
});

// API Proxy para barberos
app.get('/api/barbers', async (req, res) => {
  try {
    console.log('Obteniendo barberos de:', `${SERVICES.barbers}`);
    const response = await axios.get(`${SERVICES.barbers}`);
    console.log('Respuesta de barberos:', response.data);
    res.json(response.data);
  } catch (error) {
    console.error('Error obteniendo barberos:', error.response?.data || error.message);
    res.status(error.response?.status || 500).json({ error: 'Error al obtener barberos' });
  }
});

app.get('/api/barbers/:id/schedule', async (req, res) => {
  try {
    const response = await axios.get(`${SERVICES.barbers}/${req.params.id}/schedule`);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({ error: 'Error al obtener horario' });
  }
});

app.get('/api/appointments/available', async (req, res) => {
  try {
    const { date, barber } = req.query;
    const response = await axios.get(`${SERVICES.appointments}/appointments/available`, {
      params: { date, barber }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Error interno del servidor' });
  }
});

app.post('/api/appointments', verifyToken, async (req, res) => {
  try {
    const response = await axios.post(`${SERVICES.appointments}/appointments`, req.body, {
      headers: {
        'Authorization': `Bearer ${req.session.token}`
      }
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Error interno del servidor' });
  }
});

// Middleware para manejar errores 404
app.use((req, res) => {
  res.status(404).render('index', { error: 'Página no encontrada' });
});

app.listen(PORT, () => {
  console.log(`Frontend service running on port ${PORT}`);
}); 