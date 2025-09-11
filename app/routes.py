from flask import Blueprint, request, jsonify
from app.controllers.auth_controller import register, sign_in
from app.controllers.usuario_controller import get_user
from datetime import datetime

bp = Blueprint('routes', __name__)

@bp.route('/api/auth/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        
        required_fields = ['nome', 'email', 'cpf', 'senha', 'tipo_usuario', 'id_granja',
                          'data_nascimento', 'endereco', 'data_admissao', 
                          'carteira_trabalho', 'telefone', 'matricula']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        data_nascimento = datetime.strptime(data['data_nascimento'], '%Y-%m-%d').date()
        data_admissao = datetime.strptime(data['data_admissao'], '%Y-%m-%d').date()
        
        return register(
            nome=data['nome'],
            email=data['email'],
            cpf=data['cpf'],
            senha=data['senha'],
            tipo_usuario=data['tipo_usuario'],
            id_granja=data['id_granja'],
            sexo=data['sexo'],
            data_nascimento=data_nascimento,
            endereco=data['endereco'],
            data_admissao=data_admissao,
            carteira_trabalho=data['carteira_trabalho'],
            telefone=data['telefone'],
            matricula=data['matricula']
        )
        
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@bp.route('/api/auth/login', methods=['POST'])
def login_user():
    try:
        data = request.get_json()
        
        if 'email' not in data or 'senha' not in data:
            return jsonify({'error': 'Email and password are required'}), 400

        return sign_in(data['email'], data['senha'])
        
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@bp.route('/api/users', methods=['GET'])
def list_users():
    from app.controllers.usuario_controller import get_users
    return get_users()

@bp.route('/api/users/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    return get_user(user_id)

@bp.route('/api/users/<user_id>/deactivate', methods=['POST'])
def deactivate_user(user_id):
    from app.controllers.usuario_controller import deactivate_user
    return deactivate_user(user_id)

@bp.route('/api/register-grange', methods=['POST'])
def register_grange():
    from app.controllers.auth_controller import register_grange
    return register_grange()


