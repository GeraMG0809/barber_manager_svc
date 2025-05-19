const express = require('express');
const path = require('path');
const cors = require('cors');
const axios = require('axios');
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

app.use(cors());
app.use(express.json());

// Servir archivos estáticos
app.use(express.static(path.join(__dirname, 'static')));
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
  next();
});

// Middleware para verificar autenticación
const verifyToken = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
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
      user: req.session?.user
    });
  } catch (error) {
    console.error('Error:', error);
    res.render('index', { barberos: [], productos: [], user: null });
  }
});

app.get('/login', (req, res) => {
  res.render('loginUser');
});

app.get('/admin', (req, res) => {
  res.render('loginAdmin');
});

app.get('/adminManager', (req, res) => {
  res.render('AdminManager');
});

app.get('/barber', (req, res) => {
  res.render('barberPage');
});

app.get('/productos', (req, res) => {
  res.render('productos');
});

app.get('/venta', (req, res) => {
  res.render('venta');
});

// API Proxy para autenticación
app.post('/api/auth/login', async (req, res) => {
  try {
    const response = await axios.post(`${SERVICES.auth}/auth/login`, req.body);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Error interno del servidor' });
  }
});

app.post('/api/auth/register', async (req, res) => {
  try {
    const response = await axios.post(`${SERVICES.auth}/auth/register`, req.body);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json(error.response?.data || { error: 'Error interno del servidor' });
  }
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
        'Authorization': `Bearer ${req.headers.authorization.split(' ')[1]}`
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