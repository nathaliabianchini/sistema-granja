from flask import request, jsonify
from app.models import Usuario, db
from sqlalchemy import or_

def find_by_email_or_cpf(email: str, cpf: str):
    return Usuario.query.filter(
        or_(Usuario.email == email, Usuario.cpf == cpf)
    ).first()

def get_user(user_id):
    user = Usuario.query.get(user_id)
    if user:
        return jsonify(user.to_dict())
    return jsonify({'message': 'User not found'}), 404
    
def update_user(user_id, **kwargs):
    user = Usuario.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
        
    try:
        db.session.commit()
        return jsonify(user.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error updating user', 'error': str(e)}), 500

def get_users():
    users = Usuario.query.all()
    return jsonify([user.to_dict() for user in users])

def deactivate_user(user_id):
    user = Usuario.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.is_ativo = False
    try:
        db.session.commit()
        return jsonify({'message': 'User deactivated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error deactivating user', 'error': str(e)}), 500

