from models import (db, RelatorioProducaoOvos, ProducaoOvos, TipoRelatorioProducao, 
                   QualidadeOvo, StatusProducao, Lotes, Setores)
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, desc, asc
from decimal import Decimal
import json

class RelatorioProducaoService:
    
    @staticmethod
    def gerar_relatorio_producao(data, usuario_id):
        """Gerar relatório detalhado de produção de ovos"""
        try:
            data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d').date()
            data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d').date()
            
            query = ProducaoOvos.query.filter(
                and_(
                    ProducaoOvos.id_granja == data['id_granja'],
                    ProducaoOvos.data_producao >= data_inicio,
                    ProducaoOvos.data_producao <= data_fim,
                    ProducaoOvos.status != StatusProducao.CANCELADO
                )
            )
            
            if data.get('id_lote'):
                query = query.filter(ProducaoOvos.id_lote == data['id_lote'])
            
            if data.get('id_setor'):
                query = query.filter(ProducaoOvos.id_setor == data['id_setor'])
            
            if data.get('qualidade_ovos'):
                query = query.filter(ProducaoOvos.qualidade_ovos == QualidadeOvo(data['qualidade_ovos']))
            
            producoes = query.all()
            
            if not producoes:
                return None, "Nenhum dado de produção encontrado para o período"
            
            total_ovos_produzidos = sum(p.quantidade_ovos_produzidos for p in producoes)
            total_ovos_quebrados = sum(p.ovos_quebrados_danificados for p in producoes)
            total_ovos_aproveitaveis = sum(p.ovos_aproveitaveis for p in producoes)
            
            total_aves_ativas = sum(p.numero_aves_ativas for p in producoes) // len(producoes) if producoes else 0
            
            dias_producao = len(set(p.data_producao for p in producoes))
            
            taxa_producao_media = sum(p.taxa_producao for p in producoes if p.taxa_producao) / len([p for p in producoes if p.taxa_producao]) if producoes else 0
            producao_diaria_media = total_ovos_produzidos / dias_producao if dias_producao > 0 else 0
            percentual_quebrados = (total_ovos_quebrados / total_ovos_produzidos * 100) if total_ovos_produzidos > 0 else 0
            eficiencia_producao = (total_ovos_aproveitaveis / total_ovos_produzidos * 100) if total_ovos_produzidos > 0 else 0
            
            dados_por_qualidade = {}
            for qualidade in QualidadeOvo:
                producoes_qualidade = [p for p in producoes if p.qualidade_ovos == qualidade]
                if producoes_qualidade:
                    total_qualidade = sum(p.quantidade_ovos_produzidos for p in producoes_qualidade)
                    dados_por_qualidade[qualidade.value] = {
                        'total_ovos': total_qualidade,
                        'percentual': (total_qualidade / total_ovos_produzidos * 100) if total_ovos_produzidos > 0 else 0,
                        'dias_registrados': len(producoes_qualidade)
                    }
            
            dias_periodo = (data_fim - data_inicio).days + 1
            meio_periodo = data_inicio + timedelta(days=dias_periodo // 2)
            
            producao_primeira_metade = sum(
                p.quantidade_ovos_produzidos for p in producoes 
                if p.data_producao <= meio_periodo
            )
            
            producao_segunda_metade = sum(
                p.quantidade_ovos_produzidos for p in producoes 
                if p.data_producao > meio_periodo
            )
            
            if producao_segunda_metade > producao_primeira_metade * 1.1:
                tendencia_producao = 'CRESCENTE'
            elif producao_segunda_metade < producao_primeira_metade * 0.9:
                tendencia_producao = 'DECRESCENTE'
            else:
                tendencia_producao = 'ESTAVEL'
            
            producao_diaria = {}
            for p in producoes:
                data_prod = p.data_producao
                if data_prod in producao_diaria:
                    producao_diaria[data_prod] += p.quantidade_ovos_produzidos
                else:
                    producao_diaria[data_prod] = p.quantidade_ovos_produzidos
            
            if producao_diaria:
                melhor_dia = max(producao_diaria.keys(), key=lambda x: producao_diaria[x])
                pior_dia = min(producao_diaria.keys(), key=lambda x: producao_diaria[x])
                maior_producao = producao_diaria[melhor_dia]
                menor_producao = producao_diaria[pior_dia]
            else:
                melhor_dia = pior_dia = None
                maior_producao = menor_producao = 0
            
            dias_anteriores = (data_inicio - timedelta(days=1), data_inicio - timedelta(days=dias_periodo))
            producao_anterior = db.session.query(
                func.sum(ProducaoOvos.quantidade_ovos_produzidos)
            ).filter(
                and_(
                    ProducaoOvos.id_granja == data['id_granja'],
                    ProducaoOvos.data_producao >= dias_anteriores[1],
                    ProducaoOvos.data_producao <= dias_anteriores[0],
                    ProducaoOvos.status != StatusProducao.CANCELADO
                )
            ).scalar() or 0
            
            variacao_periodo_anterior = None
            if producao_anterior > 0:
                variacao_periodo_anterior = ((total_ovos_produzidos - producao_anterior) / producao_anterior) * 100
            
            meta_producao = data.get('meta_producao')
            percentual_meta_atingida = None
            if meta_producao:
                percentual_meta_atingida = (total_ovos_produzidos / meta_producao * 100) if meta_producao > 0 else 0
            
            titulo = f"Relatório de Produção - {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}"
            if data.get('id_setor'):
                setor = Setores.query.get(data['id_setor'])
                if setor:
                    titulo += f" - {setor.descricao_setor}"
            
            relatorio = RelatorioProducaoOvos(
                titulo=titulo,
                tipo_relatorio=TipoRelatorioProducao(data.get('tipo_relatorio', 'PERSONALIZADO')),
                data_inicio=data_inicio,
                data_fim=data_fim,
                id_lote=data.get('id_lote'),
                id_setor=data.get('id_setor'),
                total_ovos_produzidos=total_ovos_produzidos,
                total_ovos_quebrados=total_ovos_quebrados,
                total_ovos_aproveitaveis=total_ovos_aproveitaveis,
                total_aves_ativas=total_aves_ativas,
                dias_producao=dias_producao,
                taxa_producao_media=Decimal(str(round(taxa_producao_media, 2))),
                producao_diaria_media=Decimal(str(round(producao_diaria_media, 2))),
                percentual_quebrados=Decimal(str(round(percentual_quebrados, 2))),
                eficiencia_producao=Decimal(str(round(eficiencia_producao, 2))),
                dados_por_qualidade=json.dumps(dados_por_qualidade),
                tendencia_producao=tendencia_producao,
                melhor_dia_producao=melhor_dia,
                pior_dia_producao=pior_dia,
                maior_producao_diaria=maior_producao,
                menor_producao_diaria=menor_producao,
                variacao_periodo_anterior=Decimal(str(round(variacao_periodo_anterior, 2))) if variacao_periodo_anterior is not None else None,
                meta_producao=meta_producao,
                percentual_meta_atingida=Decimal(str(round(percentual_meta_atingida, 2))) if percentual_meta_atingida is not None else None,
                agrupamento=data.get('agrupamento'),
                filtros_aplicados=json.dumps({k: v for k, v in data.items() if k not in ['id_granja', 'data_inicio', 'data_fim']}),
                gerado_por=usuario_id,
                formato_exportacao=data.get('formato_exportacao'),
                id_granja=data['id_granja']
            )
            
            db.session.add(relatorio)
            db.session.commit()
            
            return relatorio, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def obter_dados_tabular(id_relatorio):
        """Obter dados em formato tabular para o relatório"""
        try:
            relatorio = RelatorioProducaoOvos.query.get(id_relatorio)
            if not relatorio:
                return None
            
            query = ProducaoOvos.query.filter(
                and_(
                    ProducaoOvos.id_granja == relatorio.id_granja,
                    ProducaoOvos.data_producao >= relatorio.data_inicio,
                    ProducaoOvos.data_producao <= relatorio.data_fim,
                    ProducaoOvos.status != StatusProducao.CANCELADO
                )
            )
            
            if relatorio.id_lote:
                query = query.filter(ProducaoOvos.id_lote == relatorio.id_lote)
            
            if relatorio.id_setor:
                query = query.filter(ProducaoOvos.id_setor == relatorio.id_setor)
            
            producoes = query.order_by(ProducaoOvos.data_producao).all()
            
            dados_tabular = []
            for producao in producoes:
                dados_tabular.append({
                    'data_producao': producao.data_producao.strftime('%d/%m/%Y'),
                    'setor': producao.setor.descricao_setor if producao.setor else '',
                    'lote': producao.id_lote or '',
                    'ovos_produzidos': producao.quantidade_ovos_produzidos,
                    'aves_ativas': producao.numero_aves_ativas,
                    'taxa_producao': float(producao.taxa_producao) if producao.taxa_producao else 0,
                    'ovos_quebrados': producao.ovos_quebrados_danificados,
                    'ovos_aproveitaveis': producao.ovos_aproveitaveis,
                    'qualidade': producao.qualidade_ovos.value if producao.qualidade_ovos else '',
                    'operador': producao.operador.nome if producao.operador else '',
                    'observacoes': producao.observacoes or ''
                })
            
            return dados_tabular
            
        except Exception as e:
            return None
    
    @staticmethod
    def obter_dados_grafico(id_relatorio, tipo_grafico='linha'):
        """Obter dados formatados para gráficos"""
        try:
            relatorio = RelatorioProducaoOvos.query.get(id_relatorio)
            if not relatorio:
                return None
            
            base_filter = and_(
                ProducaoOvos.id_granja == relatorio.id_granja,
                ProducaoOvos.data_producao >= relatorio.data_inicio,
                ProducaoOvos.data_producao <= relatorio.data_fim,
                ProducaoOvos.status != StatusProducao.CANCELADO
            )
            
            if relatorio.id_lote:
                base_filter = and_(base_filter, ProducaoOvos.id_lote == relatorio.id_lote)
            if relatorio.id_setor:
                base_filter = and_(base_filter, ProducaoOvos.id_setor == relatorio.id_setor)
            
            if tipo_grafico == 'linha':
                dados = db.session.query(
                    ProducaoOvos.data_producao,
                    func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_ovos'),
                    func.sum(ProducaoOvos.ovos_quebrados_danificados).label('total_quebrados'),
                    func.avg(ProducaoOvos.taxa_producao).label('taxa_media')
                ).filter(base_filter).group_by(ProducaoOvos.data_producao).order_by(ProducaoOvos.data_producao).all()
                
                return {
                    'labels': [d.data_producao.strftime('%d/%m') for d in dados],
                    'datasets': [
                        {
                            'label': 'Ovos Produzidos',
                            'data': [d.total_ovos for d in dados],
                            'type': 'line',
                            'borderColor': '#4CAF50',
                            'backgroundColor': 'rgba(76, 175, 80, 0.1)'
                        },
                        {
                            'label': 'Ovos Quebrados',
                            'data': [d.total_quebrados for d in dados],
                            'type': 'line',
                            'borderColor': '#F44336',
                            'backgroundColor': 'rgba(244, 67, 54, 0.1)'
                        },
                        {
                            'label': 'Taxa Produção (%)',
                            'data': [float(d.taxa_media) if d.taxa_media else 0 for d in dados],
                            'type': 'line',
                            'borderColor': '#2196F3',
                            'backgroundColor': 'rgba(33, 150, 243, 0.1)',
                            'yAxisID': 'y1'
                        }
                    ]
                }
            
            elif tipo_grafico == 'pizza':
                dados_qualidade = json.loads(relatorio.dados_por_qualidade) if relatorio.dados_por_qualidade else {}
                
                if not dados_qualidade:
                    return {
                        'labels': ['Sem dados'],
                        'data': [0],
                        'type': 'pie',
                        'backgroundColor': ['#E0E0E0']
                    }
                
                cores = {
                    'Excelente': '#4CAF50',
                    'Bom': '#8BC34A',
                    'Regular': '#FF9800',
                    'Ruim': '#F44336'
                }
                
                return {
                    'labels': list(dados_qualidade.keys()),
                    'data': [dados_qualidade[k]['total_ovos'] for k in dados_qualidade.keys()],
                    'type': 'pie',
                    'backgroundColor': [cores.get(k, '#9E9E9E') for k in dados_qualidade.keys()]
                }
            
            elif tipo_grafico == 'barras':
                dados = db.session.query(
                    Setores.descricao_setor,
                    func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_producao'),
                    func.sum(ProducaoOvos.ovos_quebrados_danificados).label('total_quebrados'),
                    func.avg(ProducaoOvos.taxa_producao).label('taxa_media')
                ).join(ProducaoOvos).filter(base_filter).group_by(Setores.id_setor).order_by(desc('total_producao')).all()
                
                return {
                    'labels': [d.descricao_setor for d in dados],
                    'datasets': [
                        {
                            'label': 'Ovos Produzidos',
                            'data': [d.total_producao for d in dados],
                            'backgroundColor': '#4CAF50'
                        },
                        {
                            'label': 'Ovos Quebrados',
                            'data': [d.total_quebrados for d in dados],
                            'backgroundColor': '#F44336'
                        }
                    ],
                    'type': 'bar'
                }
            
            elif tipo_grafico == 'area':
                dados = db.session.query(
                    ProducaoOvos.data_producao,
                    func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_ovos'),
                    func.sum(ProducaoOvos.ovos_aproveitaveis).label('total_aproveitaveis')
                ).filter(base_filter).group_by(ProducaoOvos.data_producao).order_by(ProducaoOvos.data_producao).all()
                
                return {
                    'labels': [d.data_producao.strftime('%d/%m') for d in dados],
                    'datasets': [
                        {
                            'label': 'Total Produzidos',
                            'data': [d.total_ovos for d in dados],
                            'fill': True,
                            'backgroundColor': 'rgba(76, 175, 80, 0.3)',
                            'borderColor': '#4CAF50'
                        },
                        {
                            'label': 'Aproveitáveis',
                            'data': [d.total_aproveitaveis for d in dados],
                            'fill': True,
                            'backgroundColor': 'rgba(33, 150, 243, 0.3)',
                            'borderColor': '#2196F3'
                        }
                    ],
                    'type': 'area'
                }
            
            return None
            
        except Exception as e:
            return None
    
    @staticmethod
    def listar_relatorios(id_granja, filtros=None):
        """Listar relatórios gerados"""
        try:
            query = RelatorioProducaoOvos.query.filter(RelatorioProducaoOvos.id_granja == id_granja)
            
            if filtros:
                if filtros.get('tipo_relatorio'):
                    query = query.filter(RelatorioProducaoOvos.tipo_relatorio == TipoRelatorioProducao(filtros['tipo_relatorio']))
                
                if filtros.get('data_geracao_inicio'):
                    data_inicio = datetime.strptime(filtros['data_geracao_inicio'], '%Y-%m-%d')
                    query = query.filter(RelatorioProducaoOvos.data_geracao >= data_inicio)
                
                if filtros.get('data_geracao_fim'):
                    data_fim = datetime.strptime(filtros['data_geracao_fim'], '%Y-%m-%d')
                    data_fim = data_fim.replace(hour=23, minute=59, second=59)
                    query = query.filter(RelatorioProducaoOvos.data_geracao <= data_fim)
                
                if filtros.get('gerado_por'):
                    query = query.filter(RelatorioProducaoOvos.gerado_por == filtros['gerado_por'])
                
                if filtros.get('id_setor'):
                    query = query.filter(RelatorioProducaoOvos.id_setor == filtros['id_setor'])
            
            return query.order_by(desc(RelatorioProducaoOvos.data_geracao)).all()
            
        except Exception as e:
            return []
    
    @staticmethod
    def obter_relatorio(id_relatorio, id_granja):
        """Obter relatório específico"""
        return RelatorioProducaoOvos.query.filter(
            and_(
                RelatorioProducaoOvos.id_relatorio == id_relatorio,
                RelatorioProducaoOvos.id_granja == id_granja
            )
        ).first()
    
    @staticmethod
    def obter_indicadores_performance(id_granja, data_inicio, data_fim, comparar_com_anterior=True):
        """Obter indicadores de performance detalhados"""
        try:
            if isinstance(data_inicio, str):
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            if isinstance(data_fim, str):
                data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            
            dados_periodo = db.session.query(
                func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_ovos'),
                func.sum(ProducaoOvos.ovos_quebrados_danificados).label('total_quebrados'),
                func.sum(ProducaoOvos.ovos_aproveitaveis).label('total_aproveitaveis'),
                func.avg(ProducaoOvos.numero_aves_ativas).label('media_aves'),
                func.avg(ProducaoOvos.taxa_producao).label('taxa_media'),
                func.count(func.distinct(ProducaoOvos.data_producao)).label('dias_atividade'),
                func.max(ProducaoOvos.quantidade_ovos_produzidos).label('maior_producao'),
                func.min(ProducaoOvos.quantidade_ovos_produzidos).label('menor_producao')
            ).filter(
                and_(
                    ProducaoOvos.id_granja == id_granja,
                    ProducaoOvos.data_producao >= data_inicio,
                    ProducaoOvos.data_producao <= data_fim,
                    ProducaoOvos.status != StatusProducao.CANCELADO
                )
            ).first()
            
            if not dados_periodo or not dados_periodo.total_ovos:
                return {
                    'periodo_atual': {
                        'total_ovos_produzidos': 0,
                        'total_ovos_quebrados': 0,
                        'total_ovos_aproveitaveis': 0,
                        'taxa_producao_media': 0,
                        'eficiencia_producao': 0,
                        'producao_diaria_media': 0,
                        'dias_atividade': 0
                    },
                    'comparativo': None
                }
            
            total_ovos = dados_periodo.total_ovos or 0
            total_quebrados = dados_periodo.total_quebrados or 0
            total_aproveitaveis = dados_periodo.total_aproveitaveis or 0
            dias_atividade = dados_periodo.dias_atividade or 1
            
            eficiencia_producao = (total_aproveitaveis / total_ovos * 100) if total_ovos > 0 else 0
            producao_diaria_media = total_ovos / dias_atividade
            percentual_quebrados = (total_quebrados / total_ovos * 100) if total_ovos > 0 else 0
            
            indicadores = {
                'periodo_atual': {
                    'total_ovos_produzidos': total_ovos,
                    'total_ovos_quebrados': total_quebrados,
                    'total_ovos_aproveitaveis': total_aproveitaveis,
                    'taxa_producao_media': float(dados_periodo.taxa_media or 0),
                    'eficiencia_producao': round(eficiencia_producao, 2),
                    'percentual_quebrados': round(percentual_quebrados, 2),
                    'producao_diaria_media': round(producao_diaria_media, 2),
                    'media_aves_ativas': int(dados_periodo.media_aves or 0),
                    'dias_atividade': dias_atividade,
                    'maior_producao_diaria': dados_periodo.maior_producao or 0,
                    'menor_producao_diaria': dados_periodo.menor_producao or 0
                }
            }
            
            if comparar_com_anterior:
                dias_periodo = (data_fim - data_inicio).days + 1
                data_anterior_fim = data_inicio - timedelta(days=1)
                data_anterior_inicio = data_anterior_fim - timedelta(days=dias_periodo - 1)
                
                dados_anterior = db.session.query(
                    func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_ovos'),
                    func.sum(ProducaoOvos.ovos_quebrados_danificados).label('total_quebrados'),
                    func.avg(ProducaoOvos.taxa_producao).label('taxa_media')
                ).filter(
                    and_(
                        ProducaoOvos.id_granja == id_granja,
                        ProducaoOvos.data_producao >= data_anterior_inicio,
                        ProducaoOvos.data_producao <= data_anterior_fim,
                        ProducaoOvos.status != StatusProducao.CANCELADO
                    )
                ).first()
                
                if dados_anterior and dados_anterior.total_ovos:
                    total_anterior = dados_anterior.total_ovos
                    quebrados_anterior = dados_anterior.total_quebrados or 0
                    taxa_anterior = float(dados_anterior.taxa_media or 0)
                    
                    variacao_producao = ((total_ovos - total_anterior) / total_anterior * 100) if total_anterior > 0 else 0
                    variacao_quebrados = ((total_quebrados - quebrados_anterior) / quebrados_anterior * 100) if quebrados_anterior > 0 else 0
                    variacao_taxa = indicadores['periodo_atual']['taxa_producao_media'] - taxa_anterior
                    
                    indicadores['comparativo'] = {
                        'periodo_anterior': {
                            'total_ovos': total_anterior,
                            'total_quebrados': quebrados_anterior,
                            'taxa_media': taxa_anterior
                        },
                        'variacoes': {
                            'producao': round(variacao_producao, 2),
                            'quebrados': round(variacao_quebrados, 2),
                            'taxa_producao': round(variacao_taxa, 2)
                        },
                        'tendencias': {
                            'producao': 'CRESCENTE' if variacao_producao > 5 else 'DECRESCENTE' if variacao_producao < -5 else 'ESTAVEL',
                            'qualidade': 'MELHOROU' if variacao_quebrados < -10 else 'PIOROU' if variacao_quebrados > 10 else 'ESTAVEL'
                        }
                    }
                else:
                    indicadores['comparativo'] = None
            
            return indicadores
            
        except Exception as e:
            return None
    
    @staticmethod
    def gerar_relatorio_personalizado(parametros, usuario_id):
        """Gerar relatório com parâmetros personalizados"""
        try:
            id_granja = parametros['id_granja']
            data_inicio = datetime.strptime(parametros['data_inicio'], '%Y-%m-%d').date()
            data_fim = datetime.strptime(parametros['data_fim'], '%Y-%m-%d').date()
            agrupamento = parametros.get('agrupamento', 'diario') 
            incluir_comparativo = parametros.get('incluir_comparativo', True)
            incluir_graficos = parametros.get('incluir_graficos', True)
            meta_personalizada = parametros.get('meta_producao')
            
            relatorio, erro = RelatorioProducaoService.gerar_relatorio_producao(parametros, usuario_id)
            if erro:
                return None, erro
            
            dados_agrupados = None
            
            if agrupamento == 'semanal':
                dados_agrupados = db.session.query(
                    func.date_trunc('week', ProducaoOvos.data_producao).label('periodo'),
                    func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_ovos'),
                    func.sum(ProducaoOvos.ovos_quebrados_danificados).label('total_quebrados'),
                    func.avg(ProducaoOvos.taxa_producao).label('taxa_media'),
                    func.count(ProducaoOvos.id_producao_ovos).label('dias_registrados')
                ).filter(
                    and_(
                        ProducaoOvos.id_granja == id_granja,
                        ProducaoOvos.data_producao >= data_inicio,
                        ProducaoOvos.data_producao <= data_fim,
                        ProducaoOvos.status != StatusProducao.CANCELADO
                    )
                ).group_by('periodo').order_by('periodo').all()
            
            elif agrupamento == 'mensal':
                dados_agrupados = db.session.query(
                    func.date_trunc('month', ProducaoOvos.data_producao).label('periodo'),
                    func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_ovos'),
                    func.sum(ProducaoOvos.ovos_quebrados_danificados).label('total_quebrados'),
                    func.avg(ProducaoOvos.taxa_producao).label('taxa_media'),
                    func.count(ProducaoOvos.id_producao_ovos).label('dias_registrados')
                ).filter(
                    and_(
                        ProducaoOvos.id_granja == id_granja,
                        ProducaoOvos.data_producao >= data_inicio,
                        ProducaoOvos.data_producao <= data_fim,
                        ProducaoOvos.status != StatusProducao.CANCELADO
                    )
                ).group_by('periodo').order_by('periodo').all()
            
            elif agrupamento == 'setor':
                dados_agrupados = db.session.query(
                    Setores.descricao_setor.label('periodo'),
                    func.sum(ProducaoOvos.quantidade_ovos_produzidos).label('total_ovos'),
                    func.sum(ProducaoOvos.ovos_quebrados_danificados).label('total_quebrados'),
                    func.avg(ProducaoOvos.taxa_producao).label('taxa_media'),
                    func.count(ProducaoOvos.id_producao_ovos).label('dias_registrados')
                ).join(ProducaoOvos).filter(
                    and_(
                        ProducaoOvos.id_granja == id_granja,
                        ProducaoOvos.data_producao >= data_inicio,
                        ProducaoOvos.data_producao <= data_fim,
                        ProducaoOvos.status != StatusProducao.CANCELADO
                    )
                ).group_by(Setores.id_setor, Setores.descricao_setor).order_by(desc('total_ovos')).all()
            
            if dados_agrupados:
                dados_formatados = []
                for item in dados_agrupados:
                    dados_formatados.append({
                        'periodo': str(item.periodo),
                        'total_ovos': item.total_ovos,
                        'total_quebrados': item.total_quebrados,
                        'taxa_media': float(item.taxa_media) if item.taxa_media else 0,
                        'dias_registrados': item.dias_registrados,
                        'eficiencia': ((item.total_ovos - item.total_quebrados) / item.total_ovos * 100) if item.total_ovos > 0 else 0
                    })
                
                filtros_atuais = json.loads(relatorio.filtros_aplicados) if relatorio.filtros_aplicados else {}
                filtros_atuais['dados_agrupados'] = dados_formatados
                filtros_atuais['agrupamento_aplicado'] = agrupamento
                
                relatorio.filtros_aplicados = json.dumps(filtros_atuais)
                relatorio.agrupamento = agrupamento
                
                db.session.commit()
            
            return relatorio, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def excluir_relatorio(id_relatorio, id_granja):
        """Excluir relatório"""
        try:
            relatorio = RelatorioProducaoOvos.query.filter(
                and_(
                    RelatorioProducaoOvos.id_relatorio == id_relatorio,
                    RelatorioProducaoOvos.id_granja == id_granja
                )
            ).first()
            
            if not relatorio:
                return False, "Relatório não encontrado"
            
            db.session.delete(relatorio)
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)