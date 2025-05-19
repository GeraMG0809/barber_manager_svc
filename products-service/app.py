from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
jwt = JWTManager(app)

@app.route('/products', methods=['GET'])
def get_products():
    # Implementación pendiente
    return jsonify({"message": "Get products endpoint"}), 200

@app.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    # Implementación pendiente
    return jsonify({"message": "Create product endpoint"}), 200

@app.route('/sales', methods=['POST'])
@jwt_required()
def create_sale():
    # Implementación pendiente
    return jsonify({"message": "Create sale endpoint"}), 200

@app.route('/reports/sales', methods=['GET'])
@jwt_required()
def get_sales_report():
    # Implementación pendiente
    return jsonify({"message": "Get sales report endpoint"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004) 