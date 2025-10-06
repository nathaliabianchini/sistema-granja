import datetime
from peewee import (SqliteDatabase, Model, AutoField, CharField, DateField, 
                    BooleanField, IntegerField, DoubleField, TextField, ForeignKeyField, 
                    DateTimeField, DecimalField)
from enum import Enum

db = SqliteDatabase('BD_Granja.db')

class BaseModel(Model):
    class Meta:
        database = db

class Granja(BaseModel):
    id_granja = AutoField()                             #PK
    cnpj_granja = CharField(max_length=18)

class Sexo(Enum):
    FEMININO = "Feminino"
    MASCULINO = "Masculino"

class TipoUsuarios(Enum):
    OPERADOR = "Operador de Produção"
    GERENTE = "Gerente"
    ADMIN = "ADMIN"
    
class Usuarios(BaseModel):
    id_usuario = AutoField()
    nome = CharField(max_length=100)
    username = CharField(max_length=50, unique=True)  
    email = CharField(max_length=100)
    cpf = CharField(max_length=14)
    senha = CharField(max_length=100)
    tipo_usuario = CharField(max_length=20)
    id_granja = CharField(max_length=50)
    sexo = CharField(max_length=1)
    data_nascimento = DateField()
    endereco = TextField()
    data_admissao = DateField()
    carteira_trabalho = CharField(max_length=50)
    telefone = CharField(max_length=20)
    
    class Meta:
        database = db
        table_name = 'usuarios'

class Setor(BaseModel):
    id_setor = AutoField()                              #PK
    descricao_setor = CharField(max_length=100)
    capacidade = IntegerField()
    granja = ForeignKeyField(Granja, backref="setores")

class TipoAve(Enum):
    POEDEIRAS_LEVES = "Poedeiras Leves (ovos brancos)"
    POEDEIRAS_PESADAS = "Poedeiras Pesadas (ovos vermelhos)"

class Lote(BaseModel):
    id_lote = AutoField()
    numero_lote = CharField(max_length=50)
    data_entrada = DateField()
    quantidade_inicial = IntegerField()
    idade_inicial = IntegerField()
    raca = CharField(max_length=100)
    fornecedor = CharField(max_length=200)
    observacoes = TextField(null=True)
    ativo = BooleanField(default=True) 

    class Meta:
        table_name = 'lotes'

class RacaAve(Enum):
    ISA_BROWN = "Isa Brown"
    HY_LINE_BROWN = "Hy-Line Brown"
    LOHMANN_BROWN = "Lohmann Brown"
    LEGHORN = "Leghorn"
    RHODE_ISLAND_RED = "Rhode Island Red"
    EMBRAPA_051 = "Embrapa 051"
    NEW_HAMPSHIRE = "New Hampshire"

class Aves(BaseModel):
    id_ave = AutoField()                                #PK
    id_lote = CharField(max_length=50)                 
    raca_ave = CharField(max_length=100)               
    data_nascimento = DateField()
    tempo_de_vida = IntegerField()                     
    media_peso = DoubleField()
    caracteristicas_geneticas = TextField()            
    tipo_alojamento = CharField(max_length=50)           
    historico_vacinas = TextField()                    
    observacoes = TextField(null=True)                 
    ativa = BooleanField(default=True)                 
    
    class Meta:
        table_name = 'aves'

class CategoriaInsumo(Enum):
    RACAO = "Ração"
    MEDICAMENTO = "Medicamento"
    SUPLEMENTO = "Suplemento"
    EQUIPAMENTO = "Equipamento"
    LIMPEZA = "Limpeza"
    MANUTENCAO = "Manutenção"
    EMBALAGEM = "Embalagem"
    OUTROS = "Outros"

class TipoMovimentacao(Enum):
    ENTRADA_COMPRA = "Entrada - Compra"
    ENTRADA_DOACAO = "Entrada - Doação"
    SAIDA_USO = "Saída - Uso"
    SAIDA_PERDA = "Saída - Perda"
    AJUSTE = "Ajuste"

