from flask import request, jsonify
from app.models import Usuarios, db
from sqlalchemy import or_

def find_by_email_or_cpf(email: str, cpf: str):
    return Usuarios.query.filter(
        or_(Usuarios.email == email, Usuarios.cpf == cpf)
    ).first()

def get_user(user_id):
    user = Usuarios.query.get(user_id)
    if user:
        return jsonify(user.to_dict())
    return jsonify({'message': 'User not found'}), 404
    
def update_user(user_id, **kwargs):
    user = Usuarios.query.get(user_id)
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
    users = Usuarios.query.all()
    return jsonify([user.to_dict() for user in users])

def deactivate_user(user_id):
    user = Usuarios.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    if user.is_ativo == False:
        return jsonify({'message': 'User already deactivated'}), 400

    user.is_ativo = False
    try:
        db.session.commit()
        return jsonify({'message': 'User deactivated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error deactivating user', 'error': str(e)}), 500
    
def reactivate_user(user_id):
    user = Usuarios.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    if user.is_ativo == True:
        return jsonify({'message': 'User already active'}), 400
    
    user.is_ativo = True
    try:
        db.session.commit()
        return jsonify({'message': 'User reactivated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error reactivating user', 'error': str(e)}), 500

