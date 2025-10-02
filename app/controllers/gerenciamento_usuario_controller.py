from flask import request, jsonify, g
from app.models import Usuarios, UserActivityLog, db, Sexo, TipoUsuarios
from app.utils import validate_password, log_user_activity, validate_cpf
import bcrypt

def update_user_data(user_id: str):
    try:
        current_user = g.get('current_user')
        user = Usuarios.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        updatable_fields = ['nome', 'sexo', 'endereco', 'tipo_usuario', 'telefone']
        
        for field in updatable_fields:
            if field in data:
                old_value = getattr(user, field)
                new_value = data[field]
                
                if field == 'sexo' and isinstance(new_value, str):
                    new_value = Sexo(new_value)
                elif field == 'tipo_usuario' and isinstance(new_value, str):
                    new_value = TipoUsuarios(new_value)
                
                if old_value != new_value:
                    setattr(user, field, new_value)
                    log_user_activity(
                        current_user.id_usuario if current_user else user_id,
                        'USER_UPDATED',
                        f'Campo {field} alterado de {old_value} para {new_value} no usuário {user.nome}'
                    )
        
        db.session.commit()
        return jsonify({'message': 'User data updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

def get_user_by_cpf():
    try:
        data = request.get_json()
        cpf = data.get('cpf')
        
        if not cpf:
            return jsonify({'error': 'CPF is required'}), 400
        
        user = Usuarios.query.filter_by(cpf=cpf).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        current_user = g.get('current_user')
        log_user_activity(
            current_user.id_usuario if current_user else None,
            'USER_CONSULTED',
            f'Consulta realizada para usuário CPF: {cpf}'
        )
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

def change_password():
    try:
        current_user = g.get('current_user')
        data = request.get_json()
        
        current_password = data.get('senha_atual')
        new_password = data.get('nova_senha')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400

        if not bcrypt.checkpw(current_password.encode('utf-8'), current_user.senha.encode('utf-8')):
            log_user_activity(current_user.id_usuario, 'PASSWORD_CHANGE_FAILED', 'Incorrect current password')
            return jsonify({'error': 'Incorrect current password'}), 401

        is_valid, password_msg = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': password_msg}), 400
        
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')
        current_user.senha = hashed_new_password
        
        db.session.commit()

        log_user_activity(current_user.id_usuario, 'PASSWORD_CHANGED', 'Password changed successfully')

        return jsonify({'message': 'Password changed successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

from typing import Optional

def get_user_activity_logs(user_id: Optional[str] = None):
    try:
        if user_id:
            logs = UserActivityLog.query.filter_by(user_id=user_id).order_by(UserActivityLog.timestamp.desc()).limit(50).all()
        else:
            logs = UserActivityLog.query.order_by(UserActivityLog.timestamp.desc()).limit(100).all()
        
        current_user = g.get('current_user')
        log_user_activity(
            current_user.id_usuario if current_user else None,
            'LOGS_ACCESSED',
            f'Logs de atividade acessados para usuário: {user_id or "todos"}'
        )
        
        return jsonify([{
            'id': log.id,
            'user_id': log.user_id,
            'user_name': log.user.nome if log.user else 'Sistema',
            'action': log.action,
            'details': log.details,
            'timestamp': log.timestamp.isoformat(),
            'ip_address': log.ip_address
        } for log in logs]), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

def get_all_users_for_admin():
    try:
        users = Usuarios.query.all()
        
        current_user = g.get('current_user')
        log_user_activity(
            current_user.id_usuario if current_user else None,
            'USERS_LISTED',
            'Lista de todos os usuários acessada'
        )
        
        return jsonify([user.to_dict() for user in users]), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

def forgot_password():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = Usuarios.query.filter_by(email=email).first()
        if not user:
            return jsonify({'message': 'If the email exists, instructions have been sent'}), 200

        new_password = "Temp123"
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')
        user.senha = hashed_password
        
        db.session.commit()

        log_user_activity(user.id_usuario, 'PASSWORD_RESET', 'Password reset due to forgetfulness')

        return jsonify({
            'message': 'Temporary password generated',
            'temporary_password': new_password,
            'note': 'Change your password after the first login'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500