import enum
import uuid
from datetime import date, datetime
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
    nome_granja = db.Column(db.String(100), nullable=False)
    
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

class TipoVacina(db.Model):
    """Tipos/Categorias de vacinas disponíveis"""
    __tablename__ = 'tipo_vacina'
    
    id_tipo_vacina = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    fabricante = db.Column(db.String(100))
    idade_recomendada_dias = db.Column(db.Integer) 
    duracao_imunidade_dias = db.Column(db.Integer)  
    metodo_aplicacao = db.Column(db.String(50))  
    temperatura_armazenamento = db.Column(db.String(50))  
    is_ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    granja = db.relationship('Granjas', backref='tipos_vacina')
    agendamentos = db.relationship('AgendamentoVacinacao', backref='tipo_vacina', lazy=True, cascade='all, delete-orphan')
    registros_vacinacao = db.relationship('RegistroVacinacao', backref='tipo_vacina', lazy=True)
    lotes_vacina = db.relationship('LoteVacina', backref='tipo_vacina', lazy=True)

    def to_dict(self):
        return {
            'id_tipo_vacina': self.id_tipo_vacina,
            'nome': self.nome,
            'descricao': self.descricao,
            'fabricante': self.fabricante,
            'idade_recomendada_dias': self.idade_recomendada_dias,
            'duracao_imunidade_dias': self.duracao_imunidade_dias,
            'metodo_aplicacao': self.metodo_aplicacao,
            'temperatura_armazenamento': self.temperatura_armazenamento,
            'is_ativo': self.is_ativo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<TipoVacina {self.nome}>'

class AgendamentoVacinacao(db.Model):
    """Calendário de vacinação programado"""
    __tablename__ = 'agendamento_vacinacao'
    
    id_agendamento = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_tipo_vacina = db.Column(db.String(36), db.ForeignKey('tipo_vacina.id_tipo_vacina'), nullable=False)
    data_agendada = db.Column(db.Date, nullable=False)
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=True) 
    grupo_alvo = db.Column(db.String(100)) 
    quantidade_estimada = db.Column(db.Integer)  
    responsavel = db.Column(db.String(100))
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), default='agendado') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    granja = db.relationship('Granjas', backref='agendamentos_vacinacao')
    lote = db.relationship('Lotes', backref='agendamentos_vacinacao')
    registros_vacinacao = db.relationship('RegistroVacinacao', backref='agendamento', lazy=True)

    def to_dict(self):
        return {
            'id_agendamento': self.id_agendamento,
            'id_tipo_vacina': self.id_tipo_vacina,
            'nome_tipo_vacina': self.tipo_vacina.nome if self.tipo_vacina else None,
            'data_agendada': self.data_agendada.isoformat() if self.data_agendada else None,
            'id_lote': self.id_lote,
            'grupo_alvo': self.grupo_alvo,
            'quantidade_estimada': self.quantidade_estimada,
            'responsavel': self.responsavel,
            'observacoes': self.observacoes,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'id_granja': self.id_granja,
            'registros_count': len(self.registros_vacinacao) if self.registros_vacinacao else 0
        }

    def __repr__(self):
        return f'<AgendamentoVacinacao {self.id_agendamento}>'

