from functools import wraps
from flask import request, jsonify, g
from app.models import Usuarios, TipoUsuarios
from app.config import verify_jwt_token

def require_auth(allowed_roles=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Authorization token required'}), 401
            
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)
            
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            try:
                user = Usuarios.query.get(payload['user_id'])
                if not user or not user.is_ativo:
                    return jsonify({'error': 'User not found or deactivated'}), 401
                
                if allowed_roles and user.tipo_usuario not in allowed_roles:
                    return jsonify({'error': 'Access denied'}), 403
                
                g.current_user = user
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({'error': 'Authentication error'}), 500
            
        return decorated_function
    return decorator

def admin_required(f):
    return require_auth([TipoUsuarios.ADMIN])(f)

def production_access(f):
    return require_auth([TipoUsuarios.ADMIN, TipoUsuarios.OPERADOR, TipoUsuarios.GERENTE])(f)

def manager_access(f):
    return require_auth([TipoUsuarios.ADMIN, TipoUsuarios.GERENTE])(f)

def read_only_access(f):
    return require_auth([TipoUsuarios.ADMIN, TipoUsuarios.GERENTE, TipoUsuarios.OPERADOR])(f)