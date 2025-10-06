from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from app.models.database import TipoVacina
from datetime import date

class EstoqueVacinaForm(FlaskForm):
    tipo_vacina = SelectField('Tipo de Vacina', 
        choices=[(tv.value, tv.value) for tv in TipoVacina],
        validators=[DataRequired()]
    )
    fabricante = StringField('Fabricante', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Fabricante deve ter entre 2 e 100 caracteres')
    ])
    lote_vacina = StringField('Lote da Vacina', validators=[
        DataRequired(),
        Length(min=1, max=50, message='Lote deve ter entre 1 e 50 caracteres')
    ])
    data_validade = DateField('Data de Validade', validators=[DataRequired()])
    quantidade_doses = IntegerField('Quantidade de Doses', validators=[
        DataRequired(),
        NumberRange(min=1, message='Quantidade deve ser maior que zero')
    ])
    data_entrada = DateField('Data de Entrada', validators=[DataRequired()], default=date.today)
    observacoes = TextAreaField('Observações')

    def validate_data_validade(self, field):
        if field.data and field.data <= date.today():
            raise ValidationError('Data de validade deve ser futura')