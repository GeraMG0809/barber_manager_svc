from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import requests

load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
jwt = JWTManager(app)

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# URLs de los servicios
BARBER_SERVICE_URL = os.getenv('BARBER_SERVICE_URL', 'http://barbers-service:5003')
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth-service:5001')

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'mysql-appointments'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'secret'),
            database=os.getenv('DB_NAME', 'appointments_db')
        )
        return connection
    except Error as e:
        logger.error(f"Error conectando a MySQL: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    barber_id INT NOT NULL,
                    service_id INT NOT NULL,
                    appointment_date DATETIME NOT NULL,
                    status ENUM('pending', 'confirmed', 'cancelled', 'completed') DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        except Error as e:
            logger.error(f"Error creando tabla: {e}")
        finally:
            cursor.close()
            conn.close()

def verify_user_exists(user_id):
    try:
        response = requests.get(f"{AUTH_SERVICE_URL}/auth/users/{user_id}")
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def verify_barber_exists(barber_id):
    try:
        response = requests.get(f"{BARBER_SERVICE_URL}/barbers/{barber_id}")
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def verify_service_exists(service_id):
    try:
        response = requests.get(f"{BARBER_SERVICE_URL}/services/{service_id}")
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

@app.route('/appointments/create', methods=['POST'])
@jwt_required()
def create_appointment():
    current_user = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ['barber_id', 'service_id', 'appointment_date']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    # Verificar que el usuario existe
    if not verify_user_exists(current_user['id']):
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Verificar que el barbero existe
    if not verify_barber_exists(data['barber_id']):
        return jsonify({"error": "Barbero no encontrado"}), 404

    # Verificar que el servicio existe
    if not verify_service_exists(data['service_id']):
        return jsonify({"error": "Servicio no encontrado"}), 404

    try:
        appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments (user_id, barber_id, service_id, appointment_date)
            VALUES (%s, %s, %s, %s)
        """, (
            current_user['id'],
            data['barber_id'],
            data['service_id'],
            appointment_date
        ))
        conn.commit()
        appointment_id = cursor.lastrowid

        return jsonify({
            "message": "Cita creada exitosamente",
            "appointment_id": appointment_id
        }), 201

    except Error as e:
        logger.error(f"Error creando cita: {e}")
        return jsonify({"error": "Error al crear la cita"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/appointments/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_appointments(user_id):
    current_user = get_jwt_identity()
    
    # Verificar que el usuario solo pueda ver sus propias citas
    if current_user['id'] != user_id and current_user['role'] != 'admin':
        return jsonify({"error": "No autorizado"}), 403

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, 
                   (SELECT name FROM barbers WHERE id = a.barber_id) as barber_name,
                   (SELECT name FROM services WHERE id = a.service_id) as service_name
            FROM appointments a
            WHERE a.user_id = %s
            ORDER BY a.appointment_date DESC
        """, (user_id,))
        
        appointments = cursor.fetchall()
        return jsonify(appointments), 200

    except Error as e:
        logger.error(f"Error obteniendo citas: {e}")
        return jsonify({"error": "Error al obtener las citas"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/appointments/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def update_appointment(appointment_id):
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({"error": "Estado no proporcionado"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor()
        # Verificar que el usuario sea el dueño de la cita o un admin
        cursor.execute("SELECT user_id FROM appointments WHERE id = %s", (appointment_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "Cita no encontrada"}), 404
            
        if result[0] != current_user['id'] and current_user['role'] != 'admin':
            return jsonify({"error": "No autorizado"}), 403

        cursor.execute("""
            UPDATE appointments 
            SET status = %s
            WHERE id = %s
        """, (data['status'], appointment_id))
        
        conn.commit()
        return jsonify({"message": "Cita actualizada exitosamente"}), 200

    except Error as e:
        logger.error(f"Error actualizando cita: {e}")
        return jsonify({"error": "Error al actualizar la cita"}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002) 