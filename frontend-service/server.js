const express = require('express');
const path = require('path');
const cors = require('cors');
const axios = require('axios');
const session = require('express-session');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5005;

// Configuración de las rutas de los servicios
const SERVICES = {
  auth: process.env.AUTH_SERVICE_URL || 'http://auth-service:5001',
  appointments: process.env.APPOINTMENTS_SERVICE_URL || 'http://appointments-service:5002',
  barbers: process.env.BARBERS_SERVICE_URL || 'http://barbers-service:5003',
  products: process.env.PRODUCTS_SERVICE_URL || 'http://products-service:5004'
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
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    maxAge: 24 * 60 * 60 * 1000 // 24 horas
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
  const token = req.headers.authorization?.split(' ')[1] || req.session?.token;
  if (!token) {
    return res.status(401).json({ error: 'Token no proporcionado' });
  }

  try {
    const response = await axios.post(`${SERVICES.auth}/auth/verify`, { token });
    req.user = response.data;
    next();
  } catch (error) {
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
    const [barberos, productos] = await Promise.all([
      axios.get(`${SERVICES.barbers}/barbers`),
      axios.get(`${SERVICES.products}/products`)
    ]);
    res.render('index', {
      barberos: barberos.data,
      productos: productos.data,
      user: req.session.user
    });
  } catch (error) {
    console.error('Error:', error);
    res.render('index', { barberos: [], productos: [], user: null });
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
    req.session.user = response.data.user;
    req.session.token = response.data.access_token;
    res.json(response.data);
  } catch (error) {
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

// API Proxy para citas
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