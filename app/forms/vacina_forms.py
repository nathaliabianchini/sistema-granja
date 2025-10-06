from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange
from app.models.database import TipoVacina
from datetime import date

class VacinaForm(FlaskForm):  
    tipo_vacina = SelectField('Tipo de Vacina', 
        choices=[(tv.value, tv.value) for tv in TipoVacina],
        validators=[DataRequired()]
    )
    id_lote = StringField('ID do Lote', validators=[
        DataRequired(),
        Length(min=1, max=50, message='ID do lote deve ter entre 1 e 50 caracteres')
    ])
    data_aplicacao = DateField('Data de Aplicação', validators=[DataRequired()], default=date.today)
    quantidade_aves = IntegerField('Quantidade de Aves', validators=[
        DataRequired(),
        NumberRange(min=1, message='Quantidade deve ser maior que zero')
    ])
    responsavel = StringField('Responsável', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Responsável deve ter entre 2 e 100 caracteres')
    ])
    observacoes = TextAreaField('Observações')