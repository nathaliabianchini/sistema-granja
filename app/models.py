import enum
import uuid
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
        
class Sexo(enum.Enum):
    MASCULINO = "Masculino"
    FEMININO = "Feminino"

class TipoUsuario(enum.Enum):
    OPERADOR = "Operador de Produção"
    GERENTE = "Gerente"
    ADMIN = "ADMIN"

class Granja(db.Model):
    __tablename__ = 'granja'
    id_granja = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cnpj_granja = db.Column(db.String(14), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Granja {self.id_granja}>'

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    sexo = db.Column(db.Enum(Sexo), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    endereco = db.Column(db.String(150), nullable=False)
    data_admissao = db.Column(db.Date, nullable=False)
    carteira_trabalho = db.Column(db.String(20), unique=True, nullable=False)
    telefone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    tipo_usuario = db.Column(db.Enum(TipoUsuario), nullable=False)
    is_ativo = db.Column(db.Boolean, default=True)
    matricula = db.Column(db.String(20), unique=True, nullable=False)
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)

    def to_dict(self):
        return {
            "id_usuario": self.id_usuario,
            "nome": self.nome,
            "email": self.email,
            "cpf": self.cpf,
            "tipo_usuario": self.tipo_usuario.value if self.tipo_usuario else None,
            "id_granja": self.id_granja,
            "carteira_trabalho": self.carteira_trabalho,
            "telefone": self.telefone,
            "sexo": self.sexo.value if self.sexo else None,
            "data_nascimento": self.data_nascimento.isoformat() if self.data_nascimento else None,
            "endereco": self.endereco,
            "data_admissao": self.data_admissao.isoformat() if self.data_admissao else None,
            "matricula": self.matricula
        }
    
    def __repr__(self):
        return f'<User {self.id_usuario}>'
    
class Setor(db.Model):
    __tablename__ = 'setor'
    id_setor = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    descricao_setor = db.Column(db.String(100), nullable=False)
    capacidade = db.Column(db.Integer, nullable=False)
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)

    granja = db.relationship('Granja', backref='setores')

    def __repr__(self):
        return f'<Setor {self.id_setor}>'

class TipoAve(enum.Enum):
    POEDEIRAS_LEVES = "Poedeiras Leves (ovos brancos)"
    POEDEIRAS_PESADAS = "Poedeiras Pesadas (ovos vermelhos)"

class Lote(db.Model):
    __tablename__ = 'lote'
    id_lote = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_setor = db.Column(db.String(36), db.ForeignKey('setor.id_setor'), nullable=False)
    tipo_ave = db.Column(db.Enum(TipoAve), nullable=False)
    quantidade_ave = db.Column(db.Integer, nullable=False)

    setor = db.relationship('Setor', backref='lotes')   

    def __repr__(self):
        return f'<Lote {self.id_lote}>'

class RacaAve(enum.Enum):
    ISA_BROWN = "Isa Brown"
    HY_LINE_BROWN = "Hy-Line Brown"
    LOHMANN_BROWN = "Lohmann Brown"
    LEGHORN = "Leghorn"
    
    RHODE_ISLAND_RED = "Rhode Island Red"
    EMBRAPA_051 = "Embrapa 051"
    NEW_HAMPSHIRE = "New Hampshire"

class Ave(db.Model):
    __tablename__ = 'ave'
    id_ave = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=False)
    raca_ave = db.Column(db.Enum(RacaAve), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    tempo_de_vida = db.Column(db.Integer, nullable=False)  # em semanas
    media_peso = db.Column(db.Float, nullable=False)
    observacoes = db.Column(db.Text, nullable=True)

    lote = db.relationship('Lote', backref='aves')

    def __repr__(self):
        return f'<Ave {self.id_ave}>'

class TipoInsumo(enum.Enum):
    RACAO = "Ração"
    MEDICAMENTOS = "Medicamentos"
    FERRAMENTAS = "Ferramentas"
    EQUIPAMENTOS = "Equipamentos"

class Insumo(db.Model):
    __tablename__ = 'insumo'
    id_insumo = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), nullable=False)
    tipo_insumo = db.Column(db.Enum(TipoInsumo), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data_validade = db.Column(db.Date, nullable=False)

    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    granja = db.relationship('Granja', backref='insumos')

    def __repr__(self):
        return f'<Insumo {self.id_insumo}>'

class Vacina(db.Model):
    __tablename__ = 'vacina'
    id_vacina = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data = db.Column(db.Date, nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    nome_vacina = db.Column(db.String(100), nullable=False)
    id_setor = db.Column(db.String(36), db.ForeignKey('setor.id_setor'), nullable=False)  
    observacoes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Vacina {self.id_vacina}>'

class QualidadeProducao(enum.Enum):
    EXCELENTE = "Excelente"
    BOM = "Bom"
    REGULAR = "Regular"
    RUIM = "Ruim"

class Producao(db.Model):
    __tablename__ = 'producao'
    id_producao = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=False)
    data_producao = db.Column(db.Date, nullable=False)
    quantidade_aves = db.Column(db.Integer, nullable=False)
    quantidade_produzida = db.Column(db.Integer, nullable=False)
    qualidade_producao = db.Column(db.Enum(QualidadeProducao), nullable=False)    
    producao_nao_aproveitada = db.Column(db.Integer, nullable=False)
    observacoes = db.Column(db.Text, nullable=True)

    lote = db.relationship('Lote', backref='producoes')

    def __repr__(self):
        return f'<Producao {self.id_producao}>'