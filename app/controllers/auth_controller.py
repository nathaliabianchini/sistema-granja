
from flask import request, jsonify
from app.controllers.usuario_controller import find_by_email_or_cpf
from app.models import Usuario, db, Sexo, TipoUsuario
from sqlalchemy import or_
from datetime import date
from typing import Union
import bcrypt

def register(nome: str, email: str, cpf: str, senha: str, tipo_usuario: Union[str, TipoUsuario], 
           id_granja: str, sexo: Union[str, Sexo], data_nascimento: date, endereco: str, 
           data_admissao: date, carteira_trabalho: str, telefone: str, matricula: str):
    try:
        existing_user = find_by_email_or_cpf(email, cpf)
        if existing_user:
            return jsonify({'message': 'The provided email or CPF already belongs to another user.'}), 400
        hashedPassword = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')
        
        if isinstance(sexo, str):
            sexo = Sexo(sexo)
        if isinstance(tipo_usuario, str):
            tipo_usuario = TipoUsuario(tipo_usuario)
        
        new_user = Usuario(**{  
            'nome': nome,
            'email': email,
            'cpf': cpf,
            'senha': hashedPassword,
            'tipo_usuario': tipo_usuario,
            'id_granja': id_granja,
            'sexo': sexo,
            'data_nascimento': data_nascimento,
            'endereco': endereco,
            'data_admissao': data_admissao,
            'carteira_trabalho': carteira_trabalho,
            'telefone': telefone,
            'matricula': matricula
        })

        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User succesfully registered!'}), 201
        
    except Exception as error:
        print(str(error))  
        return jsonify({'error': f'Internal error: {str(error)}'}), 500
    
def sign_in(email: str, senha: str):
    try:
        user = Usuario.query.filter_by(email=email).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        if not user.is_ativo:
            return jsonify({'message': 'This user has been deactivated and cannot be used.'}), 403
        
        if not user or not bcrypt.checkpw(senha.encode('utf-8'), user.senha.encode('utf-8')):
            return jsonify({'message': 'Incorrect email or password'}), 401

        return jsonify({'message': 'Login successful!'}), 200

    except Exception as error:
        print(str(error))  
        return jsonify({'error': f'Internal server error'}), 500

def register_grange():
    try:
        data = request.get_json()
        
        if 'cnpj_granja' not in data:
            return jsonify({'error': 'Grange CNPJ is required'}), 400

        from app.models import Granja, db
        
        existing_granja = Granja.query.filter_by(cnpj_granja=data['cnpj_granja']).first()
        if existing_granja:
            return jsonify({'error': 'This CNPJ has already been registered'}), 400

        new_granja = Granja(**{'cnpj_granja': data['cnpj_granja']})

        db.session.add(new_granja)
        db.session.commit()
        
        return jsonify({
            'message': 'Grange registered successfully!'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500