class UnidadeMedida(Enum):
    KG = "kg"
    LITRO = "L"
    UNIDADE = "un"
    GRAMAS = "g"
    TONELADA = "t"
    SACO = "saco"
    CAIXA = "caixa"

class TipoInsumo(Enum):
    RACAO = "Ração"
    MEDICAMENTOS = "Medicamentos"
    FERRAMENTAS = "Ferramentas"
    EQUIPAMENTOS = "Equipamentos"

class InsumoNovo(BaseModel):
    id_insumo = AutoField()
    nome = CharField(max_length=100)
    categoria = CharField(max_length=50, choices=[(c.value, c.value) for c in CategoriaInsumo])
    unidade = CharField(max_length=10, choices=[(u.value, u.value) for u in UnidadeMedida])
    quantidade_atual = DecimalField(max_digits=10, decimal_places=2, default=0)
    quantidade_minima = DecimalField(max_digits=10, decimal_places=2, default=0)
    data_validade = DateField(null=True)
    observacoes = TextField(null=True)
    ativo = BooleanField(default=True)
    data_criacao = DateTimeField(default=datetime.datetime.now)
    usuario_criacao = ForeignKeyField(Usuarios, backref='insumos_criados', null=True)

    class Meta:
        table_name = 'insumos_novo'

class MovimentacaoInsumo(BaseModel):
    id_movimentacao = AutoField()
    insumo = ForeignKeyField(InsumoNovo, backref='movimentacoes')
    tipo = CharField(max_length=50, choices=[(t.value, t.value) for t in TipoMovimentacao])
    quantidade = DecimalField(max_digits=10, decimal_places=2)
    data_movimentacao = DateTimeField(default=datetime.datetime.now)
    observacoes = TextField(null=True)
    usuarios = ForeignKeyField(Usuarios, backref='movimentacoes_insumo')
    estoque_anterior = DecimalField(max_digits=10, decimal_places=2)
    estoque_posterior = DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        table_name = 'movimentacoes_insumo'
    
class Insumo(BaseModel):
    id_insumo = AutoField()                             #PK
    nome = CharField(max_length=100)                    #Nome do produto
    tipo_insumo = CharField(
        choices=[member.value for member in TipoInsumo]
    )                     
    quantidade = IntegerField()                         #Quantidade total
    data_validade = DateField()

class TipoVacina(Enum):
    NEWCASTLE = "Newcastle"
    BRONQUITE = "Bronquite Infecciosa"
    GUMBORO = "Gumboro"
    BOUBA = "Bouba Aviária"
    MAREK = "Marek"
    ENCEFALOMIELITE = "Encefalomielite"
    SALMONELLA = "Salmonella"
    CORIZA = "Coriza Infecciosa"
    ILT = "Laringotraqueíte"
    METAPNEUMOVIRUS = "Metapneumovírus Aviário"

class EstoqueVacina(BaseModel):
    id_estoque_vacina = AutoField()
    tipo_vacina = CharField(
        choices=[member.value for member in TipoVacina]
    )
    fabricante = CharField(max_length=100)
    lote_vacina = CharField(max_length=50)
    data_validade = DateField()
    quantidade_doses = IntegerField()
    data_entrada = DateField(default=datetime.date.today)
    observacoes = TextField(null=True)
    ativo = BooleanField(default=True)
    
    class Meta:
        table_name = 'estoque_vacina'

class Vacinacao(BaseModel):
    id_vacinacao = AutoField()
    data_aplicacao = DateField()
    responsavel = CharField(max_length=100)
    tipo_vacina = CharField(
        choices=[member.value for member in TipoVacina]
    )
    id_lote = CharField(max_length=50)  
    quantidade_aves = IntegerField()
    observacoes = TextField(null=True)
    
    class Meta:
        table_name = 'vacinacao'

class StatusVacinacao(Enum):
    AGENDADA = 'AGENDADA'
    APLICADA = 'APLICADA'
    CANCELADA = 'CANCELADA'

