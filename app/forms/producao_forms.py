from flask_wtf import FlaskForm
from wtforms import IntegerField, DateField, SelectField, TextAreaField, StringField
from wtforms.validators import DataRequired, NumberRange, Length
from app.models.database import QualidadeProducao

class ProducaoForm(FlaskForm):
    id_lote = StringField('Lote', validators=[
        DataRequired(),
        Length(min=1, max=50, message='O lote deve ter entre 1 e 50 caracteres')
    ])
    
    data_coleta = DateField('Data da Coleta', validators=[DataRequired()])
    quantidade_aves = IntegerField('Quantidade de Aves', validators=[
        DataRequired(),
        NumberRange(min=1, message='A quantidade deve ser maior que zero')
    ])
    quantidade_ovos = IntegerField('Quantidade de Ovos', validators=[
        DataRequired(),
        NumberRange(min=0, message='A quantidade não pode ser negativa')
    ])
    qualidade_producao = SelectField('Qualidade da Produção', 
        choices=[(q.value, q.value) for q in QualidadeProducao],
        validators=[DataRequired()]
    )
    producao_nao_aproveitada = IntegerField('Produção Não Aproveitada', validators=[
        DataRequired(),
        NumberRange(min=0, message='A quantidade não pode ser negativa')
    ])
    observacoes = TextAreaField('Observações')
    responsavel = StringField('Responsável', validators=[DataRequired()])