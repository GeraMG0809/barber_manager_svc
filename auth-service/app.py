from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import timedelta
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)

def get_db_connection():
    try:
        logger.info("Intentando conectar a la base de datos...")
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'mysql-auth'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'secret'),
            database=os.getenv('DB_NAME', 'auth_db')
        )
        logger.info("Conexión exitosa a la base de datos")
        return connection
    except Error as e:
        logger.error(f"Error conectando a MySQL: {e}")
        return None

def init_db():
    logger.info("Inicializando la base de datos...")
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    phone VARCHAR(20),
                    role ENUM('user', 'admin', 'barber') DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            logger.info("Tabla users creada o verificada exitosamente")
        except Error as e:
            logger.error(f"Error creando tabla: {e}")
        finally:
            cursor.close()
            conn.close()
    else:
        logger.error("No se pudo inicializar la base de datos")

@app.route('/auth/register', methods=['POST'])
def register():
    logger.info("Recibida petición de registro")
    data = request.get_json()
    logger.debug(f"Datos recibidos: {data}")
    
    if not all(k in data for k in ('name', 'email', 'password', 'phone')):
        logger.warning("Faltan campos requeridos en la petición")
        return jsonify({"error": "Faltan campos requeridos"}), 400

    conn = get_db_connection()
    if not conn:
        logger.error("No se pudo conectar a la base de datos")
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor()
        
        # Verificar si el email ya existe
        cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            logger.warning(f"Email ya registrado: {data['email']}")
            return jsonify({"error": "El email ya está registrado"}), 400

        # Encriptar la contraseña
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        # Insertar nuevo usuario
        cursor.execute("""
            INSERT INTO users (name, email, password, phone, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data['name'],
            data['email'],
            hashed_password.decode('utf-8'),
            data['phone'],
            data.get('role', 'user')
        ))
        
        conn.commit()
        user_id = cursor.lastrowid
        logger.info(f"Usuario registrado exitosamente con ID: {user_id}")
        
        # Crear token de acceso
        access_token = create_access_token(
            identity={'id': user_id, 'email': data['email'], 'role': data.get('role', 'user')}
        )
        
        return jsonify({
            "message": "Usuario registrado exitosamente",
            "access_token": access_token,
            "user": {
                "id": user_id,
                "name": data['name'],
                "email": data['email'],
                "phone": data['phone'],
                "role": data.get('role', 'user')
            }
        }), 201

    except Error as e:
        logger.error(f"Error al registrar usuario: {e}")
        return jsonify({"error": "Error al registrar usuario"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/auth/login', methods=['POST'])
def login():
    logger.info("Recibida petición de login")
    data = request.get_json()
    logger.debug(f"Datos recibidos: {data}")
    
    if not all(k in data for k in ('email', 'password')):
        logger.warning("Faltan campos requeridos en la petición de login")
        return jsonify({"error": "Email y contraseña son requeridos"}), 400

    conn = get_db_connection()
    if not conn:
        logger.error("No se pudo conectar a la base de datos")
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (data['email'],))
        user = cursor.fetchone()

        if not user:
            logger.warning(f"Usuario no encontrado: {data['email']}")
            return jsonify({"error": "Usuario no encontrado"}), 404

        if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password'].encode('utf-8')):
            logger.warning(f"Contraseña incorrecta para usuario: {data['email']}")
            return jsonify({"error": "Contraseña incorrecta"}), 401

        access_token = create_access_token(
            identity={'id': user['id'], 'email': user['email'], 'role': user['role']}
        )
        logger.info(f"Login exitoso para usuario: {data['email']}")

        return jsonify({
            "message": "Login exitoso",
            "access_token": access_token,
            "user": {
                "id": user['id'],
                "name": user['name'],
                "email": user['email'],
                "phone": user['phone'],
                "role": user['role']
            }
        }), 200

    except Error as e:
        logger.error(f"Error al iniciar sesión: {e}")
        return jsonify({"error": "Error al iniciar sesión"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user = get_jwt_identity()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, phone, role FROM users WHERE id = %s", (current_user['id'],))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        return jsonify(user), 200

    except Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error al obtener perfil"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No se proporcionaron datos para actualizar"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor()
        
        # Construir la consulta de actualización dinámicamente
        update_fields = []
        values = []
        
        if 'name' in data:
            update_fields.append("name = %s")
            values.append(data['name'])
        if 'phone' in data:
            update_fields.append("phone = %s")
            values.append(data['phone'])
        if 'password' in data:
            hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
            update_fields.append("password = %s")
            values.append(hashed_password.decode('utf-8'))

        if not update_fields:
            return jsonify({"error": "No hay campos válidos para actualizar"}), 400

        values.append(current_user['id'])
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
        
        cursor.execute(query, values)
        conn.commit()

        return jsonify({"message": "Perfil actualizado exitosamente"}), 200

    except Error as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error al actualizar perfil"}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    logger.info("Iniciando servicio de autenticación...")
    init_db()
    logger.info("Servicio de autenticación iniciado en puerto 5001")
    app.run(host='0.0.0.0', port=5001, debug=True) 