from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, DateField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError, Optional
from app.models.database import CategoriaInsumo, UnidadeMedida
from datetime import date
from app.models.database import db, Insumo, MovimentacaoInsumo, Usuarios

class InsumoForm(FlaskForm):
    nome = StringField('Nome do Insumo', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Nome deve ter entre 2 e 100 caracteres')
    ])
    
    categoria = SelectField('Categoria', 
        choices=[(c.value, c.value) for c in CategoriaInsumo],
        validators=[DataRequired()]
    )
    
    unidade = SelectField('Unidade de Medida', 
        choices=[(u.value, u.value) for u in UnidadeMedida],
        validators=[DataRequired()]
    )
    
    quantidade_inicial = DecimalField('Quantidade Inicial', validators=[
        DataRequired(),
        NumberRange(min=0, message='Quantidade deve ser maior ou igual a zero')
    ], places=2)
    
    quantidade_minima = DecimalField('Quantidade Mínima', validators=[
        DataRequired(),
        NumberRange(min=0, message='Quantidade mínima deve ser maior ou igual a zero')
    ], places=2)
    
    data_validade = DateField('Data de Validade', validators=[Optional()])
    
    observacoes = TextAreaField('Observações')
    
    def validate_data_validade(self, field):
        if field.data and field.data <= date.today():
            raise ValidationError('Data de validade deve ser futura')

class MovimentacaoInsumoForm(FlaskForm):
    insumo_id = SelectField('Insumo', validators=[DataRequired()], coerce=int)
    tipo = SelectField('Tipo de Movimentação', 
        choices=[
            ('Entrada - Compra', 'Entrada - Compra'),
            ('Entrada - Doação', 'Entrada - Doação'),
            ('Saída - Uso', 'Saída - Uso'),
            ('Saída - Perda', 'Saída - Perda'),
            ('Ajuste', 'Ajuste')
        ],
        validators=[DataRequired()]
    )
    
    quantidade = DecimalField('Quantidade', validators=[
        DataRequired(),
        NumberRange(min=0.01, message='Quantidade deve ser maior que zero')
    ], places=2)
    
    data_movimentacao = DateField('Data da Movimentação', validators=[DataRequired()], default=date.today)
    
    observacoes = TextAreaField('Observações', validators=[
        Length(max=500, message='Observações devem ter no máximo 500 caracteres')
    ])
    
    def validate_data_movimentacao(self, field):
        if field.data and field.data > date.today():
            raise ValidationError('Data da movimentação não pode ser futura')