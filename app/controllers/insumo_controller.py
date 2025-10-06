from app.models.database import InsumoNovo, MovimentacaoInsumo, Usuarios
from app.exceptions import BusinessError
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal

class InsumoController:
    
    @staticmethod
    def listar_todos(categoria: str = None, abaixo_minimo: bool = False, 
                    vencimento_dias: int = None, ativo: bool = True) -> List[InsumoNovo]:
        """Lista insumos com filtros opcionais"""
        query = InsumoNovo.select().where(InsumoNovo.ativo == ativo)
        
        if categoria:
            query = query.where(InsumoNovo.categoria == categoria)
            
        if abaixo_minimo:
            query = query.where(InsumoNovo.quantidade_atual < InsumoNovo.quantidade_minima)
            
        if vencimento_dias:
            data_limite = date.today() + timedelta(days=vencimento_dias)
            query = query.where(
                (InsumoNovo.data_validade.is_null(False)) & 
                (InsumoNovo.data_validade <= data_limite)
            )
        
        return list(query.order_by(InsumoNovo.nome))
    
    @staticmethod
    def buscar_por_id(id_insumo: int) -> Optional[InsumoNovo]:
        """Busca insumo por ID"""
        try:
            return InsumoNovo.get(InsumoNovo.id_insumo == id_insumo)
        except InsumoNovo.DoesNotExist:
            return None
    
    @staticmethod
    def criar_insumo(nome: str, categoria: str, unidade: str, quantidade_inicial: Decimal,
                    quantidade_minima: Decimal, data_validade: date = None, 
                    observacoes: str = None, usuario_id: int = None) -> InsumoNovo:
        """Cria um novo insumo com movimentação inicial"""
        try:
            # Validações
            if quantidade_inicial < 0:
                raise BusinessError("Quantidade inicial não pode ser negativa")
            
            if quantidade_minima < 0:
                raise BusinessError("Quantidade mínima não pode ser negativa")
            
            if data_validade and data_validade <= date.today():
                raise BusinessError("Data de validade deve ser futura")
            
            # Criar insumo
            insumo = InsumoNovo.create(
                nome=nome,
                categoria=categoria,
                unidade=unidade,
                quantidade_atual=quantidade_inicial,
                quantidade_minima=quantidade_minima,
                data_validade=data_validade,
                observacoes=observacoes,
                usuario_criacao=usuario_id
            )
            
            # Criar movimentação inicial se quantidade > 0
            if quantidade_inicial > 0:
                MovimentacaoInsumo.create(
                    insumo=insumo,
                    tipo='Entrada - Ajuste',
                    quantidade=quantidade_inicial,
                    observacoes='Estoque inicial',
                    usuarios=usuario_id,
                    estoque_anterior=0,
                    estoque_posterior=quantidade_inicial
                )
            
            return insumo
            
        except Exception as e:
            if isinstance(e, BusinessError):
                raise e
            raise BusinessError(f"Erro ao criar insumo: {str(e)}")
    
    @staticmethod
    def atualizar_insumo(id_insumo: int, nome: str, categoria: str, unidade: str,
                        quantidade_minima: Decimal, data_validade: date = None,
                        observacoes: str = None) -> InsumoNovo:
        """Atualiza metadados do insumo (não altera estoque)"""
        try:
            insumo = InsumoController.buscar_por_id(id_insumo)
            if not insumo:
                raise BusinessError("Insumo não encontrado")
            
            # Validações
            if quantidade_minima < 0:
                raise BusinessError("Quantidade mínima não pode ser negativa")
            
            # Atualizar dados
            insumo.nome = nome
            insumo.categoria = categoria
            insumo.unidade = unidade
            insumo.quantidade_minima = quantidade_minima
            insumo.data_validade = data_validade
            insumo.observacoes = observacoes
            insumo.save()
            
            return insumo
            
        except Exception as e:
            if isinstance(e, BusinessError):
                raise e
            raise BusinessError(f"Erro ao atualizar insumo: {str(e)}")
    
    @staticmethod
    def desativar_insumo(id_insumo: int) -> bool:
        """Soft delete - desativa o insumo"""
        try:
            insumo = InsumoController.buscar_por_id(id_insumo)
            if not insumo:
                raise BusinessError("Insumo não encontrado")
            
            insumo.ativo = False
            insumo.save()
            
            return True
            
        except Exception as e:
            if isinstance(e, BusinessError):
                raise e
            raise BusinessError(f"Erro ao desativar insumo: {str(e)}")
    
    @staticmethod
    def ativar_insumo(id_insumo: int) -> bool:
        """Reativa o insumo"""
        try:
            insumo = InsumoController.buscar_por_id(id_insumo)
            if not insumo:
                raise BusinessError("Insumo não encontrado")
            
            insumo.ativo = True
            insumo.save()
            
            return True
            
        except Exception as e:
            if isinstance(e, BusinessError):
                raise e
            raise BusinessError(f"Erro ao ativar insumo: {str(e)}")

