from flask import request, jsonify
# from app.models import Usuario, db
from models import Usuario, db
from sqlalchemy import or_

def find_by_email_or_cpf(email: str, cpf: str):
    return Usuario.query.filter(
        or_(Usuario.email == email, Usuario.cpf == cpf)
    ).first()

def create(nome: str, email : str, cpf: str, senha: str, tipo_usuario: str, id_granja: str):
    new_user = Usuario(
        nome=nome,
        email=email,
        cpf=cpf,
        senha=senha,
        tipo_usuario=tipo_usuario,
        id_granja=id_granja,
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return new_user
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error creating user', 'error': str(e)}), 500
    
def get_users():
    users = Usuario.query.all()
    return jsonify([user.to_dict() for user in users])

def get_user(user_id):
    user = Usuario.query.get(user_id)
    if user:
        return jsonify(user.to_dict())
    return jsonify({'message': 'User not found'}), 404