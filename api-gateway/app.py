from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
from flask_cors import CORS
import os
from dotenv import load_dotenv
from functools import wraps
import jwt
from jwt.exceptions import InvalidTokenError

load_dotenv()

app = Flask(__name__, 
    static_folder='../frontend-service/static',
    template_folder='../frontend-service/templates'
)
# Configurar CORS para permitir peticiones desde el frontend
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5005", "http://frontend:5005"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configuración de URLs de los servicios
SERVICES = {
    'auth': os.getenv('AUTH_SERVICE_URL', 'http://auth-service:5001'),
    'appointments': os.getenv('APPOINTMENTS_SERVICE_URL', 'http://appointments-service:5002'),
    'barbers': os.getenv('BARBERS_SERVICE_URL', 'http://barbers-service:5003'),
    'products': os.getenv('PRODUCTS_SERVICE_URL', 'http://products-service:5004')
}

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Token inválido'}), 401

        if not token:
            return jsonify({'error': 'Token no proporcionado'}), 401

        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            request.user = data
        except InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401

        return f(*args, **kwargs)
    return decorated

def forward_request(service, path, method, data=None):
    service_url = SERVICES.get(service)
    if not service_url:
        return jsonify({'error': 'Servicio no encontrado'}), 404

    try:
        url = f"{service_url}{path}"
        headers = {key: value for key, value in request.headers if key != 'Host'}
        
        if method in ['POST', 'PUT']:
            response = requests.request(method, url, json=data, headers=headers)
        else:
            response = requests.request(method, url, headers=headers)
            
        try:
            response_data = response.json()
            return jsonify(response_data), response.status_code
        except ValueError:
            return jsonify({'error': 'Error al procesar la respuesta del servicio'}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

# Rutas de autenticación (no requieren token)
@app.route('/api/auth/<path:path>', methods=['POST', 'GET', 'PUT'])
def auth_routes(path):
    return forward_request('auth', f'/{path}', request.method, request.get_json())

# Rutas de citas (requieren token)
@app.route('/api/appointments/<path:path>', methods=['POST', 'GET', 'PUT', 'DELETE'])
@token_required
def appointments_routes(path):
    return forward_request('appointments', f'/appointments/{path}', request.method, request.get_json())

# Rutas de barberos (públicas)
@app.route('/api/barbers', methods=['GET'])
def get_barbers():
    return forward_request('barbers', '/barbers', request.method)

@app.route('/api/barbers/<path:path>', methods=['GET'])
def get_barber_routes(path):
    if path.endswith('/schedule'):
        return forward_request('barbers', f'/barbers/{path}', request.method)
    return jsonify({'error': 'Ruta no encontrada'}), 404

# Rutas de barberos (protegidas)
@app.route('/api/barbers/<path:path>', methods=['POST', 'PUT', 'DELETE'])
@token_required
def barbers_protected_routes(path):
    return forward_request('barbers', f'/barbers/{path}', request.method, request.get_json())

# Rutas de productos (requieren token)
@app.route('/api/products/<path:path>', methods=['POST', 'GET', 'PUT', 'DELETE'])
@token_required
def products_routes(path):
    return forward_request('products', f'/products/{path}', request.method, request.get_json())

# Ruta de health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Rutas del frontend
@app.route('/')
def index():
    try:
        # Obtener los barberos del servicio de barberos
        response = requests.get(f"{SERVICES['barbers']}/barbers")
        if response.ok:
            barberos = response.json().get('data', [])
        else:
            barberos = []
            print(f"Error obteniendo barberos: {response.status_code}")
    except Exception as e:
        print(f"Error conectando con el servicio de barberos: {e}")
        barberos = []
    
    return render_template('index.html', barberos=barberos)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/appointments')
def appointments():
    return render_template('appointments.html')

# Servir archivos estáticos
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 