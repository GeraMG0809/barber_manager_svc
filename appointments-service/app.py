from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
jwt = JWTManager(app)

@app.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    # Implementación pendiente
    return jsonify({"message": "Get appointments endpoint"}), 200

@app.route('/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    # Implementación pendiente
    return jsonify({"message": "Create appointment endpoint"}), 200

@app.route('/appointments/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def update_appointment(appointment_id):
    # Implementación pendiente
    return jsonify({"message": "Update appointment endpoint"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002) 