from flask import Blueprint, jsonify

bp = Blueprint('routes', __name__)

@bp.route('/api/home', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to Projeto Granja!"})

@bp.route('/api/users', methods=['GET'])
def users():
    # Placeholder for user retrieval logic
    return jsonify({"users": []})

@bp.route('/api/about', methods=['GET'])
def about():
    return jsonify({"message": "About Projeto Granja"})