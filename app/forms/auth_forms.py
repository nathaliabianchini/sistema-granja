from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from datetime import date
import re

# Validador customizado para username
def validate_username(form, field):
    username = field.data
    # Verificar se contém apenas letras minúsculas
    if not re.match("^[a-z]+$", username):
        raise ValidationError('Usuário deve conter apenas letras minúsculas, sem números, espaços ou caracteres especiais.')

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[
        DataRequired(message='Usuário é obrigatório'),
        Length(min=3, max=20, message='Usuário deve ter entre 3 e 20 caracteres'),
        validate_username
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=6, message='Senha deve ter pelo menos 6 caracteres')
    ])

class RegisterForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ])
    
    username = StringField('Nome de Usuário', validators=[
        DataRequired(message='Nome de usuário é obrigatório'),
        Length(min=3, max=20, message='Nome de usuário deve ter entre 3 e 20 caracteres'),
        validate_username
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    
    cpf = StringField('CPF', validators=[
        DataRequired(message='CPF é obrigatório'),
        Length(min=11, max=14, message='CPF inválido')
    ])
    
    senha = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=6, message='Senha deve ter pelo menos 6 caracteres')
    ])
    
    confirma_senha = PasswordField('Confirmar Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('senha', message='Senhas não conferem')
    ])
    
    tipo_usuario = SelectField('Tipo de Usuário', 
        choices=[
            ('admin', 'Administrador'),
            ('funcionario', 'Funcionário'),
            ('veterinario', 'Veterinário')
        ],
        validators=[DataRequired(message='Tipo de usuário é obrigatório')]
    )
    
    id_granja = StringField('ID da Granja', validators=[
        DataRequired(message='ID da granja é obrigatório')
    ])
    
    sexo = SelectField('Sexo',
        choices=[('M', 'Masculino'), ('F', 'Feminino')],
        validators=[DataRequired(message='Sexo é obrigatório')]
    )
    
    data_nascimento = DateField('Data de Nascimento', 
        default=date.today,
        validators=[DataRequired(message='Data de nascimento é obrigatória')]
    )
    
    endereco = TextAreaField('Endereço', validators=[
        DataRequired(message='Endereço é obrigatório')
    ])
    
    data_admissao = DateField('Data de Admissão',
        default=date.today,
        validators=[DataRequired(message='Data de admissão é obrigatória')]
    )
    
    carteira_trabalho = StringField('Carteira de Trabalho', validators=[
        DataRequired(message='Carteira de trabalho é obrigatória')
    ])
    
    telefone = StringField('Telefone', validators=[
        DataRequired(message='Telefone é obrigatório')
    ])