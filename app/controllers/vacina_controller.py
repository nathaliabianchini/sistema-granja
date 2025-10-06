from typing import List, Optional
from app.models.database import Vacinacao, TipoVacina  
from app.exceptions import BusinessError
from datetime import datetime, date

class VacinaController:  
    
    @staticmethod
    def criar_vacina(data_aplicacao: date, responsavel: str, tipo_vacina: str,
                    id_lote: str, quantidade_aves: int, observacoes: str = None) -> Vacinacao:
        
        if quantidade_aves <= 0:
            raise BusinessError("Quantidade de aves deve ser maior que zero")
            
        try:
            return Vacinacao.create(
                data_aplicacao=data_aplicacao,
                responsavel=responsavel,
                tipo_vacina=tipo_vacina,
                id_lote=id_lote,
                quantidade_aves=quantidade_aves,
                observacoes=observacoes
            )
        except Exception as e:
            raise Exception(f'Erro ao criar registro de vacinação: {str(e)}')

    @staticmethod
    def listar_todos() -> List[Vacinacao]:
        return list(Vacinacao.select().order_by(Vacinacao.data_aplicacao.desc()))

    @staticmethod
    def buscar_por_id(id_vacinacao: int) -> Optional[Vacinacao]:
        return Vacinacao.get_or_none(Vacinacao.id_vacinacao == id_vacinacao)

    @staticmethod
    def atualizar(id_vacinacao: int, **kwargs) -> bool:
        try:
            query = Vacinacao.update(**kwargs).where(Vacinacao.id_vacinacao == id_vacinacao)
            return query.execute() > 0
        except Exception as e:
            raise Exception(f'Erro ao atualizar vacinação: {str(e)}')

    @staticmethod
    def excluir(id_vacinacao: int) -> bool:
        try:
            query = Vacinacao.delete().where(Vacinacao.id_vacinacao == id_vacinacao)
            return query.execute() > 0
        except Exception as e:
            raise Exception(f'Erro ao excluir vacinação: {str(e)}')

    @staticmethod
    def listar_por_lote(id_lote: str) -> List[Vacinacao]:
        return list(Vacinacao.select().where(Vacinacao.id_lote == id_lote)
                   .order_by(Vacinacao.data_aplicacao.desc()))

    @staticmethod
    def listar_por_tipo_vacina(tipo_vacina: str) -> List[Vacinacao]:
        return list(Vacinacao.select().where(Vacinacao.tipo_vacina == tipo_vacina)
                   .order_by(Vacinacao.data_aplicacao.desc()))

    @staticmethod
    def listar_por_periodo(data_inicio: date, data_fim: date) -> List[Vacinacao]:
        return list(Vacinacao.select().where(
            (Vacinacao.data_aplicacao >= data_inicio) &
            (Vacinacao.data_aplicacao <= data_fim)
        ).order_by(Vacinacao.data_aplicacao.desc()))