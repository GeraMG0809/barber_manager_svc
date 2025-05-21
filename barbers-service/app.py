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
                # Eliminar tablas existentes
                cursor.execute("DROP TABLE IF EXISTS barber_schedules")
                cursor.execute("DROP TABLE IF EXISTS barbers")
                
                # Tabla de barberos
                cursor.execute('''
                    CREATE TABLE barbers (
                        id_barbero INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                        nombre_barbero VARCHAR(25) NOT NULL,
                        telefono VARCHAR(12) NOT NULL,
                        imagenes VARCHAR(100) NOT NULL,
                        estado ENUM('ACTIVO', 'INACTIVO') NOT NULL DEFAULT 'ACTIVO'
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
                    CREATE TABLE barber_schedules (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        barber_id INT NOT NULL,
                        day_of_week INT NOT NULL, -- 0 = Lunes, 6 = Domingo
                        start_time TIME NOT NULL,
                        end_time TIME NOT NULL,
                        FOREIGN KEY (barber_id) REFERENCES barbers(id_barbero)
                    )
                ''')
                
                # Insertar datos de ejemplo
                cursor.execute("""
                    INSERT INTO barbers (nombre_barbero, telefono, imagenes) VALUES 
                    ('Juan Perez', '1234567890', 'team-1.png'),
                    ('Mario Gomez', '0987654321', 'team-2.png'),
                    ('Carlos Rodriguez', '5555555555', 'team-3.png')
                """)
                
                # Obtener los IDs de los barberos
                cursor.execute("SELECT id_barbero FROM barbers")
                barber_ids = [row[0] for row in cursor.fetchall()]
                
                # Insertar horarios para cada barbero
                for barber_id in barber_ids:
                    # Horario de lunes a viernes (0-4)
                    for day in range(5):
                        cursor.execute("""
                            INSERT INTO barber_schedules (barber_id, day_of_week, start_time, end_time)
                            VALUES (%s, %s, '09:00:00', '18:00:00')
                        """, (barber_id, day))
                    
                    # Horario de sábado (5)
                    cursor.execute("""
                        INSERT INTO barber_schedules (barber_id, day_of_week, start_time, end_time)
                        VALUES (%s, 5, '09:00:00', '14:00:00')
                    """, (barber_id,))
                
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
    logger.info("Recibida petición GET /barbers")
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        logger.info("Ejecutando consulta para obtener barberos")
        cursor.execute("""
            SELECT 
                id_barbero as id,
                nombre_barbero as nombre,
                telefono,
                imagenes,
                estado
            FROM barbers 
            WHERE estado = 'ACTIVO'
        """)
        barbers = cursor.fetchall()
        logger.info(f"Barberos encontrados: {len(barbers)}")
        
        for barber in barbers:
            logger.debug(f"Barbero procesado: {barber}")
            
        return jsonify({"data": barbers}), 200
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
        cursor.execute("SELECT id_barbero FROM barbers WHERE telefono = %s", (data['phone'],))
        if cursor.fetchone():
            return jsonify({"error": "El teléfono ya está registrado"}), 400

        # Insertar nuevo barbero
        cursor.execute("""
            INSERT INTO barbers (nombre_barbero, telefono, imagenes)
            VALUES (%s, %s, %s)
        """, (
            data['name'],
            data['phone'],
            data['imagen']
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
def get_barber_schedule(barber_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT day_of_week, start_time, end_time
            FROM barber_schedules
            WHERE barber_id = %s
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