from models import db, ProducaoOvos, HistoricoProducaoOvos, RelatorioProducao, QualidadeOvo, StatusProducao, Setores, Lotes, Usuarios
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.exc import IntegrityError
import json
from decimal import Decimal

class ProducaoService:
    
    @staticmethod
    def criar_producao(data, usuario_id, ip_address=None):
        """Criar novo registro de produção"""
        try:
            data_producao = data.get('data_producao', date.today())
            if isinstance(data_producao, str):
                data_producao = datetime.strptime(data_producao, '%Y-%m-%d').date()
            
            
            existing = ProducaoOvos.query.filter(
                and_(
                    ProducaoOvos.data_producao == data_producao,
                    ProducaoOvos.id_setor == data['id_setor'],
                    ProducaoOvos.id_lote == data.get('id_lote'),
                    ProducaoOvos.status != StatusProducao.CANCELADO
                )
            ).first()
            
            if existing:
                return None, "Já existe registro de produção para este setor/lote na data informada"
            
        
            producao = ProducaoOvos(
                data_producao=data_producao,
                id_setor=data['id_setor'],
                id_lote=data.get('id_lote'),
                quantidade_ovos_produzidos=data['quantidade_ovos_produzidos'],
                numero_aves_ativas=data['numero_aves_ativas'],
                ovos_quebrados_danificados=data.get('ovos_quebrados_danificados', 0),
                qualidade_ovos=QualidadeOvo(data['qualidade_ovos']) if data.get('qualidade_ovos') else None,
                operador_responsavel=usuario_id,
                observacoes=data.get('observacoes'),
                id_granja=data['id_granja']
            )
            
      
            producao.calcular_metricas()
            
            db.session.add(producao)
            db.session.flush()  
            
          
            ProducaoService._registrar_historico(
                producao.id_producao_ovos,
                'CREATE',
                None,
                producao.to_dict(),
                usuario_id,
                ip_address,
                'Criação inicial do registro'
            )
            
            db.session.commit()
            return producao, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def listar_producoes(id_granja, filtros=None):
        """Listar produções com filtros"""
        try:
            query = ProducaoOvos.query.filter(
                and_(
                    ProducaoOvos.id_granja == id_granja,
                    ProducaoOvos.status != StatusProducao.CANCELADO
                )
            )
            
            if filtros:
               
                if filtros.get('data_inicio'):
                    data_inicio = datetime.strptime(filtros['data_inicio'], '%Y-%m-%d').date()
                    query = query.filter(ProducaoOvos.data_producao >= data_inicio)
                
                if filtros.get('data_fim'):
                    data_fim = datetime.strptime(filtros['data_fim'], '%Y-%m-%d').date()
                    query = query.filter(ProducaoOvos.data_producao <= data_fim)
                
               
                if filtros.get('id_setor'):
                    query = query.filter(ProducaoOvos.id_setor == filtros['id_setor'])
                
               
                if filtros.get('id_lote'):
                    query = query.filter(ProducaoOvos.id_lote == filtros['id_lote'])
                
               
                if filtros.get('operador_responsavel'):
                    query = query.filter(ProducaoOvos.operador_responsavel == filtros['operador_responsavel'])
                
               
                if filtros.get('qualidade_ovos'):
                    query = query.filter(ProducaoOvos.qualidade_ovos == QualidadeOvo(filtros['qualidade_ovos']))
            
            return query.order_by(desc(ProducaoOvos.data_producao)).all()
            
        except Exception as e:
            return []
    
    @staticmethod
    def obter_producao(id_producao, id_granja):
        """Obter produção específica"""
        return ProducaoOvos.query.filter(
            and_(
                ProducaoOvos.id_producao_ovos == id_producao,
                ProducaoOvos.id_granja == id_granja,
                ProducaoOvos.status != StatusProducao.CANCELADO
            )
        ).first()
    
    @staticmethod
    def atualizar_producao(id_producao, data, usuario_id, ip_address=None, motivo=None):
        """Atualizar registro de produção"""
        try:
            producao = ProducaoOvos.query.get(id_producao)
            if not producao:
                return None, "Registro de produção não encontrado"
            
            if producao.status == StatusProducao.CANCELADO:
                return None, "Não é possível alterar um registro cancelado"
            

            dados_anteriores = producao.to_dict()
            

            campos_atualizaveis = [
                'quantidade_ovos_produzidos', 'numero_aves_ativas', 
                'ovos_quebrados_danificados', 'qualidade_ovos', 'observacoes'
            ]
            
            for campo in campos_atualizaveis:
                if campo in data:
                    if campo == 'qualidade_ovos' and data[campo]:
                        setattr(producao, campo, QualidadeOvo(data[campo]))
                    else:
                        setattr(producao, campo, data[campo])
            

            producao.calcular_metricas()
            producao.updated_by = usuario_id
            producao.updated_at = datetime.utcnow()
            producao.status = StatusProducao.REVISADO
            

            dados_novos = producao.to_dict()
            

            ProducaoService._registrar_historico(
                id_producao,
                'UPDATE',
                dados_anteriores,
                dados_novos,
                usuario_id,
                ip_address,
                motivo or 'Atualização de dados'
            )
            
            db.session.commit()
            return producao, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def cancelar_producao(id_producao, usuario_id, motivo, ip_address=None):
        """Cancelar registro de produção"""
        try:
            producao = ProducaoOvos.query.get(id_producao)
            if not producao:
                return False, "Registro de produção não encontrado"
            
            dados_anteriores = producao.to_dict()
            
            producao.status = StatusProducao.CANCELADO
            producao.updated_by = usuario_id
            producao.updated_at = datetime.utcnow()

            ProducaoService._registrar_historico(
                id_producao,
                'CANCEL',
                dados_anteriores,
                None,
                usuario_id,
                ip_address,
                motivo
            )
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    @staticmethod
    def _registrar_historico(id_producao, acao, dados_anteriores, dados_novos, usuario_id, ip_address, motivo):
        """Registrar alteração no histórico"""
        historico = HistoricoProducaoOvos(
            id_producao_ovos=id_producao,
            acao=acao,
            dados_anteriores=json.dumps(dados_anteriores) if dados_anteriores else None,
            dados_novos=json.dumps(dados_novos) if dados_novos else None,
            motivo_alteracao=motivo,
            usuario_acao=usuario_id,
            ip_address=ip_address
        )
        db.session.add(historico)
    
    @staticmethod
    def obter_historico(id_producao):
        """Obter histórico de alterações"""
        return HistoricoProducaoOvos.query.filter(
            HistoricoProducaoOvos.id_producao_ovos == id_producao
        ).order_by(desc(HistoricoProducaoOvos.data_acao)).all()
    
    @staticmethod
    def gerar_relatorio_periodo(id_granja, data_inicio, data_fim, tipo_periodo, id_setor=None, id_lote=None, usuario_id=None):
        """Gerar relatório consolidado de período"""
        try:
            if isinstance(data_inicio, str):
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            if isinstance(data_fim, str):
                data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
            query = db.session.query(
                func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_ovos'),
                func.sum(ProducaoOvos.ovos_quebrados_danificados).label('total_quebrados'),
                func.sum(ProducaoOvos.ovos_aproveitaveis).label('total_aproveitaveis'),
                func.avg(ProducaoOvos.numero_aves_ativas).label('media_aves'),
                func.avg(ProducaoOvos.taxa_producao).label('taxa_media'),
                func.count(ProducaoOvos.id_producao_ovos).label('dias_registrados')
            ).filter(
                and_(
                    ProducaoOvos.id_granja == id_granja,
                    ProducaoOvos.data_producao >= data_inicio,
                    ProducaoOvos.data_producao <= data_fim,
                    ProducaoOvos.status != StatusProducao.CANCELADO
                )
            )
            
            if id_setor:
                query = query.filter(ProducaoOvos.id_setor == id_setor)
            if id_lote:
                query = query.filter(ProducaoOvos.id_lote == id_lote)
            
            resultado = query.first()

            relatorio = RelatorioProducao(
                tipo_periodo=tipo_periodo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                id_setor=id_setor,
                id_lote=id_lote,
                total_ovos_produzidos=resultado.total_ovos or 0,
                total_ovos_quebrados=resultado.total_quebrados or 0,
                total_ovos_aproveitaveis=resultado.total_aproveitaveis or 0,
                media_aves_ativas=resultado.media_aves or 0,
                taxa_producao_media=resultado.taxa_media or 0,
                dias_registrados=resultado.dias_registrados or 0,
                gerado_por=usuario_id,
                id_granja=id_granja
            )
            
            db.session.add(relatorio)
            db.session.commit()
            
            return relatorio, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def obter_estatisticas_dashboard(id_granja, dias=30):
        """Estatísticas para dashboard"""
        try:
            data_limite = date.today() - timedelta(days=dias)

            query_periodo = db.session.query(
                func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_ovos'),
                func.sum(ProducaoOvos.ovos_quebrados_danificados).label('total_quebrados'),
                func.avg(ProducaoOvos.taxa_producao).label('taxa_media')
            ).filter(
                and_(
                    ProducaoOvos.id_granja == id_granja,
                    ProducaoOvos.data_producao >= data_limite,
                    ProducaoOvos.status != StatusProducao.CANCELADO
                )
            ).first()
            
            query_hoje = db.session.query(
                func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('ovos_hoje'),
                func.count(ProducaoOvos.id_producao_ovos).label('registros_hoje')
            ).filter(
                and_(
                    ProducaoOvos.id_granja == id_granja,
                    ProducaoOvos.data_producao == date.today(),
                    ProducaoOvos.status != StatusProducao.CANCELADO
                )
            ).first()

            setores_produtivos = db.session.query(
                Setores.descricao_setor,
                func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_producao')
            ).join(ProducaoOvos).filter(
                and_(
                    ProducaoOvos.id_granja == id_granja,
                    ProducaoOvos.data_producao >= data_limite,
                    ProducaoOvos.status != StatusProducao.CANCELADO
                )
            ).group_by(Setores.id_setor).order_by(desc('total_producao')).limit(5).all()
            
            return {
                'periodo': {
                    'total_ovos': query_periodo.total_ovos or 0,
                    'total_quebrados': query_periodo.total_quebrados or 0,
                    'taxa_media': float(query_periodo.taxa_media or 0),
                    'dias_analisados': dias
                },
                'hoje': {
                    'ovos_produzidos': query_hoje.ovos_hoje or 0,
                    'registros_realizados': query_hoje.registros_hoje or 0
                },
                'setores_produtivos': [
                    {
                        'setor': setor.descricao_setor,
                        'total_producao': setor.total_producao
                    } for setor in setores_produtivos
                ]
            }
            
        except Exception as e:
            return None
    
    @staticmethod
    def obter_dados_graficos(id_granja, data_inicio, data_fim, tipo_agrupamento='diario'):
        """Obter dados para gráficos"""
        try:
            if isinstance(data_inicio, str):
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            if isinstance(data_fim, str):
                data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            
            if tipo_agrupamento == 'diario':
                dados = db.session.query(
                    ProducaoOvos.data_producao,
                    func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_ovos'),
                    func.sum(ProducaoOvos.ovos_quebrados_danificados).label('total_quebrados'),
                    func.avg(ProducaoOvos.taxa_producao).label('taxa_media')
                ).filter(
                    and_(
                        ProducaoOvos.id_granja == id_granja,
                        ProducaoOvos.data_producao >= data_inicio,
                        ProducaoOvos.data_producao <= data_fim,
                        ProducaoOvos.status != StatusProducao.CANCELADO
                    )
                ).group_by(ProducaoOvos.data_producao).order_by(ProducaoOvos.data_producao).all()
                
                return [{
                    'data': item.data_producao.isoformat(),
                    'total_ovos': item.total_ovos,
                    'total_quebrados': item.total_quebrados,
                    'taxa_producao': float(item.taxa_media or 0)
                } for item in dados]
            
            elif tipo_agrupamento == 'semanal':
                dados = db.session.query(
                    func.date_trunc('week', ProducaoOvos.data_producao).label('semana'),
                    func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_ovos'),
                    func.sum(ProducaoOvos.ovos_quebrados_danificados).label('total_quebrados'),
                    func.avg(ProducaoOvos.taxa_producao).label('taxa_media')
                ).filter(
                    and_(
                        ProducaoOvos.id_granja == id_granja,
                        ProducaoOvos.data_producao >= data_inicio,
                        ProducaoOvos.data_producao <= data_fim,
                        ProducaoOvos.status != StatusProducao.CANCELADO
                    )
                ).group_by('semana').order_by('semana').all()
                
                return [{
                    'periodo': item.semana.isoformat(),
                    'total_ovos': item.total_ovos,
                    'total_quebrados': item.total_quebrados,
                    'taxa_producao': float(item.taxa_media or 0)
                } for item in dados]
            
            return []
            
        except Exception as e:
            return []