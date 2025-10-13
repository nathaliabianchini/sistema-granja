from models import (db, Insumos, MovimentacaoInsumo, RelatorioConsumo, AlertaInsumo,
                   TipoInsumo, UnidadeMedida, TipoMovimentacao, StatusInsumo, Usuarios)
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
import json

class InsumoService:
    
    @staticmethod
    def criar_insumo(data, usuario_id):
        """Criar novo insumo"""
        try:
            codigo_interno = data.get('codigo_interno')
            if not codigo_interno:
                tipo_prefix = data['tipo_insumo'][:3].upper()
                count = Insumos.query.filter(
                    and_(
                        Insumos.id_granja == data['id_granja'],
                        Insumos.tipo_insumo == TipoInsumo(data['tipo_insumo'])
                    )
                ).count()
                codigo_interno = f"{tipo_prefix}{count + 1:04d}"
            
            data_validade = data.get('data_validade')
            if data_validade and isinstance(data_validade, str):
                data_validade = datetime.strptime(data_validade, '%Y-%m-%d').date()
            
            insumo = Insumos(
                codigo_interno=codigo_interno,
                nome=data['nome'],
                descricao=data.get('descricao'),
                tipo_insumo=TipoInsumo(data['tipo_insumo']),
                unidade_medida=UnidadeMedida(data.get('unidade_medida', 'UNIDADES')),
                quantidade_atual=Decimal(str(data.get('quantidade_inicial', 0))),
                quantidade_minima=Decimal(str(data.get('quantidade_minima', 0))),
                quantidade_maxima=Decimal(str(data.get('quantidade_maxima', 0))) if data.get('quantidade_maxima') else None,
                fabricante=data.get('fabricante'),
                fornecedor_principal=data.get('fornecedor_principal'),
                numero_registro=data.get('numero_registro'),
                composicao=data.get('composicao'),
                data_validade=data_validade,
                local_armazenamento=data.get('local_armazenamento'),
                temperatura_armazenamento=data.get('temperatura_armazenamento'),
                observacoes_armazenamento=data.get('observacoes_armazenamento'),
                preco_ultima_compra=Decimal(str(data['preco_unitario'])) if data.get('preco_unitario') else None,
                data_ultima_compra=date.today() if data.get('preco_unitario') else None,
                created_by=usuario_id,
                id_granja=data['id_granja']
            )
            
            db.session.add(insumo)
            db.session.flush()  
            
            if data.get('quantidade_inicial', 0) > 0:
                InsumoService._criar_movimentacao(
                    insumo.id_insumo,
                    TipoMovimentacao.ENTRADA_COMPRA,
                    Decimal(str(data['quantidade_inicial'])),
                    Decimal('0'),
                    Decimal(str(data['quantidade_inicial'])),
                    usuario_id,
                    data['id_granja'],
                    {
                        'numero_documento': data.get('numero_documento'),
                        'fornecedor': data.get('fornecedor_principal'),
                        'valor_unitario': data.get('preco_unitario'),
                        'data_vencimento_lote': data_validade,
                        'motivo': 'Estoque inicial'
                    }
                )
            
            InsumoService._verificar_alertas(insumo)
            
            db.session.commit()
            return insumo, None
            
        except IntegrityError:
            db.session.rollback()
            return None, "Código interno já existe"
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def listar_insumos(id_granja, filtros=None):
        """Listar insumos com filtros"""
        try:
            query = Insumos.query.filter(Insumos.id_granja == id_granja)
            
            if filtros:
                if filtros.get('status'):
                    query = query.filter(Insumos.status == StatusInsumo(filtros['status']))
                
                if filtros.get('tipo_insumo'):
                    query = query.filter(Insumos.tipo_insumo == TipoInsumo(filtros['tipo_insumo']))
                
                if filtros.get('busca'):
                    busca = f"%{filtros['busca']}%"
                    query = query.filter(or_(
                        Insumos.nome.ilike(busca),
                        Insumos.descricao.ilike(busca),
                        Insumos.codigo_interno.ilike(busca)
                    ))
                
                if filtros.get('estoque_baixo') == 'true':
                    query = query.filter(Insumos.quantidade_atual <= Insumos.quantidade_minima)
                
                if filtros.get('vencimento_proximo'):
                    dias = int(filtros['vencimento_proximo'])
                    data_limite = date.today() + timedelta(days=dias)
                    query = query.filter(
                        and_(
                            Insumos.data_validade.isnot(None),
                            Insumos.data_validade <= data_limite,
                            Insumos.data_validade >= date.today()
                        )
                    )
                
                if filtros.get('fornecedor'):
                    query = query.filter(Insumos.fornecedor_principal.ilike(f"%{filtros['fornecedor']}%"))
            
            ordem = filtros.get('ordem', 'nome') if filtros else 'nome'
            if ordem == 'quantidade':
                query = query.order_by(Insumos.quantidade_atual)
            elif ordem == 'validade':
                query = query.order_by(Insumos.data_validade.nullslast())
            elif ordem == 'tipo':
                query = query.order_by(Insumos.tipo_insumo, Insumos.nome)
            else:
                query = query.order_by(Insumos.nome)
            
            return query.all()
            
        except Exception as e:
            return []
    
    @staticmethod
    def obter_insumo(id_insumo, id_granja):
        """Obter insumo específico"""
        return Insumos.query.filter(
            and_(
                Insumos.id_insumo == id_insumo,
                Insumos.id_granja == id_granja
            )
        ).first()
    
    @staticmethod
    def atualizar_insumo(id_insumo, data, usuario_id):
        """Atualizar dados do insumo"""
        try:
            insumo = Insumos.query.get(id_insumo)
            if not insumo:
                return None, "Insumo não encontrado"
            
            campos_atualizaveis = [
                'nome', 'descricao', 'quantidade_minima', 'quantidade_maxima',
                'fabricante', 'fornecedor_principal', 'numero_registro', 'composicao',
                'local_armazenamento', 'temperatura_armazenamento', 'observacoes_armazenamento',
                'status'
            ]
            
            for campo in campos_atualizaveis:
                if campo in data:
                    if campo == 'status':
                        setattr(insumo, campo, StatusInsumo(data[campo]))
                    elif campo in ['quantidade_minima', 'quantidade_maxima']:
                        if data[campo] is not None:
                            setattr(insumo, campo, Decimal(str(data[campo])))
                    else:
                        setattr(insumo, campo, data[campo])
            
            if 'data_validade' in data:
                data_validade = data['data_validade']
                if data_validade and isinstance(data_validade, str):
                    data_validade = datetime.strptime(data_validade, '%Y-%m-%d').date()
                insumo.data_validade = data_validade
            
            insumo.updated_at = datetime.utcnow()
            
            InsumoService._verificar_alertas(insumo)
            
            db.session.commit()
            return insumo, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def registrar_entrada(id_insumo, data, usuario_id):
        """Registrar entrada de insumo"""
        try:
            insumo = Insumos.query.get(id_insumo)
            if not insumo:
                return None, "Insumo não encontrado"
            
            quantidade = Decimal(str(data['quantidade']))
            if quantidade <= 0:
                return None, "Quantidade deve ser maior que zero"
            
            quantidade_anterior = insumo.quantidade_atual
            quantidade_posterior = quantidade_anterior + quantidade
            
            insumo.quantidade_atual = quantidade_posterior
            
            if data.get('valor_unitario'):
                insumo.preco_ultima_compra = Decimal(str(data['valor_unitario']))
                insumo.data_ultima_compra = date.today()
            
            tipo_mov = TipoMovimentacao(data.get('tipo_movimentacao', 'ENTRADA_COMPRA'))
            
            movimentacao = InsumoService._criar_movimentacao(
                id_insumo,
                tipo_mov,
                quantidade,
                quantidade_anterior,
                quantidade_posterior,
                usuario_id,
                insumo.id_granja,
                data
            )
            
            InsumoService._verificar_alertas(insumo)
            
            db.session.commit()
            return movimentacao, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def registrar_saida(id_insumo, data, usuario_id):
        """Registrar saída de insumo"""
        try:
            insumo = Insumos.query.get(id_insumo)
            if not insumo:
                return None, "Insumo não encontrado"
            
            quantidade = Decimal(str(data['quantidade']))
            if quantidade <= 0:
                return None, "Quantidade deve ser maior que zero"
            
            quantidade_anterior = insumo.quantidade_atual
            
            if quantidade > quantidade_anterior:
                return None, "Quantidade solicitada maior que estoque disponível"
            
            quantidade_posterior = quantidade_anterior - quantidade
            
            insumo.quantidade_atual = quantidade_posterior
            
            tipo_mov = TipoMovimentacao(data.get('tipo_movimentacao', 'SAIDA_USO'))
            
            movimentacao = InsumoService._criar_movimentacao(
                id_insumo,
                tipo_mov,
                quantidade,
                quantidade_anterior,
                quantidade_posterior,
                usuario_id,
                insumo.id_granja,
                data
            )
            
            InsumoService._verificar_alertas(insumo)
            
            db.session.commit()
            return movimentacao, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)
    
    @staticmethod
    def _criar_movimentacao(id_insumo, tipo_mov, quantidade, qtd_anterior, qtd_posterior, usuario_id, id_granja, dados_extras):
        """Criar registro de movimentação"""
        data_vencimento = dados_extras.get('data_vencimento_lote')
        if data_vencimento and isinstance(data_vencimento, str):
            data_vencimento = datetime.strptime(data_vencimento, '%Y-%m-%d').date()
        
        valor_total = None
        if dados_extras.get('valor_unitario'):
            valor_total = Decimal(str(dados_extras['valor_unitario'])) * quantidade
        
        movimentacao = MovimentacaoInsumo(
            id_insumo=id_insumo,
            tipo_movimentacao=tipo_mov,
            quantidade=quantidade,
            quantidade_anterior=qtd_anterior,
            quantidade_posterior=qtd_posterior,
            data_vencimento_lote=data_vencimento,
            numero_documento=dados_extras.get('numero_documento'),
            fornecedor=dados_extras.get('fornecedor'),
            valor_unitario=Decimal(str(dados_extras['valor_unitario'])) if dados_extras.get('valor_unitario') else None,
            valor_total=valor_total,
            motivo=dados_extras.get('motivo'),
            observacoes=dados_extras.get('observacoes'),
            setor_destino=dados_extras.get('setor_destino'),
            responsavel=usuario_id,
            id_granja=id_granja
        )
        
        db.session.add(movimentacao)
        return movimentacao
    
    @staticmethod
    def obter_movimentacoes(id_insumo=None, id_granja=None, filtros=None):
        """Obter movimentações com filtros"""
        try:
            query = MovimentacaoInsumo.query
            
            if id_granja:
                query = query.filter(MovimentacaoInsumo.id_granja == id_granja)
            
            if id_insumo:
                query = query.filter(MovimentacaoInsumo.id_insumo == id_insumo)
            
            if filtros:
                if filtros.get('tipo_movimentacao'):
                    query = query.filter(
                        MovimentacaoInsumo.tipo_movimentacao == TipoMovimentacao(filtros['tipo_movimentacao'])
                    )
                
                if filtros.get('data_inicio'):
                    data_inicio = datetime.strptime(filtros['data_inicio'], '%Y-%m-%d')
                    query = query.filter(MovimentacaoInsumo.data_movimentacao >= data_inicio)
                
                if filtros.get('data_fim'):
                    data_fim = datetime.strptime(filtros['data_fim'], '%Y-%m-%d')
                    data_fim = data_fim.replace(hour=23, minute=59, second=59)
                    query = query.filter(MovimentacaoInsumo.data_movimentacao <= data_fim)
                
                if filtros.get('fornecedor'):
                    query = query.filter(
                        MovimentacaoInsumo.fornecedor.ilike(f"%{filtros['fornecedor']}%")
                    )
                
                if filtros.get('responsavel'):
                    query = query.filter(MovimentacaoInsumo.responsavel == filtros['responsavel'])
            
            return query.order_by(desc(MovimentacaoInsumo.data_movimentacao)).all()
            
        except Exception as e:
            return []
    
    @staticmethod
    def _verificar_alertas(insumo):
        """Verificar e criar alertas automáticos"""
        try:
            alertas_existentes = AlertaInsumo.query.filter(
                and_(
                    AlertaInsumo.id_insumo == insumo.id_insumo,
                    AlertaInsumo.ativo == True
                )
            ).all()
            
            for alerta in alertas_existentes:
                deve_resolver = False
                
                if alerta.tipo_alerta == 'ESTOQUE_BAIXO' and not insumo.estoque_baixo:
                    deve_resolver = True
                elif alerta.tipo_alerta == 'ESGOTADO' and insumo.quantidade_atual > 0:
                    deve_resolver = True
                
                if deve_resolver:
                    alerta.ativo = False
                    alerta.data_resolucao = datetime.utcnow()

            if insumo.estoque_baixo and insumo.quantidade_atual > 0:
                alerta_existente = any(a.tipo_alerta == 'ESTOQUE_BAIXO' and a.ativo for a in alertas_existentes)
                if not alerta_existente:
                    alerta = AlertaInsumo(
                        id_insumo=insumo.id_insumo,
                        tipo_alerta='ESTOQUE_BAIXO',
                        nivel_prioridade='ALTA',
                        mensagem=f'Estoque baixo para {insumo.nome}. Quantidade atual: {insumo.quantidade_atual} {insumo.unidade_medida.value}',
                        id_granja=insumo.id_granja
                    )
                    db.session.add(alerta)

            if insumo.quantidade_atual <= 0:
                alerta_existente = any(a.tipo_alerta == 'ESGOTADO' and a.ativo for a in alertas_existentes)
                if not alerta_existente:
                    alerta = AlertaInsumo(
                        id_insumo=insumo.id_insumo,
                        tipo_alerta='ESGOTADO',
                        nivel_prioridade='CRITICA',
                        mensagem=f'Estoque esgotado para {insumo.nome}',
                        id_granja=insumo.id_granja
                    )
                    db.session.add(alerta)
            
            if insumo.data_validade:
                dias_para_vencer = insumo.dias_para_vencer
                if dias_para_vencer is not None and dias_para_vencer <= 30 and dias_para_vencer >= 0:
                    alerta_existente = any(a.tipo_alerta == 'VENCIMENTO' and a.ativo for a in alertas_existentes)
                    if not alerta_existente:
                        prioridade = 'CRITICA' if dias_para_vencer <= 7 else 'ALTA'
                        alerta = AlertaInsumo(
                            id_insumo=insumo.id_insumo,
                            tipo_alerta='VENCIMENTO',
                            nivel_prioridade=prioridade,
                            mensagem=f'{insumo.nome} vence em {dias_para_vencer} dias ({insumo.data_validade.strftime("%d/%m/%Y")})',
                            id_granja=insumo.id_granja
                        )
                        db.session.add(alerta)
        
        except Exception as e:
            pass
    
    @staticmethod
    def gerar_relatorio_consumo(id_granja, data_inicio, data_fim, tipo_periodo, id_insumo=None, tipo_insumo_filtro=None, usuario_id=None):
        """Gerar relatório de consumo de insumos"""
        try:
            if isinstance(data_inicio, str):
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            if isinstance(data_fim, str):
                data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            
            query = MovimentacaoInsumo.query.filter(
                and_(
                    MovimentacaoInsumo.id_granja == id_granja,
                    func.date(MovimentacaoInsumo.data_movimentacao) >= data_inicio,
                    func.date(MovimentacaoInsumo.data_movimentacao) <= data_fim
                )
            )
            
            if id_insumo:
                query = query.filter(MovimentacaoInsumo.id_insumo == id_insumo)
            
            if tipo_insumo_filtro:
                query = query.join(Insumos).filter(Insumos.tipo_insumo == TipoInsumo(tipo_insumo_filtro))
            
            movimentacoes = query.all()
            
            total_entradas = Decimal('0')
            total_saidas = Decimal('0')
            valor_total_entradas = Decimal('0')
            valor_total_saidas = Decimal('0')
            
            for mov in movimentacoes:
                if mov.tipo_movimentacao.value.startswith('Entrada'):
                    total_entradas += mov.quantidade
                    if mov.valor_total:
                        valor_total_entradas += mov.valor_total
                else:
                    total_saidas += mov.quantidade
                    if mov.valor_total:
                        valor_total_saidas += mov.valor_total
            
            dias_periodo = (data_fim - data_inicio).days + 1
            consumo_medio_diario = total_saidas / dias_periodo if dias_periodo > 0 else Decimal('0')
            
            meio_periodo = data_inicio + timedelta(days=dias_periodo // 2)
            
            saidas_primeira_metade = sum(
                mov.quantidade for mov in movimentacoes
                if (mov.tipo_movimentacao.value.startswith('Saída') and 
                    mov.data_movimentacao.date() <= meio_periodo)
            ) or Decimal('0')
            
            saidas_segunda_metade = sum(
                mov.quantidade for mov in movimentacoes
                if (mov.tipo_movimentacao.value.startswith('Saída') and 
                    mov.data_movimentacao.date() > meio_periodo)
            ) or Decimal('0')
            
            if saidas_segunda_metade > saidas_primeira_metade * Decimal('1.1'):
                tendencia = 'CRESCENTE'
            elif saidas_segunda_metade < saidas_primeira_metade * Decimal('0.9'):
                tendencia = 'DECRESCENTE'
            else:
                tendencia = 'ESTAVEL'
            
            relatorio = RelatorioConsumo(
                tipo_periodo=tipo_periodo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                id_insumo=id_insumo,
                tipo_insumo_filtro=TipoInsumo(tipo_insumo_filtro) if tipo_insumo_filtro else None,
                total_entradas=total_entradas,
                total_saidas=total_saidas,
                valor_total_entradas=valor_total_entradas,
                valor_total_saidas=valor_total_saidas,
                movimentacoes_count=len(movimentacoes),
                consumo_medio_diario=consumo_medio_diario,
                tendencia_consumo=tendencia,
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
    def obter_dashboard_insumos(id_granja):
        """Obter dados para dashboard de insumos"""
        try:
            estoque_baixo = Insumos.query.filter(
                and_(
                    Insumos.id_granja == id_granja,
                    Insumos.quantidade_atual <= Insumos.quantidade_minima,
                    Insumos.status == StatusInsumo.ATIVO
                )
            ).count()
            
            data_limite = date.today() + timedelta(days=30)
            vencendo_30_dias = Insumos.query.filter(
                and_(
                    Insumos.id_granja == id_granja,
                    Insumos.data_validade.isnot(None),
                    Insumos.data_validade <= data_limite,
                    Insumos.data_validade >= date.today(),
                    Insumos.status == StatusInsumo.ATIVO
                )
            ).count()
            
            esgotados = Insumos.query.filter(
                and_(
                    Insumos.id_granja == id_granja,
                    Insumos.quantidade_atual <= 0,
                    Insumos.status == StatusInsumo.ATIVO
                )
            ).count()
            
            data_limite_mov = datetime.now() - timedelta(days=7)
            movimentacoes_recentes = MovimentacaoInsumo.query.filter(
                and_(
                    MovimentacaoInsumo.id_granja == id_granja,
                    MovimentacaoInsumo.data_movimentacao >= data_limite_mov
                )
            ).count()
            
            data_limite_consumo = datetime.now() - timedelta(days=30)
            top_consumidos = db.session.query(
                Insumos.nome,
                func.sum(MovimentacaoInsumo.quantidade).label('total_consumido')
            ).join(MovimentacaoInsumo).filter(
                and_(
                    MovimentacaoInsumo.id_granja == id_granja,
                    MovimentacaoInsumo.data_movimentacao >= data_limite_consumo,
                    MovimentacaoInsumo.tipo_movimentacao.in_([
                        TipoMovimentacao.SAIDA_USO,
                        TipoMovimentacao.SAIDA_PERDA
                    ])
                )
            ).group_by(Insumos.id_insumo).order_by(desc('total_consumido')).limit(5).all()
            
            alertas_ativos = AlertaInsumo.query.filter(
                and_(
                    AlertaInsumo.id_granja == id_granja,
                    AlertaInsumo.ativo == True
                )
            ).count()
            
            return {
                'resumo': {
                    'estoque_baixo': estoque_baixo,
                    'vencendo_30_dias': vencendo_30_dias,
                    'esgotados': esgotados,
                    'alertas_ativos': alertas_ativos,
                    'movimentacoes_recentes': movimentacoes_recentes
                },
                'top_consumidos': [
                    {
                        'nome': item.nome,
                        'total_consumido': float(item.total_consumido)
                    } for item in top_consumidos
                ]
            }
            
        except Exception as e:
            return None
    
    @staticmethod
    def obter_alertas_ativos(id_granja):
        """Obter alertas ativos"""
        return AlertaInsumo.query.filter(
            and_(
                AlertaInsumo.id_granja == id_granja,
                AlertaInsumo.ativo == True
            )
        ).order_by(
            AlertaInsumo.nivel_prioridade.desc(),
            AlertaInsumo.data_criacao.desc()
        ).all()
    
    @staticmethod
    def resolver_alerta(id_alerta, usuario_id):
        """Resolver alerta"""
        try:
            alerta = AlertaInsumo.query.get(id_alerta)
            if not alerta:
                return False, "Alerta não encontrado"
            
            alerta.ativo = False
            alerta.data_resolucao = datetime.utcnow()
            alerta.resolvido_por = usuario_id
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)