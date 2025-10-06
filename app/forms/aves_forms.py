from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, SelectField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from datetime import date

class AvesForm(FlaskForm):
    id_lote = StringField('ID do Lote', validators=[DataRequired(), Length(min=1, max=50)])
    
    raca_ave = SelectField('Raça da Ave', 
        choices=[
            ('Isa Brown', 'Isa Brown'),
            ('Hy-Line Brown', 'Hy-Line Brown'),
            ('Lohmann Brown', 'Lohmann Brown'),
            ('Leghorn', 'Leghorn'),
            ('Rhode Island Red', 'Rhode Island Red'),
            ('Embrapa 051', 'Embrapa 051'),
            ('New Hampshire', 'New Hampshire')
        ],
        validators=[DataRequired()]
    )
    
    data_nascimento = DateField('Data de Nascimento', validators=[DataRequired()])
    tempo_de_vida = IntegerField('Tempo de Vida (dias)', validators=[DataRequired(), NumberRange(min=1)])
    media_peso = DecimalField('Média de Peso (kg)', validators=[DataRequired(), NumberRange(min=0.1)], places=2)
    caracteristicas_geneticas = TextAreaField('Características Genéticas', validators=[DataRequired(), Length(min=10, max=500)])
    tipo_alojamento = SelectField('Tipo de Alojamento', 
        choices=[
            ('gaiola', 'Gaiola'),
            ('galinheiro', 'Galinheiro'),
            ('livre', 'Criação Livre'),
            ('semi_livre', 'Semi-Livre')
        ],
        validators=[DataRequired()]
    )
    historico_vacinas = TextAreaField('Histórico de Vacinas', validators=[DataRequired(), Length(min=10, max=1000)])
    observacoes = TextAreaField('Observações', validators=[Optional(), Length(max=1000)])

class FiltroAvesForm(FlaskForm):
    id_ave = StringField('ID da Ave', validators=[Optional()])
    raca = StringField('Raça', validators=[Optional()])
    id_lote = StringField('ID do Lote', validators=[Optional()])
    data_nascimento = DateField('Data de Nascimento', validators=[Optional()])
    incluir_inativas = SelectField('Incluir Inativas',
        choices=[('false', 'Não'), ('true', 'Sim')],
        default='false',
        validators=[Optional()]
    )