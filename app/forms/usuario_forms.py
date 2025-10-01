from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.models.database import Usuario

class UsuarioForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired(), Length(min=3, max=100)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)])
    sexo = SelectField('Sexo', choices=[
        ('Feminino', 'Feminino'),
        ('Masculino', 'Masculino')
    ])
    data_nascimento = DateField('Data de Nascimento', validators=[DataRequired()])
    endereco = StringField('Endereço', validators=[DataRequired(), Length(max=150)])
    data_admissao = DateField('Data de Admissão', validators=[DataRequired()])
    carteira_trabalho = StringField('Carteira de Trabalho', validators=[DataRequired(), Length(max=20)])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    tipo_usuario = SelectField('Tipo de Usuário', choices=[
        ('Operador de Produção', 'Operador'),
        ('Gerente', 'Gerente'),
        ('ADMIN', 'Administrador')
    ])
    matricula = StringField('Matrícula', validators=[DataRequired(), Length(max=10)])

    def validate_cpf(self, field):
        if Usuario.select().where(Usuario.cpf == field.data).exists():
            raise ValidationError('CPF já cadastrado')

    def validate_email(self, field):
        if Usuario.select().where(Usuario.email == field.data).exists():
            raise ValidationError('Email já cadastrado')

    def validate_matricula(self, field):
        if Usuario.select().where(Usuario.matricula == field.data).exists():
            raise ValidationError('Matrícula já cadastrada')