class QualidadeProducao(Enum):
    EXCELENTE = "Excelente"
    BOM = "Bom"
    REGULAR = "Regular"
    RUIM = "Ruim"

class Producao(BaseModel):
    id_producao = AutoField()
    data_coleta = DateField()  
    quantidade_ovos = IntegerField()
    quantidade_aves = IntegerField()
    qualidade_producao = CharField(max_length=50)
    producao_nao_aproveitada = IntegerField(default=0)
    id_lote = CharField(max_length=50)  
    observacoes = TextField(null=True)
    responsavel = CharField(max_length=100)

    class Meta:
        table_name = 'producao'

class UserActivityLog(BaseModel):
    id_log = AutoField(primary_key=True)
    usuario_id = IntegerField()  
    acao = CharField(max_length=100)
    detalhes = TextField(null=True)
    data_acao = DateTimeField(default=lambda: datetime.datetime.now())
    
    class Meta:
        table_name = 'user_activity_logs'

class Avisos(BaseModel):
    id_aviso = AutoField(primary_key=True)
    titulo = CharField(max_length=200)
    mensagem = TextField()
    tipo = CharField(max_length=50)  
    data_criacao = DateTimeField(default=lambda: datetime.datetime.now())
    ativo = BooleanField(default=True)
    
    class Meta:
        table_name = 'avisos'

class NotificacaoUsuario(BaseModel):
    id_notificacao = AutoField(primary_key=True)
    usuario = ForeignKeyField(Usuarios, backref='notificacoes')
    aviso = ForeignKeyField(Avisos, backref='notificacoes')
    lida = BooleanField(default=False)
    data_leitura = DateTimeField(null=True)
    
    class Meta:
        table_name = 'notificacao_usuario'

class HistoricoAvisos(BaseModel):
    id_historico = AutoField(primary_key=True)
    aviso = ForeignKeyField(Avisos, backref='historicos')
    usuario_modificador = ForeignKeyField(Usuarios)
    acao = CharField(max_length=50)  
    data_acao = DateTimeField(default=lambda: datetime.datetime.now())
    
    class Meta:
        table_name = 'historico_avisos'

class HistoricoProducao(BaseModel):
    id_historico = AutoField(primary_key=True)
    producao = ForeignKeyField(Producao, backref='historicos')
    usuario_modificador = ForeignKeyField(Usuarios)
    acao = CharField(max_length=50)  
    valores_anteriores = TextField(null=True) 
    valores_novos = TextField(null=True)       
    data_acao = DateTimeField(default=lambda: datetime.datetime.now())
    
    class Meta:
        table_name = 'historico_producao'

class CategoriaNotificacao(BaseModel):
    id_categoria = AutoField(primary_key=True)
    nome = CharField(max_length=100, unique=True)
    descricao = TextField(null=True)
    cor = CharField(max_length=7, default='#007bff')  
    ativo = BooleanField(default=True)
    
    class Meta:
        table_name = 'categoria_notificacao'

class PrioridadeNotificacao(BaseModel):
    id_prioridade = AutoField(primary_key=True)
    nome = CharField(max_length=50, unique=True)  
    nivel = IntegerField(unique=True)  
    cor = CharField(max_length=7, default='#28a745')
    
    class Meta:
        table_name = 'prioridade_notificacao'

class StatusNotificacao(BaseModel):
    id_status = AutoField(primary_key=True)
    nome = CharField(max_length=50, unique=True)  
    descricao = TextField(null=True)
    
    class Meta:
        table_name = 'status_notificacao'

db.connect()
db.create_tables([Granja, Usuarios, Insumo, InsumoNovo, MovimentacaoInsumo, Lote, Setor, 
                  EstoqueVacina, Vacinacao, Aves, Producao, 
                  UserActivityLog, Avisos, NotificacaoUsuario, HistoricoAvisos, 
                  HistoricoProducao, CategoriaNotificacao, PrioridadeNotificacao, 
                  StatusNotificacao], safe=True)