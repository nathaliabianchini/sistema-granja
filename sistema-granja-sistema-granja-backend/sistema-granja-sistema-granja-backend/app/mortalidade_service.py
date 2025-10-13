from models import (db, EventoMortalidade, ConfiguracaoAlertaMortalidade, RelatorioMortalidade,
                   CausaMortalidade, StatusEventoMortalidade, Lotes, Setores, Usuarios, Avisos, CategoriaNotificacao, PrioridadeNotificacao)
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, desc
from decimal import Decimal
import json

class MortalidadeService:
    
    @staticmethod
    def registrar_evento_mortalidade(data, usuario_id):
        """Registrar evento de mortalidade"""
        try:
            data_hora_evento = data.get('data_hora_evento', datetime.utcnow())
            if isinstance(data_hora_evento, str):
                data_hora_evento = datetime.fromisoformat(data_hora_evento.replace('Z', '+00:00'))
            
            evento = EventoMortalidade(
                data_hora_evento=data_hora_evento,
                id_ave=data.get('id_ave'),
                id_lote=data['id_lote'],
                id_setor=data['id_setor'],
                numero_aves_mortas=data.get('numero_aves_mortas', 1),
                causa_mortalidade=CausaMortalidade(data['causa_mortalidade']),
                descricao_adicional=data.get('descricao_adicional'),
                sintomas_observados=data.get('sintomas_observados'),
                registrado_por=usuario_id,
                id_granja=data['id_granja']
            )
            
            db.session.add(evento)
            db.session.flush()  
            
            alertas_gerados = MortalidadeService._verificar_alertas_mortalidade(evento)
            if alertas_gerados:
                evento.requer_investigacao = True
            
            db.session.commit()
            
            return evento, alertas_gerados
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def _verificar_alertas_mortalidade(evento):
        """Verificar alertas de mortalidade e gerar notificações"""
        try:
            alertas_gerados = []
            
            config = ConfiguracaoAlertaMortalidade.query.filter(
                or_(
                    and_(ConfiguracaoAlertaMortalidade.id_lote == evento.id_lote,
                         ConfiguracaoAlertaMortalidade.ativo == True),
                    and_(ConfiguracaoAlertaMortalidade.id_setor == evento.id_setor,
                         ConfiguracaoAlertaMortalidade.ativo == True)
                )
            ).first()
            
            if not config:
                config_padrao = {
                    'percentual_alerta_diario': 2.0,
                    'percentual_alerta_semanal': 5.0,
                    'percentual_alerta_mensal': 10.0
                }
            else:
                config_padrao = {
                    'percentual_alerta_diario': float(config.percentual_alerta_diario),
                    'percentual_alerta_semanal': float(config.percentual_alerta_semanal),
                    'percentual_alerta_mensal': float(config.percentual_alerta_mensal)
                }
            
            lote = Lotes.query.get(evento.id_lote)
            if not lote:
                return alertas_gerados
            
            total_aves_lote = lote.quantidade_ave
            if total_aves_lote <= 0:
                return alertas_gerados
            
            hoje = date.today()
            mortalidade_hoje = db.session.query(
                func.sum(EventoMortalidade.numero_aves_mortas)
            ).filter(
                and_(
                    EventoMortalidade.id_lote == evento.id_lote,
                    func.date(EventoMortalidade.data_hora_evento) == hoje
                )
            ).scalar() or 0
            
            percentual_diario = (mortalidade_hoje / total_aves_lote) * 100
            
            if percentual_diario >= config_padrao['percentual_alerta_diario']:
                MortalidadeService._criar_alerta_mortalidade(
                    evento, 
                    'DIARIO',
                    percentual_diario,
                    config_padrao['percentual_alerta_diario'],
                    mortalidade_hoje
                )
                alertas_gerados.append('DIARIO')
            
            data_semana = hoje - timedelta(days=7)
            mortalidade_semanal = db.session.query(
                func.sum(EventoMortalidade.numero_aves_mortas)
            ).filter(
                and_(
                    EventoMortalidade.id_lote == evento.id_lote,
                    func.date(EventoMortalidade.data_hora_evento) >= data_semana
                )
            ).scalar() or 0
            
            percentual_semanal = (mortalidade_semanal / total_aves_lote) * 100
            
            if percentual_semanal >= config_padrao['percentual_alerta_semanal']:
                MortalidadeService._criar_alerta_mortalidade(
                    evento,
                    'SEMANAL',
                    percentual_semanal,
                    config_padrao['percentual_alerta_semanal'],
                    mortalidade_semanal
                )
                alertas_gerados.append('SEMANAL')
            
            data_mes = hoje - timedelta(days=30)
            mortalidade_mensal = db.session.query(
                func.sum(EventoMortalidade.numero_aves_mortas)
            ).filter(
                and_(
                    EventoMortalidade.id_lote == evento.id_lote,
                    func.date(EventoMortalidade.data_hora_evento) >= data_mes
                )
            ).scalar() or 0
            
            percentual_mensal = (mortalidade_mensal / total_aves_lote) * 100
            
            if percentual_mensal >= config_padrao['percentual_alerta_mensal']:
                MortalidadeService._criar_alerta_mortalidade(
                    evento,
                    'MENSAL',
                    percentual_mensal,
                    config_padrao['percentual_alerta_mensal'],
                    mortalidade_mensal
                )
                alertas_gerados.append('MENSAL')
            
            return alertas_gerados
            
        except Exception as e:
            return []
    
    @staticmethod
    def _criar_alerta_mortalidade(evento, periodo, percentual_atual, percentual_limite, total_mortes):
        """Criar alerta/notificação de mortalidade alta"""
        try:
            titulo = f"ALERTA: Mortalidade {periodo.lower()} elevada"
            
            conteudo = f"""
            Mortalidade {periodo.lower()} acima do limite configurado:
            
            Lote: {evento.lote.id_lote if evento.lote else 'N/A'}
            Setor: {evento.setor.descricao_setor if evento.setor else 'N/A'}
            
            Mortalidade atual: {percentual_atual:.2f}%
            Limite configurado: {percentual_limite:.2f}%
            Total de mortes no período: {total_mortes}
            
            Última causa registrada: {evento.causa_mortalidade.value}
            
            Investigação imediata recomendada.
            """
            
            aviso = Avisos(
                titulo=titulo,
                conteudo=conteudo,
                categoria=CategoriaNotificacao.GERAL,
                prioridade=PrioridadeNotificacao.CRITICA if percentual_atual >= percentual_limite * 2 else PrioridadeNotificacao.ALTA,
                criado_por=evento.registrado_por
            )
            
            db.session.add(aviso)
            
        except Exception as e:
            pass 
    
    @staticmethod
    def listar_eventos_mortalidade(id_granja, filtros=None):
        """Listar eventos de mortalidade com filtros"""
        try:
            query = EventoMortalidade.query.filter(EventoMortalidade.id_granja == id_granja)
            
            if filtros:
                if filtros.get('data_inicio'):
                    data_inicio = datetime.strptime(filtros['data_inicio'], '%Y-%m-%d')
                    query = query.filter(EventoMortalidade.data_hora_evento >= data_inicio)
                
                if filtros.get('data_fim'):
                    data_fim = datetime.strptime(filtros['data_fim'], '%Y-%m-%d')
                    data_fim = data_fim.replace(hour=23, minute=59, second=59)
                    query = query.filter(EventoMortalidade.data_hora_evento <= data_fim)
                
                if filtros.get('id_lote'):
                    query = query.filter(EventoMortalidade.id_lote == filtros['id_lote'])
                
                if filtros.get('id_setor'):
                    query = query.filter(EventoMortalidade.id_setor == filtros['id_setor'])
                
                if filtros.get('causa_mortalidade'):
                    query = query.filter(EventoMortalidade.causa_mortalidade == CausaMortalidade(filtros['causa_mortalidade']))
                
                if filtros.get('status_evento'):
                    query = query.filter(EventoMortalidade.status_evento == StatusEventoMortalidade(filtros['status_evento']))
                
                if filtros.get('requer_investigacao') == 'true':
                    query = query.filter(EventoMortalidade.requer_investigacao == True)
            
            return query.order_by(desc(EventoMortalidade.data_hora_evento)).all()
            
        except Exception as e:
            return []
    
    @staticmethod
    def gerar_relatorio_mortalidade(id_granja, data_inicio, data_fim, tipo_periodo, filtros=None, usuario_id=None):
        """Gerar relatório consolidado de mortalidade"""
        try:
            if isinstance(data_inicio, str):
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            if isinstance(data_fim, str):
                data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            
            query = EventoMortalidade.query.filter(
                and_(
                    EventoMortalidade.id_granja == id_granja,
                    func.date(EventoMortalidade.data_hora_evento) >= data_inicio,
                    func.date(EventoMortalidade.data_hora_evento) <= data_fim
                )
            )
            
            if filtros:
                if filtros.get('id_lote'):
                    query = query.filter(EventoMortalidade.id_lote == filtros['id_lote'])
                if filtros.get('id_setor'):
                    query = query.filter(EventoMortalidade.id_setor == filtros['id_setor'])
                if filtros.get('causa_mortalidade'):
                    query = query.filter(EventoMortalidade.causa_mortalidade == CausaMortalidade(filtros['causa_mortalidade']))
            
            eventos = query.all()
            
            total_aves_mortas = sum(evento.numero_aves_mortas for evento in eventos)
            total_eventos = len(eventos)
            
            if filtros and filtros.get('id_lote'):
                lote = Lotes.query.get(filtros['id_lote'])
                total_aves_periodo = lote.quantidade_ave if lote else 0
            else:
                lotes_envolvidos = set(evento.id_lote for evento in eventos)
                total_aves_periodo = sum(
                    lote.quantidade_ave for lote in Lotes.query.filter(Lotes.id_lote.in_(lotes_envolvidos)).all()
                ) if lotes_envolvidos else 0
            
            percentual_mortalidade = (total_aves_mortas / total_aves_periodo * 100) if total_aves_periodo > 0 else 0
            
            dados_por_causa = {}
            for causa in CausaMortalidade:
                count = sum(evento.numero_aves_mortas for evento in eventos if evento.causa_mortalidade == causa)
                if count > 0:
                    dados_por_causa[causa.value] = {
                        'total': count,
                        'percentual': (count / total_aves_mortas * 100) if total_aves_mortas > 0 else 0
                    }
            
            causa_predominante = max(dados_por_causa.keys(), key=lambda x: dados_por_causa[x]['total']) if dados_por_causa else None
            
            dias_periodo = (data_fim - data_inicio).days + 1
            data_anterior_inicio = data_inicio - timedelta(days=dias_periodo)
            data_anterior_fim = data_inicio - timedelta(days=1)
            
            mortalidade_anterior = db.session.query(
                func.sum(EventoMortalidade.numero_aves_mortas)
            ).filter(
                and_(
                    EventoMortalidade.id_granja == id_granja,
                    func.date(EventoMortalidade.data_hora_evento) >= data_anterior_inicio,
                    func.date(EventoMortalidade.data_hora_evento) <= data_anterior_fim
                )
            ).scalar() or 0
            
            if mortalidade_anterior == 0:
                tendencia = 'ESTAVEL' if total_aves_mortas == 0 else 'CRESCENTE'
            else:
                variacao = ((total_aves_mortas - mortalidade_anterior) / mortalidade_anterior) * 100
                if variacao > 10:
                    tendencia = 'CRESCENTE'
                elif variacao < -10:
                    tendencia = 'DECRESCENTE'
                else:
                    tendencia = 'ESTAVEL'
            
            alertas_gerados = sum(1 for evento in eventos if evento.requer_investigacao)
            
            relatorio = RelatorioMortalidade(
                tipo_periodo=tipo_periodo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                id_lote=filtros.get('id_lote') if filtros else None,
                id_setor=filtros.get('id_setor') if filtros else None,
                total_aves_mortas=total_aves_mortas,
                total_eventos=total_eventos,
                total_aves_periodo=total_aves_periodo,
                percentual_mortalidade=Decimal(str(round(percentual_mortalidade, 2))),
                dados_por_causa=json.dumps(dados_por_causa),
                causa_predominante=causa_predominante,
                tendencia=tendencia,
                alertas_gerados=alertas_gerados,
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
    def obter_configuracao_alerta(id_lote=None, id_setor=None, id_granja=None):
        """Obter configuração de alerta para lote/setor"""
        return ConfiguracaoAlertaMortalidade.query.filter(
            and_(
                or_(
                    ConfiguracaoAlertaMortalidade.id_lote == id_lote,
                    ConfiguracaoAlertaMortalidade.id_setor == id_setor
                ),
                ConfiguracaoAlertaMortalidade.id_granja == id_granja,
                ConfiguracaoAlertaMortalidade.ativo == True
            )
        ).first()
    
    @staticmethod
    def configurar_alerta_mortalidade(data, usuario_id):
        """Configurar alertas de mortalidade"""
        try:
            config_existente = MortalidadeService.obter_configuracao_alerta(
                data.get('id_lote'),
                data.get('id_setor'),
                data['id_granja']
            )
            
            if config_existente:
                config_existente.percentual_alerta_diario = Decimal(str(data.get('percentual_alerta_diario', 2.0)))
                config_existente.percentual_alerta_semanal = Decimal(str(data.get('percentual_alerta_semanal', 5.0)))
                config_existente.percentual_alerta_mensal = Decimal(str(data.get('percentual_alerta_mensal', 10.0)))
                config_existente.updated_at = datetime.utcnow()
                
                db.session.commit()
                return config_existente, None
            else:
                config = ConfiguracaoAlertaMortalidade(
                    id_lote=data.get('id_lote'),
                    id_setor=data.get('id_setor'),
                    percentual_alerta_diario=Decimal(str(data.get('percentual_alerta_diario', 2.0))),
                    percentual_alerta_semanal=Decimal(str(data.get('percentual_alerta_semanal', 5.0))),
                    percentual_alerta_mensal=Decimal(str(data.get('percentual_alerta_mensal', 10.0))),
                    criado_por=usuario_id,
                    id_granja=data['id_granja']
                )
                
                db.session.add(config)
                db.session.commit()
                return config, None
                
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def obter_estatisticas_mortalidade(id_granja, dias=30):
        """Obter estatísticas de mortalidade para dashboard"""
        try:
            data_limite = date.today() - timedelta(days=dias)
            
            query_periodo = db.session.query(
                func.sum(EventoMortalidade.numero_aves_mortas).label('total_mortes'),
                func.count(EventoMortalidade.id_evento).label('total_eventos')
            ).filter(
                and_(
                    EventoMortalidade.id_granja == id_granja,
                    func.date(EventoMortalidade.data_hora_evento) >= data_limite
                )
            ).first()
            
            hoje = date.today()
            mortalidade_hoje = db.session.query(
                func.sum(EventoMortalidade.numero_aves_mortas)
            ).filter(
                and_(
                    EventoMortalidade.id_granja == id_granja,
                    func.date(EventoMortalidade.data_hora_evento) == hoje
                )
            ).scalar() or 0
            
            principais_causas = db.session.query(
                EventoMortalidade.causa_mortalidade,
                func.sum(EventoMortalidade.numero_aves_mortas).label('total')
            ).filter(
                and_(
                    EventoMortalidade.id_granja == id_granja,
                    func.date(EventoMortalidade.data_hora_evento) >= data_limite
                )
            ).group_by(EventoMortalidade.causa_mortalidade).order_by(desc('total')).limit(5).all()
            
            alertas_ativos = EventoMortalidade.query.filter(
                and_(
                    EventoMortalidade.id_granja == id_granja,
                    EventoMortalidade.requer_investigacao == True,
                    EventoMortalidade.status_evento.in_([StatusEventoMortalidade.REGISTRADO, StatusEventoMortalidade.INVESTIGANDO])
                )
            ).count()
            
            return {
                'periodo': {
                    'total_mortes': query_periodo.total_mortes or 0,
                    'total_eventos': query_periodo.total_eventos or 0,
                    'dias_analisados': dias
                },
                'hoje': {
                    'mortes_hoje': mortalidade_hoje
                },
                'principais_causas': [
                    {
                        'causa': causa.causa_mortalidade.value,
                        'total': causa.total
                    } for causa in principais_causas
                ],
                'alertas_ativos': alertas_ativos
            }
            
        except Exception as e:
            return None