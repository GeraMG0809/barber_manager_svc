from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
jwt = JWTManager(app)

@app.route('/barbers', methods=['GET'])
def get_barbers():
    # Implementación pendiente
    return jsonify({"message": "Get barbers endpoint"}), 200

@app.route('/barbers', methods=['POST'])
@jwt_required()
def create_barber():
    # Implementación pendiente
    return jsonify({"message": "Create barber endpoint"}), 200

@app.route('/services', methods=['GET'])
def get_services():
    # Implementación pendiente
    return jsonify({"message": "Get services endpoint"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003) 