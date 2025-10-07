from peewee import ModelSelect
from wtforms import Form, DateTimeField, SelectField, StringField, TextAreaField, IntegerField, validators
from app.models.database import Aves, Lote, Setor, Usuarios

class MortalidadeForm(Form):
    data_hora_evento = DateTimeField('Data e Hora do Evento', [validators.DataRequired()])
    ave = SelectField('Ave', coerce=int, choices=[])
    lote = SelectField('Lote', coerce=int, choices=[])
    setor = SelectField('Setor', coerce=int, choices=[])
    motivo_obito = StringField('Motivo do Óbito', [validators.DataRequired()])
    categoria_motivo = SelectField('Categoria do Motivo', choices=[
        ('doenca', 'Doença'),
        ('idade_avancada', 'Idade Avançada'),
        ('acidente', 'Acidente'),
        ('outros', 'Outros')
    ])
    descricao_adicional = TextAreaField('Descrição Adicional')
    funcionario = SelectField('Funcionário', coerce=int, choices=[])

    def set_choices(self):
        self.ave.choices = [(a.id_ave, f"{a.id_ave} - {a.raca_ave}") for a in Aves.select()]
        self.lote.choices = [(l.id_lote, l.numero_lote) for l in Lote.select()]
        self.setor.choices = [(s.id_setor, s.descricao_setor) for s in Setor.select()]
        self.funcionario.choices = [(u.id_usuario, u.nome) for u in Usuarios.select()]
