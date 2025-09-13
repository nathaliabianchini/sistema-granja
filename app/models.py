import enum
import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
        
class Sexo(enum.Enum):
    MASCULINO = "Masculino"
    FEMININO = "Feminino"

class TipoUsuario(enum.Enum):
    OPERADOR = "Operador de Produção"
    GERENTE = "Gerente"
    ADMIN = "ADMIN"

class Granjas(db.Model):
    __tablename__ = 'granja'
    id_granja = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cnpj_granja = db.Column(db.String(14), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<Granja {self.id_granja}>'

class Usuarios(db.Model):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    sexo = db.Column(db.Enum(Sexo), nullable=True)
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

class UserActivityLog(db.Model):
    __tablename__ = 'user_activity_log'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    
    user = db.relationship('Usuarios', backref='activity_logs')
    
    def __repr__(self):
        return f'<UserActivityLog {self.id}>'
    
class Setores(db.Model):
    __tablename__ = 'setor'
    id_setor = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    descricao_setor = db.Column(db.String(100), nullable=False)
    capacidade = db.Column(db.Integer, nullable=False)
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)

    granja = db.relationship('Granjas', backref='setores')

    def __repr__(self):
        return f'<Setor {self.id_setor}>'

class TipoAve(enum.Enum):
    POEDEIRAS_LEVES = "Poedeiras Leves (ovos brancos)"
    POEDEIRAS_PESADAS = "Poedeiras Pesadas (ovos vermelhos)"

class Lotes(db.Model):
    __tablename__ = 'lote'
    id_lote = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_setor = db.Column(db.String(36), db.ForeignKey('setor.id_setor'), nullable=False)
    tipo_ave = db.Column(db.Enum(TipoAve), nullable=False)
    quantidade_ave = db.Column(db.Integer, nullable=False)

    setor = db.relationship('Setores', backref='lotes')   

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

class Aves(db.Model):
    __tablename__ = 'ave'
    id_ave = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=False)
    raca_ave = db.Column(db.Enum(RacaAve), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=True)
    tempo_de_vida = db.Column(db.Integer, nullable=False)  # em semanas
    media_peso = db.Column(db.Float, nullable=False)
    tipo_alojamento = db.Column(db.String(100), nullable=False)
    historico_vacinas = db.Column(db.String(200), db.ForeignKey('vacina.id_vacina'), nullable=True)
    caracteristicas_geneticas = db.Column(db.String(200), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    
    # Campos para soft delete
    is_ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_exclusao = db.Column(db.DateTime, nullable=True)
    motivo_exclusao = db.Column(db.Text, nullable=True)
    excluido_por = db.Column(db.String(100), nullable=True)
    
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False) 

    granja = db.relationship('Granjas', backref='aves')
    lote = db.relationship('Lotes', backref='aves')
    vacina = db.relationship('Vacinas', backref='aves')

    def __repr__(self):
        return f'<Ave {self.id_ave}>'

class TipoInsumo(enum.Enum):
    RACAO = "Ração"
    MEDICAMENTOS = "Medicamentos"
    FERRAMENTAS = "Ferramentas"
    EQUIPAMENTOS = "Equipamentos"

class Insumos(db.Model):
    __tablename__ = 'insumo'
    id_insumo = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), nullable=False)
    tipo_insumo = db.Column(db.Enum(TipoInsumo), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data_validade = db.Column(db.Date, nullable=False)

    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    granja = db.relationship('Granjas', backref='insumos')

    def __repr__(self):
        return f'<Insumo {self.id_insumo}>'

class Vacinas(db.Model):
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

class CategoriaNotificacao(enum.Enum):
    ESTOQUE = "Estoque"
    MANUTENCAO = "Manutenção"
    RELATORIOS = "Relatórios"
    GERAL = "Geral"

class PrioridadeNotificacao(enum.Enum):
    BAIXA = "Baixa"
    NORMAL = "Normal"
    ALTA = "Alta"
    CRITICA = "Crítica"

class StatusNotificacao(enum.Enum):
    ATIVO = "Ativo"
    LIDA = "Lida"
    ARQUIVADA = "Arquivada"
    EXCLUIDA = "Excluída"

class Avisos(db.Model):
    __tablename__ = 'aviso'
    id_aviso = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.Enum(CategoriaNotificacao), nullable=False)
    prioridade = db.Column(db.Enum(PrioridadeNotificacao), default=PrioridadeNotificacao.NORMAL)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_validade = db.Column(db.DateTime, nullable=True)
    criado_por = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    is_ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_exclusao = db.Column(db.DateTime, nullable=True)
    excluido_por = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=True)
    
    criador = db.relationship('Usuarios', foreign_keys=[criado_por], backref='avisos_criados')
    exclusor = db.relationship('Usuarios', foreign_keys=[excluido_por], backref='avisos_excluidos')
    
    def __repr__(self):
        return f'<Aviso {self.id_aviso}>'

class NotificacaoUsuario(db.Model):
    __tablename__ = 'notificacao_usuario'
    id_notificacao = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_aviso = db.Column(db.String(36), db.ForeignKey('aviso.id_aviso'), nullable=False)
    id_usuario = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    status = db.Column(db.Enum(StatusNotificacao), default=StatusNotificacao.ATIVO, nullable=False)
    data_leitura = db.Column(db.DateTime, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    aviso = db.relationship('Avisos', backref='notificacoes')
    usuario = db.relationship('Usuarios', backref='notificacoes_recebidas')
    
    def __repr__(self):
        return f'<NotificacaoUsuario {self.id_notificacao}>'

class HistoricoAvisos(db.Model):
    __tablename__ = 'historico_avisos'
    id_historico = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_aviso = db.Column(db.String(36), db.ForeignKey('aviso.id_aviso'), nullable=False)
    acao = db.Column(db.String(50), nullable=False)
    detalhes = db.Column(db.Text, nullable=True)
    usuario_acao = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    data_acao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    aviso = db.relationship('Avisos', backref='historico')
    usuario = db.relationship('Usuarios', backref='acoes_avisos')
    
    def __repr__(self):
        return f'<HistoricoAvisos {self.id_historico}>'

class Producoes(db.Model):
    __tablename__ = 'producao'
    id_producao = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=False)
    data_producao = db.Column(db.Date, nullable=False)
    quantidade_aves = db.Column(db.Integer, nullable=False)
    quantidade_produzida = db.Column(db.Integer, nullable=False)
    qualidade_producao = db.Column(db.Enum(QualidadeProducao), nullable=False)    
    producao_nao_aproveitada = db.Column(db.Integer, nullable=False)
    observacoes = db.Column(db.Text, nullable=True)

    lote = db.relationship('Lotes', backref='producoes')

    def __repr__(self):
        return f'<Producao {self.id_producao}>'