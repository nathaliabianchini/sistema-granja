from flask_wtf import FlaskForm
from wtforms import IntegerField, DateField, SelectField, TextAreaField, StringField
from wtforms.validators import DataRequired, NumberRange
from app.models.database import QualidadeProducao

class ProducaoForm(FlaskForm):
    lote = SelectField('Lote', coerce=int, validators=[DataRequired()])
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