from datetime import datetime, timedelta
from typing import List, Optional
from app.models.database import Producao, Lote
from peewee import fn, JOIN
from app.exceptions import BusinessError

class ProducaoController:
    @staticmethod
    def criar_producao(lote_id: str, data_coleta: datetime, quantidade_aves: int,  # ✅ CORRIGIDO: int → str
                      quantidade_ovos: int, qualidade_producao: str,
                      producao_nao_aproveitada: int, responsavel: str, observacoes: str = None) -> Producao:
       
        if quantidade_aves <= 0:
            raise BusinessError("quantidade_aves deve ser maior que zero")
        if quantidade_ovos < 0 or producao_nao_aproveitada < 0:
            raise BusinessError("quantidades não podem ser negativas")
        if quantidade_ovos > quantidade_aves:
            raise BusinessError("quantidade_ovos não pode ser maior que quantidade_aves")

        try:
            return Producao.create(
                id_lote=lote_id,  # ✅ JÁ ESTAVA CORRETO
                data_coleta=data_coleta,
                quantidade_aves=quantidade_aves,
                quantidade_ovos=quantidade_ovos,
                qualidade_producao=qualidade_producao,
                producao_nao_aproveitada=producao_nao_aproveitada,
                responsavel=responsavel,
                observacoes=observacoes
            )
        except Exception as e:
            raise Exception(f'Erro ao criar registro de produção: {str(e)}')

    @staticmethod
    def excluir_producao(producao_id: int) -> bool:
        try:
            query = Producao.delete().where(Producao.id_producao == producao_id)
            return query.execute() > 0
        except Exception as e:
            raise Exception(f'Erro ao excluir produção: {str(e)}')

    @staticmethod
    def buscar_por_id(producao_id: int) -> Optional[Producao]:
        return Producao.get_or_none(Producao.id_producao == producao_id)

    @staticmethod
    def listar_todos() -> List[Producao]:
        return list(Producao.select().order_by(Producao.data_coleta.desc()))

    @staticmethod
    def listar_por_lote(lote_id: str) -> List[Producao]:  # ✅ CORRIGIDO: int → str
        return list(Producao.select().where(Producao.id_lote == lote_id))  # ✅ CORRIGIDO: lote_id → id_lote

    @staticmethod
    def atualizar(producao_id: int, **kwargs) -> bool:
        try:
            query = Producao.update(**kwargs).where(Producao.id_producao == producao_id)
            return query.execute() > 0
        except Exception as e:
            raise Exception(f'Erro ao atualizar produção: {str(e)}')

    @staticmethod
    def deletar(producao_id: int) -> bool:
        try:
            query = Producao.delete().where(Producao.id_producao == producao_id)
            return query.execute() > 0
        except Exception as e:
            raise Exception(f'Erro ao deletar produção: {str(e)}')

    @staticmethod
    def calcular_estatisticas_periodo(data_inicio: datetime, data_fim: datetime) -> dict:
        producoes = (Producao
                    .select()
                    .where(
                        (Producao.data_coleta >= data_inicio) &
                        (Producao.data_coleta <= data_fim)
                    ))
        
        total_produzido = sum(p.quantidade_ovos for p in producoes)
        total_perdas = sum(p.producao_nao_aproveitada for p in producoes)
        dias_periodo = (data_fim - data_inicio).days or 1

        return {
            'total_produzido': total_produzido,
            'media_diaria': total_produzido / dias_periodo,
            'total_perdas': total_perdas,
            'taxa_aproveitamento': ((total_produzido - total_perdas) / total_produzido * 100) if total_produzido > 0 else 0
        }

    @staticmethod
    def buscar_melhores_lotes(limite: int = 5) -> List[dict]:
        query = (Producao
                .select(
                    Producao.id_lote,  # ✅ CORRIGIDO: lote_id → id_lote
                    fn.SUM(Producao.quantidade_ovos).alias('total_producao'),
                    fn.AVG(Producao.quantidade_ovos).alias('media_diaria')
                )
                .group_by(Producao.id_lote)  # ✅ CORRIGIDO: lote_id → id_lote
                .order_by(fn.SUM(Producao.quantidade_ovos).desc())
                .limit(limite))
        
        return [{
            'lote_id': prod.id_lote,  # ✅ CORRIGIDO: lote_id → id_lote
            'total_producao': int(prod.total_producao),
            'media_diaria': round(float(prod.media_diaria), 2)
        } for prod in query]

    @staticmethod
    def verificar_baixa_producao(limite_percentual: float = 20.0) -> List[dict]:
        media_geral = (Producao
                      .select(fn.AVG(Producao.quantidade_ovos))
                      .scalar())
        
        if not media_geral:
            return []

        limite_inferior = media_geral * (1 - limite_percentual/100)
        
        query = (Producao
                .select()
                .where(Producao.quantidade_ovos < limite_inferior)
                .order_by(Producao.data_coleta.desc()))

        return [{
            'id_producao': p.id_producao,
            'lote_id': p.id_lote,  # ✅ CORRIGIDO: lote_id → id_lote
            'data': p.data_coleta,
            'quantidade': p.quantidade_ovos,
            'percentual_abaixo': round((1 - p.quantidade_ovos/media_geral) * 100, 2)
        } for p in query]