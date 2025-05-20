from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging
import time

load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
jwt = JWTManager(app)

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'mysql-barbers'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'secret'),
            database=os.getenv('DB_NAME', 'barbers_db')
        )
        return connection
    except Error as e:
        logger.error(f"Error conectando a MySQL: {e}")
        return None

def init_db():
    max_retries = 5
    retry_delay = 5  # segundos
    
    for attempt in range(max_retries):
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Tabla de barberos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS barbers (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        phone VARCHAR(20),
                        status ENUM('active', 'inactive') DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabla de servicios
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS services (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        duration INT NOT NULL, -- duración en minutos
                        price DECIMAL(10,2) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabla de horarios de barberos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS barber_schedules (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        barber_id INT NOT NULL,
                        day_of_week INT NOT NULL, -- 0 = Lunes, 6 = Domingo
                        start_time TIME NOT NULL,
                        end_time TIME NOT NULL,
                        FOREIGN KEY (barber_id) REFERENCES barbers(id)
                    )
                ''')
                
                # Insertar datos de ejemplo si las tablas están vacías
                cursor.execute("SELECT COUNT(*) FROM barbers")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO barbers (name, email, phone) VALUES 
                        ('Juan Pérez', 'juan@barber.com', '1234567890'),
                        ('María García', 'maria@barber.com', '0987654321')
                    """)
                
                cursor.execute("SELECT COUNT(*) FROM services")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO services (name, description, duration, price) VALUES 
                        ('Corte de cabello', 'Corte básico de cabello', 30, 150.00),
                        ('Barba', 'Arreglo de barba', 20, 100.00),
                        ('Corte + Barba', 'Corte de cabello y arreglo de barba', 45, 200.00)
                    """)
                
                conn.commit()
                logger.info("Base de datos inicializada correctamente")
                return True
            except Error as e:
                logger.error(f"Error creando tablas: {e}")
            finally:
                cursor.close()
                conn.close()
        else:
            logger.warning(f"Intento {attempt + 1} de {max_retries} fallido. Reintentando en {retry_delay} segundos...")
            time.sleep(retry_delay)
    
    logger.error("No se pudo inicializar la base de datos después de varios intentos")
    return False

# Inicializar la base de datos al arrancar la aplicación
init_db()

@app.route('/barbers', methods=['GET'])
def get_barbers():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM barbers WHERE status = 'active'")
        barbers = cursor.fetchall()
        return jsonify(barbers), 200
    except Error as e:
        logger.error(f"Error obteniendo barberos: {e}")
        return jsonify({"error": "Error al obtener barberos"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/barbers', methods=['POST'])
def create_barber():
    data = request.get_json()
    
    if not all(k in data for k in ('name', 'email', 'phone')):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor()
        
        # Verificar si el email ya existe
        cursor.execute("SELECT id FROM barbers WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            return jsonify({"error": "El email ya está registrado"}), 400

        # Insertar nuevo barbero
        cursor.execute("""
            INSERT INTO barbers (name, email, phone)
            VALUES (%s, %s, %s)
        """, (
            data['name'],
            data['email'],
            data['phone']
        ))
        
        conn.commit()
        barber_id = cursor.lastrowid
        
        return jsonify({
            "message": "Barbero registrado exitosamente",
            "barber_id": barber_id
        }), 201

    except Error as e:
        logger.error(f"Error al registrar barbero: {e}")
        return jsonify({"error": "Error al registrar barbero"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/barbers/<int:barber_id>/schedule', methods=['GET'])
@jwt_required()
def get_barber_schedule(barber_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM barber_schedules 
            WHERE barber_id = %s 
            ORDER BY day_of_week, start_time
        """, (barber_id,))
        schedule = cursor.fetchall()
        return jsonify(schedule), 200
    except Error as e:
        logger.error(f"Error obteniendo horario: {e}")
        return jsonify({"error": "Error al obtener horario"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/services', methods=['GET'])
def get_services():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM services")
        services = cursor.fetchall()
        return jsonify(services), 200
    except Error as e:
        logger.error(f"Error obteniendo servicios: {e}")
        return jsonify({"error": "Error al obtener servicios"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/barbers/<int:barber_id>/availability', methods=['GET'])
@jwt_required()
def check_availability(barber_id):
    date = request.args.get('date')
    if not date:
        return jsonify({"error": "Fecha no proporcionada"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        # Obtener el horario del barbero para ese día
        cursor.execute("""
            SELECT * FROM barber_schedules 
            WHERE barber_id = %s AND day_of_week = WEEKDAY(%s)
        """, (barber_id, date))
        schedule = cursor.fetchone()

        if not schedule:
            return jsonify({"error": "El barbero no trabaja en ese día"}), 400

        # Obtener las citas existentes para ese día
        cursor.execute("""
            SELECT appointment_date 
            FROM appointments 
            WHERE barber_id = %s 
            AND DATE(appointment_date) = %s
            AND status != 'cancelled'
        """, (barber_id, date))
        appointments = cursor.fetchall()

        # Calcular slots disponibles
        # Implementar lógica de disponibilidad aquí
        # Por ahora retornamos un mensaje simple
        return jsonify({
            "message": "Disponibilidad calculada",
            "schedule": schedule,
            "appointments": appointments
        }), 200

    except Error as e:
        logger.error(f"Error verificando disponibilidad: {e}")
        return jsonify({"error": "Error al verificar disponibilidad"}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003) 