class MovimentacaoInsumoController:
    
    @staticmethod
    def listar_movimentacoes(insumo_id: int = None, tipo: str = None, 
                           data_inicio: date = None, data_fim: date = None,
                           usuario_id: int = None) -> List[MovimentacaoInsumo]:
        """Lista movimentações com filtros opcionais"""
        query = MovimentacaoInsumo.select().join(InsumoNovo)
        
        if insumo_id:
            query = query.where(MovimentacaoInsumo.insumo == insumo_id)
        
        if tipo:
            query = query.where(MovimentacaoInsumo.tipo == tipo)
        
        if data_inicio:
            query = query.where(MovimentacaoInsumo.data_movimentacao >= data_inicio)
        
        if data_fim:
            query = query.where(MovimentacaoInsumo.data_movimentacao <= data_fim)
        
        if usuario_id:
            query = query.where(MovimentacaoInsumo.usuarios == usuario_id)
        
        return list(query.order_by(MovimentacaoInsumo.data_movimentacao.desc()))
    
    @staticmethod
    def criar_movimentacao(insumo_id: int, tipo: str, quantidade: Decimal,
                          data_movimentacao: date, observacoes: str = None,
                          usuario_id: int = None) -> MovimentacaoInsumo:
        """Cria nova movimentação e atualiza estoque"""
        try:
            insumo = InsumoController.buscar_por_id(insumo_id)
            if not insumo:
                raise BusinessError("Insumo não encontrado")
            
            if not insumo.ativo:
                raise BusinessError("Não é possível movimentar insumo inativo")
            
            # Validações
            if quantidade <= 0:
                raise BusinessError("Quantidade deve ser maior que zero")
            
            if data_movimentacao > date.today():
                raise BusinessError("Data da movimentação não pode ser futura")
            
            estoque_anterior = insumo.quantidade_atual
            
            # Calcular novo estoque
            if tipo.startswith('Entrada'):
                novo_estoque = estoque_anterior + quantidade
            elif tipo.startswith('Saída'):
                if estoque_anterior < quantidade:
                    raise BusinessError("Estoque insuficiente")
                novo_estoque = estoque_anterior - quantidade
            elif tipo == 'Entrada - Ajuste':
                # Para ajuste, a quantidade pode ser positiva ou negativa
                novo_estoque = quantidade
            else:
                raise BusinessError("Tipo de movimentação inválido")
            
            # Validações específicas
            if tipo == 'Saída - Perda' and not observacoes:
                raise BusinessError("Observação é obrigatória para perdas")
            
            # Criar movimentação
            movimentacao = MovimentacaoInsumo.create(
                insumo=insumo,
                tipo=tipo,
                quantidade=quantidade,
                data_movimentacao=data_movimentacao,
                observacoes=observacoes,
                usuarios=usuario_id,
                estoque_anterior=estoque_anterior,
                estoque_posterior=novo_estoque
            )
            
            # Atualizar estoque do insumo
            insumo.quantidade_atual = novo_estoque
            insumo.save()
            
            return movimentacao
            
        except Exception as e:
            if isinstance(e, BusinessError):
                raise e
            raise BusinessError(f"Erro ao criar movimentação: {str(e)}")