class LoteVacina(db.Model):
    """Lotes de vacinas (estoque)"""
    __tablename__ = 'lote_vacina'
    
    id_lote_vacina = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_tipo_vacina = db.Column(db.String(36), db.ForeignKey('tipo_vacina.id_tipo_vacina'), nullable=False)
    numero_lote = db.Column(db.String(50), nullable=False)
    data_fabricacao = db.Column(db.Date)
    data_validade = db.Column(db.Date, nullable=False)
    quantidade_recebida = db.Column(db.Integer, nullable=False)
    quantidade_usada = db.Column(db.Integer, default=0)
    fornecedor = db.Column(db.String(100))
    preco_compra = db.Column(db.Numeric(10, 2))
    local_armazenamento = db.Column(db.String(100))
    is_ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    granja = db.relationship('Granjas', backref='lotes_vacina')
    registros_vacinacao = db.relationship('RegistroVacinacao', backref='lote_vacina', lazy=True)
    
    @property
    def quantidade_disponivel(self):
        return self.quantidade_recebida - self.quantidade_usada
    
    @property
    def is_expirado(self):
        return datetime.now().date() > self.data_validade if self.data_validade else False

    def to_dict(self):
        return {
            'id_lote_vacina': self.id_lote_vacina,
            'id_tipo_vacina': self.id_tipo_vacina,
            'nome_tipo_vacina': self.tipo_vacina.nome if self.tipo_vacina else None,
            'numero_lote': self.numero_lote,
            'data_fabricacao': self.data_fabricacao.isoformat() if self.data_fabricacao else None,
            'data_validade': self.data_validade.isoformat() if self.data_validade else None,
            'quantidade_recebida': self.quantidade_recebida,
            'quantidade_usada': self.quantidade_usada,
            'quantidade_disponivel': self.quantidade_disponivel,
            'fornecedor': self.fornecedor,
            'preco_compra': float(self.preco_compra) if self.preco_compra else None,
            'local_armazenamento': self.local_armazenamento,
            'is_ativo': self.is_ativo,
            'is_expirado': self.is_expirado,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<LoteVacina {self.numero_lote}>'

class RegistroVacinacao(db.Model):
    """Registros de vacinação aplicada"""
    __tablename__ = 'registro_vacinacao'
    
    id_registro = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_agendamento = db.Column(db.String(36), db.ForeignKey('agendamento_vacinacao.id_agendamento'), nullable=True)
    id_tipo_vacina = db.Column(db.String(36), db.ForeignKey('tipo_vacina.id_tipo_vacina'), nullable=False)
    id_lote_vacina = db.Column(db.String(36), db.ForeignKey('lote_vacina.id_lote_vacina'), nullable=False)
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=True) 
    data_aplicacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    quantidade_aplicada = db.Column(db.Integer, nullable=False)
    grupo_alvo = db.Column(db.String(100))  
    responsavel = db.Column(db.String(100), nullable=False)
    metodo_aplicacao = db.Column(db.String(50))
    observacoes = db.Column(db.Text)
    reacoes_adversas = db.Column(db.Text)  
    temperatura_aplicacao = db.Column(db.Numeric(4, 1)) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    granja = db.relationship('Granjas', backref='registros_vacinacao')
    lote = db.relationship('Lotes', backref='registros_vacinacao')

    def to_dict(self):
        return {
            'id_registro': self.id_registro,
            'id_agendamento': self.id_agendamento,
            'id_tipo_vacina': self.id_tipo_vacina,
            'nome_tipo_vacina': self.tipo_vacina.nome if self.tipo_vacina else None,
            'id_lote_vacina': self.id_lote_vacina,
            'numero_lote_vacina': self.lote_vacina.numero_lote if self.lote_vacina else None,
            'id_lote': self.id_lote,
            'data_aplicacao': self.data_aplicacao.isoformat() if self.data_aplicacao else None,
            'quantidade_aplicada': self.quantidade_aplicada,
            'grupo_alvo': self.grupo_alvo,
            'responsavel': self.responsavel,
            'metodo_aplicacao': self.metodo_aplicacao,
            'observacoes': self.observacoes,
            'reacoes_adversas': self.reacoes_adversas,
            'temperatura_aplicacao': float(self.temperatura_aplicacao) if self.temperatura_aplicacao else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<RegistroVacinacao {self.id_registro}>'

class Aves(db.Model):
    __tablename__ = 'ave'
    id_ave = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=False)
    raca_ave = db.Column(db.Enum(RacaAve), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=True)
    tempo_de_vida = db.Column(db.Integer, nullable=False) 
    media_peso = db.Column(db.Float, nullable=False)
    tipo_alojamento = db.Column(db.String(100), nullable=False)
    historico_vacinas = db.Column(db.String(200), nullable=True)  
    caracteristicas_geneticas = db.Column(db.String(200), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    
    is_ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_exclusao = db.Column(db.DateTime, nullable=True)
    motivo_exclusao = db.Column(db.Text, nullable=True)
    excluido_por = db.Column(db.String(100), nullable=True)
    
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False) 

    granja = db.relationship('Granjas', backref='aves')
    lote = db.relationship('Lotes', backref='aves')

    def __repr__(self):
        return f'<Ave {self.id_ave}>'

class TipoInsumo(enum.Enum):
    RACAO = "Ração"
    MEDICAMENTOS = "Medicamentos"
    FERRAMENTAS = "Ferramentas"
    EQUIPAMENTOS = "Equipamentos"
    VACINAS = "Vacinas"
    SUPLEMENTOS = "Suplementos"
    DESINFETANTES = "Desinfetantes"
    OUTROS = "Outros"

class UnidadeMedida(enum.Enum):
    KG = "Quilograma"
    GRAMAS = "Gramas"
    LITROS = "Litros"
    ML = "Mililitros"
    UNIDADES = "Unidades"
    METROS = "Metros"
    CAIXAS = "Caixas"
    SACAS = "Sacas"

class TipoMovimentacao(enum.Enum):
    ENTRADA_COMPRA = "Entrada - Compra"
    ENTRADA_DOACAO = "Entrada - Doação"
    ENTRADA_TRANSFERENCIA = "Entrada - Transferência"
    ENTRADA_DEVOLUCAO = "Entrada - Devolução"
    SAIDA_USO = "Saída - Uso"
    SAIDA_PERDA = "Saída - Perda"
    SAIDA_VENCIMENTO = "Saída - Vencimento"
    SAIDA_TRANSFERENCIA = "Saída - Transferência"
    AJUSTE_INVENTARIO = "Ajuste - Inventário"

class StatusInsumo(enum.Enum):
    ATIVO = "Ativo"
    INATIVO = "Inativo"
    VENCIDO = "Vencido"
    ESGOTADO = "Esgotado"

