from app.models.database import EstoqueVacina
from app.exceptions import BusinessError
from typing import List, Optional
from datetime import date

class EstoqueVacinaController:
    
    @staticmethod
    def listar_todos() -> List[EstoqueVacina]:
        """Lista todos os estoques de vacina"""
        return list(EstoqueVacina.select())  
    
    @staticmethod
    def buscar_por_id(id_estoque_vacina: int) -> Optional[EstoqueVacina]:
        """Busca estoque por ID"""
        try:
            return EstoqueVacina.get(EstoqueVacina.id_estoque_vacina == id_estoque_vacina)
        except EstoqueVacina.DoesNotExist:
            return None
    
    @staticmethod
    def criar_estoque_vacina(tipo_vacina: str, fabricante: str, lote_vacina: str,
                           data_validade: date, quantidade_doses: int,
                           data_entrada: date, observacoes: str = None) -> EstoqueVacina:
        """Cria um novo estoque de vacina"""
        try:
            # Validações
            if quantidade_doses <= 0:
                raise BusinessError("Quantidade de doses deve ser maior que zero")
            
            if data_validade <= date.today():
                raise BusinessError("Data de validade deve ser futura")
            
            # Criar estoque usando Peewee
            estoque = EstoqueVacina.create(
                tipo_vacina=tipo_vacina,
                fabricante=fabricante,
                lote_vacina=lote_vacina,
                data_validade=data_validade,
                quantidade_doses=quantidade_doses,
                data_entrada=data_entrada,
                observacoes=observacoes
            )
            
            return estoque
            
        except Exception as e:
            if isinstance(e, BusinessError):
                raise e
            raise BusinessError(f"Erro ao criar estoque de vacina: {str(e)}")
    
    @staticmethod
    def atualizar(id_estoque_vacina: int, tipo_vacina: str, fabricante: str,
                 lote_vacina: str, data_validade: date, quantidade_doses: int,
                 data_entrada: date, observacoes: str = None) -> EstoqueVacina:
        """Atualiza um estoque de vacina"""
        try:
            estoque = EstoqueVacinaController.buscar_por_id(id_estoque_vacina)
            if not estoque:
                raise BusinessError("Estoque de vacina não encontrado")
            
            # Validações
            if quantidade_doses <= 0:
                raise BusinessError("Quantidade de doses deve ser maior que zero")
            
            # Atualizar dados usando Peewee
            estoque.tipo_vacina = tipo_vacina
            estoque.fabricante = fabricante
            estoque.lote_vacina = lote_vacina
            estoque.data_validade = data_validade
            estoque.quantidade_doses = quantidade_doses
            estoque.data_entrada = data_entrada
            estoque.observacoes = observacoes
            estoque.save() 
            
            return estoque
            
        except Exception as e:
            if isinstance(e, BusinessError):
                raise e
            raise BusinessError(f"Erro ao atualizar estoque: {str(e)}")
    
    @staticmethod
    def excluir(id_estoque_vacina: int) -> bool:
        """Exclui um estoque de vacina"""
        try:
            estoque = EstoqueVacinaController.buscar_por_id(id_estoque_vacina)
            if not estoque:
                raise BusinessError("Estoque de vacina não encontrado")
            
            estoque.delete_instance() 
            
            return True
            
        except Exception as e:
            if isinstance(e, BusinessError):
                raise e
            raise BusinessError(f"Erro ao excluir estoque: {str(e)}")
    
    @staticmethod
    def buscar_por_tipo(tipo_vacina: str) -> List[EstoqueVacina]:
        """Busca estoques por tipo de vacina"""
        return list(EstoqueVacina.select().where(EstoqueVacina.tipo_vacina == tipo_vacina))
    
    @staticmethod
    def listar_vencendo(dias: int = 30) -> List[EstoqueVacina]:
        """Lista estoques que vencem em X dias"""
        from datetime import timedelta
        data_limite = date.today() + timedelta(days=dias)
        
        return list(EstoqueVacina.select().where(EstoqueVacina.data_validade <= data_limite))
    
    @staticmethod
    def listar_baixo_estoque(quantidade_minima: int = 10) -> List[EstoqueVacina]:
        """Lista estoques com quantidade baixa"""
        return list(EstoqueVacina.select().where(EstoqueVacina.quantidade_doses <= quantidade_minima))