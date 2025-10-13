
from flask import request, jsonify
from app.controllers.usuario_controller import find_by_email_or_cpf
from app.models import Usuarios, Granjas, db, Sexo, TipoUsuario
from app.utils import validate_password, generate_matricula, validate_cpf, log_user_activity
from sqlalchemy import or_
from datetime import date
from typing import Union
import bcrypt

def register(nome: str, email: str, cpf: str, senha: str, tipo_usuario: Union[str, TipoUsuario], 
           id_granja: str, sexo: Union[str, Sexo], data_nascimento: date, endereco: str, 
           data_admissao: date, carteira_trabalho: str, telefone: str, matricula: str = ""):
    try:
        existing_user = find_by_email_or_cpf(email, cpf)
        if existing_user:
            return jsonify({'message': 'The provided email or CPF already belongs to another user.'}), 400
        

        is_valid, password_msg = validate_password(senha)
        if not is_valid:
            return jsonify({'error': password_msg}), 400
            
        hashedPassword = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')
        
        if isinstance(sexo, str):
            sexo = Sexo(sexo)
        if isinstance(tipo_usuario, str):
            tipo_usuario = TipoUsuario(tipo_usuario)
        
        if not matricula:
            matricula = generate_matricula()
        
        new_user = Usuarios(**{  
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
        
        log_user_activity(new_user.id_usuario, 'USER_CREATED', f'Novo usuário criado: {nome} ({email})')
        
        return jsonify({'message': 'User succesfully registered!', 'matricula': matricula}), 201
        
    except Exception as error:
        return jsonify({'error': f'Internal error: {str(error)}'}), 500
    
def sign_in(email: str, senha: str):
    try:
        user = Usuarios.query.filter_by(email=email).first()
        if not user:
            log_user_activity(None, 'LOGIN_FAILED', f'Tentativa de login com email inexistente: {email}')
            return jsonify({'message': 'User not found'}), 404

        if not user.is_ativo:
            log_user_activity(user.id_usuario, 'LOGIN_DENIED', 'Tentativa de login com usuário desativado')
            return jsonify({'message': 'This user has been deactivated and cannot be used.'}), 403
        
        if not user or not bcrypt.checkpw(senha.encode('utf-8'), user.senha.encode('utf-8')):
            log_user_activity(user.id_usuario, 'LOGIN_FAILED', 'Senha incorreta')
            return jsonify({'message': 'Incorrect email or password'}), 401

        from app.config import generate_jwt_token
        token = generate_jwt_token(
            user_id=user.id_usuario,
            user_tipo=user.tipo_usuario.value,
            user_nome=user.nome
        )
        
        log_user_activity(user.id_usuario, 'LOGIN_SUCCESS', f'Login realizado com sucesso')

        return jsonify({
            'message': 'Login successful!',
            'token': token,
        }), 200

    except Exception as error:
        return jsonify({'error': f'Internal server error'}), 500

def register_grange():
    try:
        data = request.get_json()
        
        if 'cnpj_granja' not in data:
            return jsonify({'error': 'Grange CNPJ is required'}), 400
            
        if 'nome_granja' not in data or not data['nome_granja'].strip():
            return jsonify({'error': 'Grange name is required'}), 400

        from app.models import Granjas, db
        
        existing_granja = Granjas.query.filter_by(cnpj_granja=data['cnpj_granja']).first()
        if existing_granja:
            return jsonify({'error': 'This CNPJ has already been registered'}), 400

        new_granja = Granjas(**{
            'cnpj_granja': data['cnpj_granja'],
            'nome_granja': data['nome_granja'].strip()
        })

        db.session.add(new_granja)
        db.session.commit()
        
        return jsonify({
            'message': 'Grange registered successfully!',
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

def create_default_admin():
    try:
        admin_exists = Usuarios.query.filter_by(email='ADMIN').first()
        if admin_exists:
            return True
        
        granja_exists = Granjas.query.first()
        if not granja_exists:
            default_granja = Granjas(**{
                'cnpj_granja': '00000000000000',
                'nome_granja': 'GRANJA PADRÃO'
            })
            db.session.add(default_granja)
            db.session.commit()
            granja_id = default_granja.id_granja
        else:
            granja_id = granja_exists.id_granja
        
        hashedPassword = bcrypt.hashpw('ADMIN'.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')
        
        admin_user = Usuarios(**{
            'nome': 'Administrator',
            'email': 'ADMIN',
            'cpf': '00000000000',
            'senha': hashedPassword,
            'tipo_usuario': TipoUsuario.ADMIN,
            'id_granja': granja_id,
            'sexo': Sexo.MASCULINO,
            'data_nascimento': date(1990, 1, 1),
            'endereco': 'Sistema',
            'data_admissao': date.today(),
            'carteira_trabalho': 'ADMIN000',
            'telefone': '00000000000',
            'matricula': 'ADMIN001'
        })
        
        db.session.add(admin_user)
        db.session.commit()
        
        log_user_activity(admin_user.id_usuario, 'ADMIN_CREATED', 'Usuário ADMIN padrão criado')
        
        return True
        
    except Exception as e:
        db.session.rollback()
        return False