class Insumos(db.Model):
    """Cadastro de insumos e materiais"""
    __tablename__ = 'insumo'
    
    id_insumo = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    codigo_interno = db.Column(db.String(50), unique=True, nullable=True)  
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    tipo_insumo = db.Column(db.Enum(TipoInsumo), nullable=False)
    unidade_medida = db.Column(db.Enum(UnidadeMedida), nullable=False, default=UnidadeMedida.UNIDADES)
    
    quantidade_atual = db.Column(db.Numeric(10, 3), default=0)
    quantidade_minima = db.Column(db.Numeric(10, 3), default=0)  
    quantidade_maxima = db.Column(db.Numeric(10, 3), nullable=True)  
    
    fabricante = db.Column(db.String(100), nullable=True)
    fornecedor_principal = db.Column(db.String(100), nullable=True)
    numero_registro = db.Column(db.String(50), nullable=True)  
    composicao = db.Column(db.Text, nullable=True)  
    
    data_validade = db.Column(db.Date, nullable=True)
    local_armazenamento = db.Column(db.String(100), nullable=True)
    temperatura_armazenamento = db.Column(db.String(50), nullable=True)
    observacoes_armazenamento = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.Enum(StatusInsumo), default=StatusInsumo.ATIVO)
    preco_ultima_compra = db.Column(db.Numeric(10, 2), nullable=True)
    data_ultima_compra = db.Column(db.Date, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    
    granja = db.relationship('Granjas', backref='insumos_novos')
    criador = db.relationship('Usuarios', backref='insumos_criados')
    movimentacoes = db.relationship('MovimentacaoInsumo', backref='insumo', lazy=True, cascade='all, delete-orphan')
    
    @property
    def estoque_baixo(self):
        """Verificar se está com estoque baixo"""
        return self.quantidade_atual <= self.quantidade_minima
    
    @property
    def dias_para_vencer(self):
        """Dias para vencimento"""
        if not self.data_validade:
            return None
        delta = self.data_validade - date.today()
        return delta.days
    
    @property
    def status_validade(self):
        """Status baseado na validade"""
        if not self.data_validade:
            return "SEM_VALIDADE"
        
        dias = self.dias_para_vencer
        if dias < 0:
            return "VENCIDO"
        elif dias <= 30:
            return "VENCE_30_DIAS"
        elif dias <= 90:
            return "VENCE_90_DIAS"
        else:
            return "VALIDO"

    def to_dict(self):
        return {
            'id_insumo': self.id_insumo,
            'codigo_interno': self.codigo_interno,
            'nome': self.nome,
            'descricao': self.descricao,
            'tipo_insumo': self.tipo_insumo.value if self.tipo_insumo else None,
            'unidade_medida': self.unidade_medida.value if self.unidade_medida else None,
            'quantidade_atual': float(self.quantidade_atual) if self.quantidade_atual else 0,
            'quantidade_minima': float(self.quantidade_minima) if self.quantidade_minima else 0,
            'quantidade_maxima': float(self.quantidade_maxima) if self.quantidade_maxima else None,
            'fabricante': self.fabricante,
            'fornecedor_principal': self.fornecedor_principal,
            'numero_registro': self.numero_registro,
            'composicao': self.composicao,
            'data_validade': self.data_validade.isoformat() if self.data_validade else None,
            'local_armazenamento': self.local_armazenamento,
            'temperatura_armazenamento': self.temperatura_armazenamento,
            'observacoes_armazenamento': self.observacoes_armazenamento,
            'status': self.status.value if self.status else None,
            'preco_ultima_compra': float(self.preco_ultima_compra) if self.preco_ultima_compra else None,
            'data_ultima_compra': self.data_ultima_compra.isoformat() if self.data_ultima_compra else None,
            'estoque_baixo': self.estoque_baixo,
            'dias_para_vencer': self.dias_para_vencer,
            'status_validade': self.status_validade,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'nome_criador': self.criador.nome if self.criador else None,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<Insumo {self.nome}>'

class MovimentacaoInsumo(db.Model):
    """Movimentações de entrada e saída de insumos"""
    __tablename__ = 'movimentacao_insumo'
    
    id_movimentacao = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_insumo = db.Column(db.String(36), db.ForeignKey('insumo.id_insumo'), nullable=False)
    
    tipo_movimentacao = db.Column(db.Enum(TipoMovimentacao), nullable=False)
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)
    quantidade_anterior = db.Column(db.Numeric(10, 3), nullable=False)  
    quantidade_posterior = db.Column(db.Numeric(10, 3), nullable=False)  
    
    data_movimentacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_vencimento_lote = db.Column(db.Date, nullable=True) 
    

    numero_documento = db.Column(db.String(100), nullable=True)  
    fornecedor = db.Column(db.String(100), nullable=True)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=True)
    valor_total = db.Column(db.Numeric(12, 2), nullable=True)
    
    motivo = db.Column(db.String(200), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    setor_destino = db.Column(db.String(36), db.ForeignKey('setor.id_setor'), nullable=True)  
    
    responsavel = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    
    granja = db.relationship('Granjas', backref='movimentacoes_insumo')
    usuario_responsavel = db.relationship('Usuarios', backref='movimentacoes_realizadas')
    setor = db.relationship('Setores', backref='movimentacoes_insumo')

    def to_dict(self):
        return {
            'id_movimentacao': self.id_movimentacao,
            'id_insumo': self.id_insumo,
            'nome_insumo': self.insumo.nome if self.insumo else None,
            'tipo_movimentacao': self.tipo_movimentacao.value if self.tipo_movimentacao else None,
            'quantidade': float(self.quantidade) if self.quantidade else 0,
            'quantidade_anterior': float(self.quantidade_anterior) if self.quantidade_anterior else 0,
            'quantidade_posterior': float(self.quantidade_posterior) if self.quantidade_posterior else 0,
            'unidade_medida': self.insumo.unidade_medida.value if self.insumo and self.insumo.unidade_medida else None,
            'data_movimentacao': self.data_movimentacao.isoformat() if self.data_movimentacao else None,
            'data_vencimento_lote': self.data_vencimento_lote.isoformat() if self.data_vencimento_lote else None,
            'numero_documento': self.numero_documento,
            'fornecedor': self.fornecedor,
            'valor_unitario': float(self.valor_unitario) if self.valor_unitario else None,
            'valor_total': float(self.valor_total) if self.valor_total else None,
            'motivo': self.motivo,
            'observacoes': self.observacoes,
            'setor_destino': self.setor_destino,
            'nome_setor_destino': self.setor.descricao_setor if self.setor else None,
            'responsavel': self.responsavel,
            'nome_responsavel': self.usuario_responsavel.nome if self.usuario_responsavel else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<MovimentacaoInsumo {self.id_movimentacao}>'

class RelatorioConsumo(db.Model):
    """Relatórios de consumo de insumos"""
    __tablename__ = 'relatorio_consumo'
    
    id_relatorio = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tipo_periodo = db.Column(db.String(20), nullable=False) 
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    id_insumo = db.Column(db.String(36), db.ForeignKey('insumo.id_insumo'), nullable=True)
    tipo_insumo_filtro = db.Column(db.Enum(TipoInsumo), nullable=True)
    
    total_entradas = db.Column(db.Numeric(12, 3), default=0)
    total_saidas = db.Column(db.Numeric(12, 3), default=0)
    valor_total_entradas = db.Column(db.Numeric(15, 2), default=0)
    valor_total_saidas = db.Column(db.Numeric(15, 2), default=0)
    movimentacoes_count = db.Column(db.Integer, default=0)
    
    consumo_medio_diario = db.Column(db.Numeric(10, 3), default=0)
    tendencia_consumo = db.Column(db.String(20), nullable=True)  

    gerado_por = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    data_geracao = db.Column(db.DateTime, default=datetime.utcnow)
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    
    granja = db.relationship('Granjas', backref='relatorios_consumo')
    insumo = db.relationship('Insumos', backref='relatorios_consumo')
    responsavel = db.relationship('Usuarios', backref='relatorios_consumo_gerados')
    
    def to_dict(self):
        return {
            'id_relatorio': self.id_relatorio,
            'tipo_periodo': self.tipo_periodo,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'id_insumo': self.id_insumo,
            'nome_insumo': self.insumo.nome if self.insumo else None,
            'tipo_insumo_filtro': self.tipo_insumo_filtro.value if self.tipo_insumo_filtro else None,
            'total_entradas': float(self.total_entradas) if self.total_entradas else 0,
            'total_saidas': float(self.total_saidas) if self.total_saidas else 0,
            'valor_total_entradas': float(self.valor_total_entradas) if self.valor_total_entradas else 0,
            'valor_total_saidas': float(self.valor_total_saidas) if self.valor_total_saidas else 0,
            'movimentacoes_count': self.movimentacoes_count,
            'consumo_medio_diario': float(self.consumo_medio_diario) if self.consumo_medio_diario else 0,
            'tendencia_consumo': self.tendencia_consumo,
            'gerado_por': self.gerado_por,
            'nome_responsavel': self.responsavel.nome if self.responsavel else None,
            'data_geracao': self.data_geracao.isoformat() if self.data_geracao else None,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<RelatorioConsumo {self.id_relatorio}>'

class AlertaInsumo(db.Model):
    """Alertas automáticos para insumos"""
    __tablename__ = 'alerta_insumo'
    
    id_alerta = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_insumo = db.Column(db.String(36), db.ForeignKey('insumo.id_insumo'), nullable=False)
    
    tipo_alerta = db.Column(db.String(50), nullable=False)  
    nivel_prioridade = db.Column(db.String(20), default='NORMAL')  
    
    mensagem = db.Column(db.Text, nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_resolucao = db.Column(db.DateTime, nullable=True)
    resolvido_por = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=True)
    
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    
    granja = db.relationship('Granjas', backref='alertas_insumo')
    insumo = db.relationship('Insumos', backref='alertas')
    usuario_resolucao = db.relationship('Usuarios', backref='alertas_resolvidos')
    
    def to_dict(self):
        return {
            'id_alerta': self.id_alerta,
            'id_insumo': self.id_insumo,
            'nome_insumo': self.insumo.nome if self.insumo else None,
            'tipo_alerta': self.tipo_alerta,
            'nivel_prioridade': self.nivel_prioridade,
            'mensagem': self.mensagem,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_resolucao': self.data_resolucao.isoformat() if self.data_resolucao else None,
            'resolvido_por': self.resolvido_por,
            'nome_resolveu': self.usuario_resolucao.nome if self.usuario_resolucao else None,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<AlertaInsumo {self.id_alerta}>'

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

class QualidadeOvo(enum.Enum):
    EXCELENTE = "Excelente"
    BOM = "Bom"
    REGULAR = "Regular"
    RUIM = "Ruim"

class StatusProducao(enum.Enum):
    ATIVO = "Ativo"
    REVISADO = "Revisado"
    CANCELADO = "Cancelado"

class ProducaoOvos(db.Model):
    """Registro diário de produção de ovos"""
    __tablename__ = 'producao_ovos'
    
    id_producao_ovos = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_producao = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=True)
    id_setor = db.Column(db.String(36), db.ForeignKey('setor.id_setor'), nullable=False)
    quantidade_ovos_produzidos = db.Column(db.Integer, nullable=False)
    numero_aves_ativas = db.Column(db.Integer, nullable=False)
    ovos_quebrados_danificados = db.Column(db.Integer, default=0)
    qualidade_ovos = db.Column(db.Enum(QualidadeOvo), nullable=True)
    taxa_producao = db.Column(db.Numeric(5, 2), nullable=True)  
    ovos_aproveitaveis = db.Column(db.Integer, nullable=True) 
    operador_responsavel = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    observacoes = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(StatusProducao), default=StatusProducao.ATIVO)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=True) 
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    granja = db.relationship('Granjas', backref='producoes_ovos')
    lote = db.relationship('Lotes', backref='producoes_ovos')
    setor = db.relationship('Setores', backref='producoes_ovos')
    operador = db.relationship('Usuarios', foreign_keys=[operador_responsavel], backref='producoes_registradas')
    responsavel_atualizacao = db.relationship('Usuarios', foreign_keys=[updated_by], backref='producoes_atualizadas')
    
    def calcular_metricas(self):
        """Calcular métricas automáticas"""
        if self.numero_aves_ativas > 0:
            self.taxa_producao = round((self.quantidade_ovos_produzidos / self.numero_aves_ativas) * 100, 2)
        else:
            self.taxa_producao = 0
            
        self.ovos_aproveitaveis = self.quantidade_ovos_produzidos - self.ovos_quebrados_danificados

    def to_dict(self):
        return {
            'id_producao_ovos': self.id_producao_ovos,
            'data_producao': self.data_producao.isoformat() if self.data_producao else None,
            'id_lote': self.id_lote,
            'id_setor': self.id_setor,
            'descricao_setor': self.setor.descricao_setor if self.setor else None,
            'quantidade_ovos_produzidos': self.quantidade_ovos_produzidos,
            'numero_aves_ativas': self.numero_aves_ativas,
            'ovos_quebrados_danificados': self.ovos_quebrados_danificados,
            'ovos_aproveitaveis': self.ovos_aproveitaveis,
            'taxa_producao': float(self.taxa_producao) if self.taxa_producao else None,
            'qualidade_ovos': self.qualidade_ovos.value if self.qualidade_ovos else None,
            'operador_responsavel': self.operador_responsavel,
            'nome_operador': self.operador.nome if self.operador else None,
            'observacoes': self.observacoes,
            'status': self.status.value if self.status else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': self.updated_by,
            'nome_responsavel_atualizacao': self.responsavel_atualizacao.nome if self.responsavel_atualizacao else None,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<ProducaoOvos {self.id_producao_ovos}>'

class HistoricoProducaoOvos(db.Model):
    """Histórico de alterações na produção de ovos"""
    __tablename__ = 'historico_producao_ovos'
    
    id_historico = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_producao_ovos = db.Column(db.String(36), db.ForeignKey('producao_ovos.id_producao_ovos'), nullable=False)
    acao = db.Column(db.String(50), nullable=False)  
    dados_anteriores = db.Column(db.Text, nullable=True)  
    dados_novos = db.Column(db.Text, nullable=True)  
    motivo_alteracao = db.Column(db.Text, nullable=True)
    usuario_acao = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    data_acao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    producao = db.relationship('ProducaoOvos', backref='historico_alteracoes')
    usuario = db.relationship('Usuarios', backref='acoes_producao')
    
    def to_dict(self):
        return {
            'id_historico': self.id_historico,
            'id_producao_ovos': self.id_producao_ovos,
            'acao': self.acao,
            'dados_anteriores': self.dados_anteriores,
            'dados_novos': self.dados_novos,
            'motivo_alteracao': self.motivo_alteracao,
            'usuario_acao': self.usuario_acao,
            'nome_usuario': self.usuario.nome if self.usuario else None,
            'data_acao': self.data_acao.isoformat() if self.data_acao else None,
            'ip_address': self.ip_address
        }

    def __repr__(self):
        return f'<HistoricoProducaoOvos {self.id_historico}>'

class RelatorioProducao(db.Model):
    """Relatórios consolidados de produção"""
    __tablename__ = 'relatorio_producao'
    
    id_relatorio = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tipo_periodo = db.Column(db.String(20), nullable=False) 
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    id_setor = db.Column(db.String(36), db.ForeignKey('setor.id_setor'), nullable=True)
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=True)
    total_ovos_produzidos = db.Column(db.Integer, default=0)
    total_ovos_quebrados = db.Column(db.Integer, default=0)
    total_ovos_aproveitaveis = db.Column(db.Integer, default=0)
    media_aves_ativas = db.Column(db.Numeric(10, 2), default=0)
    taxa_producao_media = db.Column(db.Numeric(5, 2), default=0)
    dias_registrados = db.Column(db.Integer, default=0)
    gerado_por = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    data_geracao = db.Column(db.DateTime, default=datetime.utcnow)
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    granja = db.relationship('Granjas', backref='relatorios_producao')
    setor = db.relationship('Setores', backref='relatorios_producao')
    lote = db.relationship('Lotes', backref='relatorios_producao')
    responsavel = db.relationship('Usuarios', backref='relatorios_gerados')
    
    def to_dict(self):
        return {
            'id_relatorio': self.id_relatorio,
            'tipo_periodo': self.tipo_periodo,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'id_setor': self.id_setor,
            'descricao_setor': self.setor.descricao_setor if self.setor else None,
            'id_lote': self.id_lote,
            'total_ovos_produzidos': self.total_ovos_produzidos,
            'total_ovos_quebrados': self.total_ovos_quebrados,
            'total_ovos_aproveitaveis': self.total_ovos_aproveitaveis,
            'media_aves_ativas': float(self.media_aves_ativas) if self.media_aves_ativas else None,
            'taxa_producao_media': float(self.taxa_producao_media) if self.taxa_producao_media else None,
            'dias_registrados': self.dias_registrados,
            'gerado_por': self.gerado_por,
            'nome_responsavel': self.responsavel.nome if self.responsavel else None,
            'data_geracao': self.data_geracao.isoformat() if self.data_geracao else None,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<RelatorioProducao {self.id_relatorio}>'

    def __repr__(self):
        return f'<Producao {self.id_producao}>'

class CausaMortalidade(enum.Enum):
    DOENCA = "Doença"
    IDADE_AVANCADA = "Idade Avançada"
    ACIDENTE = "Acidente"
    ESTRESSE = "Estresse"
    PROBLEMAS_RESPIRATORIOS = "Problemas Respiratórios"
    PROBLEMAS_DIGESTIVOS = "Problemas Digestivos"
    PREDACAO = "Predação"
    DESCONHECIDA = "Desconhecida"
    OUTRAS = "Outras"

class StatusEventoMortalidade(enum.Enum):
    REGISTRADO = "Registrado"
    INVESTIGANDO = "Investigando"
    RESOLVIDO = "Resolvido"
    ARQUIVADO = "Arquivado"

class EventoMortalidade(db.Model):
    """Registro de eventos de mortalidade"""
    __tablename__ = 'evento_mortalidade'
    
    id_evento = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_hora_evento = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    id_ave = db.Column(db.String(36), db.ForeignKey('ave.id_ave'), nullable=True)  
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=False)
    id_setor = db.Column(db.String(36), db.ForeignKey('setor.id_setor'), nullable=False)
    
    numero_aves_mortas = db.Column(db.Integer, nullable=False, default=1)
    causa_mortalidade = db.Column(db.Enum(CausaMortalidade), nullable=False)
    descricao_adicional = db.Column(db.Text, nullable=True)
    sintomas_observados = db.Column(db.Text, nullable=True)
    
    status_evento = db.Column(db.Enum(StatusEventoMortalidade), default=StatusEventoMortalidade.REGISTRADO)
    requer_investigacao = db.Column(db.Boolean, default=False)
    medidas_tomadas = db.Column(db.Text, nullable=True)
    
    registrado_por = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    investigado_por = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=True)
    data_investigacao = db.Column(db.DateTime, nullable=True)
    
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    
    granja = db.relationship('Granjas', backref='eventos_mortalidade')
    ave = db.relationship('Aves', backref='eventos_mortalidade')
    lote = db.relationship('Lotes', backref='eventos_mortalidade')
    setor = db.relationship('Setores', backref='eventos_mortalidade')
    registrador = db.relationship('Usuarios', foreign_keys=[registrado_por], backref='eventos_registrados')
    investigador = db.relationship('Usuarios', foreign_keys=[investigado_por], backref='eventos_investigados')

    def to_dict(self):
        return {
            'id_evento': self.id_evento,
            'data_hora_evento': self.data_hora_evento.isoformat() if self.data_hora_evento else None,
            'id_ave': self.id_ave,
            'id_lote': self.id_lote,
            'id_setor': self.id_setor,
            'descricao_setor': self.setor.descricao_setor if self.setor else None,
            'numero_aves_mortas': self.numero_aves_mortas,
            'causa_mortalidade': self.causa_mortalidade.value if self.causa_mortalidade else None,
            'descricao_adicional': self.descricao_adicional,
            'sintomas_observados': self.sintomas_observados,
            'status_evento': self.status_evento.value if self.status_evento else None,
            'requer_investigacao': self.requer_investigacao,
            'medidas_tomadas': self.medidas_tomadas,
            'registrado_por': self.registrado_por,
            'nome_registrador': self.registrador.nome if self.registrador else None,
            'data_registro': self.data_registro.isoformat() if self.data_registro else None,
            'investigado_por': self.investigado_por,
            'nome_investigador': self.investigador.nome if self.investigador else None,
            'data_investigacao': self.data_investigacao.isoformat() if self.data_investigacao else None,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<EventoMortalidade {self.id_evento}>'

class ConfiguracaoAlertaMortalidade(db.Model):
    """Configurações de alertas de mortalidade por lote/setor"""
    __tablename__ = 'configuracao_alerta_mortalidade'
    
    id_configuracao = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=True)
    id_setor = db.Column(db.String(36), db.ForeignKey('setor.id_setor'), nullable=True)
    
    percentual_alerta_diario = db.Column(db.Numeric(5, 2), default=2.0)  
    percentual_alerta_semanal = db.Column(db.Numeric(5, 2), default=5.0)  
    percentual_alerta_mensal = db.Column(db.Numeric(5, 2), default=10.0) 
    
    ativo = db.Column(db.Boolean, default=True)
    criado_por = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    
    granja = db.relationship('Granjas', backref='configuracoes_alerta_mortalidade')
    lote = db.relationship('Lotes', backref='configuracoes_alerta')
    setor = db.relationship('Setores', backref='configuracoes_alerta')
    criador = db.relationship('Usuarios', backref='configuracoes_alerta_criadas')

    def to_dict(self):
        return {
            'id_configuracao': self.id_configuracao,
            'id_lote': self.id_lote,
            'id_setor': self.id_setor,
            'descricao_setor': self.setor.descricao_setor if self.setor else None,
            'percentual_alerta_diario': float(self.percentual_alerta_diario) if self.percentual_alerta_diario else 0,
            'percentual_alerta_semanal': float(self.percentual_alerta_semanal) if self.percentual_alerta_semanal else 0,
            'percentual_alerta_mensal': float(self.percentual_alerta_mensal) if self.percentual_alerta_mensal else 0,
            'ativo': self.ativo,
            'criado_por': self.criado_por,
            'nome_criador': self.criador.nome if self.criador else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<ConfiguracaoAlertaMortalidade {self.id_configuracao}>'

class RelatorioMortalidade(db.Model):
    """Relatórios consolidados de mortalidade"""
    __tablename__ = 'relatorio_mortalidade'
    
    id_relatorio = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tipo_periodo = db.Column(db.String(20), nullable=False)  
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=True)
    id_setor = db.Column(db.String(36), db.ForeignKey('setor.id_setor'), nullable=True)
    
    total_aves_mortas = db.Column(db.Integer, default=0)
    total_eventos = db.Column(db.Integer, default=0)
    total_aves_periodo = db.Column(db.Integer, default=0)  
    percentual_mortalidade = db.Column(db.Numeric(5, 2), default=0)
    
    dados_por_causa = db.Column(db.Text, nullable=True)  
    
    causa_predominante = db.Column(db.String(50), nullable=True)
    tendencia = db.Column(db.String(20), nullable=True)  
    alertas_gerados = db.Column(db.Integer, default=0)
    
    gerado_por = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    data_geracao = db.Column(db.DateTime, default=datetime.utcnow)
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)
    
    granja = db.relationship('Granjas', backref='relatorios_mortalidade')
    lote = db.relationship('Lotes', backref='relatorios_mortalidade')
    setor = db.relationship('Setores', backref='relatorios_mortalidade')
    responsavel = db.relationship('Usuarios', backref='relatorios_mortalidade_gerados')

    def to_dict(self):
        import json
        return {
            'id_relatorio': self.id_relatorio,
            'tipo_periodo': self.tipo_periodo,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'id_lote': self.id_lote,
            'id_setor': self.id_setor,
            'descricao_setor': self.setor.descricao_setor if self.setor else None,
            'total_aves_mortas': self.total_aves_mortas,
            'total_eventos': self.total_eventos,
            'total_aves_periodo': self.total_aves_periodo,
            'percentual_mortalidade': float(self.percentual_mortalidade) if self.percentual_mortalidade else 0,
            'dados_por_causa': json.loads(self.dados_por_causa) if self.dados_por_causa else {},
            'causa_predominante': self.causa_predominante,
            'tendencia': self.tendencia,
            'alertas_gerados': self.alertas_gerados,
            'gerado_por': self.gerado_por,
            'nome_responsavel': self.responsavel.nome if self.responsavel else None,
            'data_geracao': self.data_geracao.isoformat() if self.data_geracao else None,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<RelatorioMortalidade {self.id_relatorio}>'

class TipoRelatorioProducao(enum.Enum):
    DIARIO = "Diário"
    SEMANAL = "Semanal"
    MENSAL = "Mensal"
    ANUAL = "Anual"
    PERSONALIZADO = "Personalizado"

class RelatorioProducaoOvos(db.Model):
    """Relatórios consolidados de produção de ovos"""
    __tablename__ = 'relatorio_producao_ovos'
    
    id_relatorio = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    titulo = db.Column(db.String(200), nullable=False)
    tipo_relatorio = db.Column(db.Enum(TipoRelatorioProducao), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    id_lote = db.Column(db.String(36), db.ForeignKey('lote.id_lote'), nullable=True)
    id_setor = db.Column(db.String(36), db.ForeignKey('setor.id_setor'), nullable=True)
    
    total_ovos_produzidos = db.Column(db.Integer, default=0)
    total_ovos_quebrados = db.Column(db.Integer, default=0)
    total_ovos_aproveitaveis = db.Column(db.Integer, default=0)
    total_aves_ativas = db.Column(db.Integer, default=0)
    dias_producao = db.Column(db.Integer, default=0)
    
    taxa_producao_media = db.Column(db.Numeric(5, 2), default=0) 
    producao_diaria_media = db.Column(db.Numeric(10, 2), default=0)
    percentual_quebrados = db.Column(db.Numeric(5, 2), default=0)  
    eficiencia_producao = db.Column(db.Numeric(5, 2), default=0)  
    
    dados_por_qualidade = db.Column(db.Text, nullable=True) 
    
    tendencia_producao = db.Column(db.String(20), nullable=True) 
    melhor_dia_producao = db.Column(db.Date, nullable=True)
    pior_dia_producao = db.Column(db.Date, nullable=True)
    maior_producao_diaria = db.Column(db.Integer, default=0)
    menor_producao_diaria = db.Column(db.Integer, default=0)
    
    variacao_periodo_anterior = db.Column(db.Numeric(5, 2), nullable=True)  
    meta_producao = db.Column(db.Integer, nullable=True)
    percentual_meta_atingida = db.Column(db.Numeric(5, 2), nullable=True) 

    agrupamento = db.Column(db.String(50), nullable=True) 
    filtros_aplicados = db.Column(db.Text, nullable=True)  

    gerado_por = db.Column(db.String(36), db.ForeignKey('usuario.id_usuario'), nullable=False)
    data_geracao = db.Column(db.DateTime, default=datetime.utcnow)
    formato_exportacao = db.Column(db.String(20), nullable=True) 
    
    id_granja = db.Column(db.String(36), db.ForeignKey('granja.id_granja'), nullable=False)

    granja = db.relationship('Granjas', backref='relatorios_producao_ovos')
    lote = db.relationship('Lotes', backref='relatorios_producao_ovos')
    setor = db.relationship('Setores', backref='relatorios_producao_ovos')
    responsavel = db.relationship('Usuarios', backref='relatorios_producao_gerados')

    def to_dict(self):
        import json
        return {
            'id_relatorio': self.id_relatorio,
            'titulo': self.titulo,
            'tipo_relatorio': self.tipo_relatorio.value if self.tipo_relatorio else None,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'id_lote': self.id_lote,
            'id_setor': self.id_setor,
            'descricao_setor': self.setor.descricao_setor if self.setor else None,
            'total_ovos_produzidos': self.total_ovos_produzidos,
            'total_ovos_quebrados': self.total_ovos_quebrados,
            'total_ovos_aproveitaveis': self.total_ovos_aproveitaveis,
            'total_aves_ativas': self.total_aves_ativas,
            'dias_producao': self.dias_producao,
            'taxa_producao_media': float(self.taxa_producao_media) if self.taxa_producao_media else 0,
            'producao_diaria_media': float(self.producao_diaria_media) if self.producao_diaria_media else 0,
            'percentual_quebrados': float(self.percentual_quebrados) if self.percentual_quebrados else 0,
            'eficiencia_producao': float(self.eficiencia_producao) if self.eficiencia_producao else 0,
            'dados_por_qualidade': json.loads(self.dados_por_qualidade) if self.dados_por_qualidade else {},
            'tendencia_producao': self.tendencia_producao,
            'melhor_dia_producao': self.melhor_dia_producao.isoformat() if self.melhor_dia_producao else None,
            'pior_dia_producao': self.pior_dia_producao.isoformat() if self.pior_dia_producao else None,
            'maior_producao_diaria': self.maior_producao_diaria,
            'menor_producao_diaria': self.menor_producao_diaria,
            'variacao_periodo_anterior': float(self.variacao_periodo_anterior) if self.variacao_periodo_anterior else None,
            'meta_producao': self.meta_producao,
            'percentual_meta_atingida': float(self.percentual_meta_atingida) if self.percentual_meta_atingida else None,
            'agrupamento': self.agrupamento,
            'filtros_aplicados': json.loads(self.filtros_aplicados) if self.filtros_aplicados else {},
            'gerado_por': self.gerado_por,
            'nome_responsavel': self.responsavel.nome if self.responsavel else None,
            'data_geracao': self.data_geracao.isoformat() if self.data_geracao else None,
            'formato_exportacao': self.formato_exportacao,
            'id_granja': self.id_granja
        }

    def __repr__(self):
        return f'<RelatorioProducaoOvos {self.titulo}>'