from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.forms.insumo_forms import InsumoForm, MovimentacaoInsumoForm
from app.controllers.insumo_controller import InsumoController, MovimentacaoInsumoController
from app.models.database import InsumoNovo, CategoriaInsumo, TipoMovimentacao
from app.exceptions import BusinessError
from datetime import date, datetime, timedelta
from decimal import Decimal
from app.controllers.export_controller import RelatoriosInsumosController

insumo_web = Blueprint('insumo_web', __name__, url_prefix='/insumos')

# ===== ROTAS DE INSUMOS =====
@insumo_web.route('/', methods=['GET'])
def listar():
    """Lista insumos com filtros"""
    categoria = request.args.get('categoria')
    abaixo_minimo = request.args.get('abaixo_minimo') == 'true'
    vencimento_dias = request.args.get('vencimento_dias', type=int)
    ativo = request.args.get('ativo', 'true') == 'true'
    
    insumos = InsumoController.listar_todos(
        categoria=categoria,
        abaixo_minimo=abaixo_minimo,
        vencimento_dias=vencimento_dias,
        ativo=ativo
    )
    
    # Estatísticas rápidas
    total_insumos = len(insumos)
    insumos_abaixo_minimo = len([i for i in insumos if i.quantidade_atual < i.quantidade_minima])
    insumos_vencendo = len([i for i in insumos if i.data_validade and i.data_validade <= date.today() + timedelta(days=30)])
    
    return render_template('insumo/listar.html', 
                         insumos=insumos,
                         categorias=CategoriaInsumo,
                         today=date.today(),
                         total_insumos=total_insumos,
                         insumos_abaixo_minimo=insumos_abaixo_minimo,
                         insumos_vencendo=insumos_vencendo,
                         filtros={
                             'categoria': categoria,
                             'abaixo_minimo': abaixo_minimo,
                             'vencimento_dias': vencimento_dias,
                             'ativo': ativo
                         })

@insumo_web.route('/criar', methods=['GET', 'POST'])
def criar():
    """Criar novo insumo"""
    form = InsumoForm()
    
    if form.validate_on_submit():
        try:
            InsumoController.criar_insumo(
                nome=form.nome.data,
                categoria=form.categoria.data,
                unidade=form.unidade.data,
                quantidade_inicial=form.quantidade_inicial.data,
                quantidade_minima=form.quantidade_minima.data,
                data_validade=form.data_validade.data,
                observacoes=form.observacoes.data,
                usuario_id=1  # TODO: Pegar do session
            )
            
            flash('✅ Insumo criado com sucesso!', 'success')
            return redirect(url_for('insumo_web.listar'))
            
        except Exception as e:
            flash(f'❌ Erro ao criar insumo: {str(e)}', 'danger')
    
    return render_template('insumo/criar.html', form=form)

@insumo_web.route('/<int:id_insumo>/editar', methods=['GET', 'POST'])
def editar(id_insumo: int):
    """Editar insumo"""
    insumo = InsumoController.buscar_por_id(id_insumo)
    if not insumo:
        flash('Insumo não encontrado.', 'danger')
        return redirect(url_for('insumo_web.listar'))

    form = InsumoForm(obj=insumo)
    # Não mostrar quantidade inicial na edição
    del form.quantidade_inicial

    if form.validate_on_submit():
        try:
            InsumoController.atualizar_insumo(
                id_insumo,
                nome=form.nome.data,
                categoria=form.categoria.data,
                unidade=form.unidade.data,
                quantidade_minima=form.quantidade_minima.data,
                data_validade=form.data_validade.data,
                observacoes=form.observacoes.data
            )
            flash('✅ Insumo atualizado com sucesso.', 'success')
            return redirect(url_for('insumo_web.listar'))
        except Exception as e:
            flash(f'❌ Erro ao atualizar insumo: {str(e)}', 'danger')

    return render_template('insumo/editar.html', 
                         form=form, 
                         insumo=insumo, 
                         today=date.today())

@insumo_web.route('/<int:id_insumo>/desativar', methods=['POST'])
def desativar(id_insumo: int):
    """Desativar insumo (soft delete)"""
    try:
        InsumoController.desativar_insumo(id_insumo)
        flash('✅ Insumo desativado com sucesso!', 'success')
    except Exception as e:
        flash(f'❌ Erro ao desativar insumo: {str(e)}', 'danger')
    
    return redirect(url_for('insumo_web.listar'))

@insumo_web.route('/<int:id_insumo>/ativar', methods=['POST'])
def ativar(id_insumo: int):
    """Ativar insumo"""
    try:
        InsumoController.ativar_insumo(id_insumo)
        flash('✅ Insumo ativado com sucesso!', 'success')
    except Exception as e:
        flash(f'❌ Erro ao ativar insumo: {str(e)}', 'danger')
    
    return redirect(url_for('insumo_web.listar'))

# ===== ROTAS DE MOVIMENTAÇÕES =====
@insumo_web.route('/listar_movimentacoes', methods=['GET'])
@insumo_web.route('/movimentacoes', methods=['GET'])
def listar_movimentacoes():
    """Lista movimentações com filtros"""
    insumo_id = request.args.get('insumo_id', type=int)
    tipo = request.args.get('tipo')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Converter datas
    if data_inicio:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    if data_fim:
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    movimentacoes = MovimentacaoInsumoController.listar_movimentacoes(
        insumo_id=insumo_id,
        tipo=tipo,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    # Para o select de insumos
    insumos = InsumoController.listar_todos(ativo=True)
    
    return render_template('insumo/movimentacoes.html',
                         movimentacoes=movimentacoes,
                         insumos=insumos,
                         tipos=TipoMovimentacao,
                         filtros={
                             'insumo_id': insumo_id,
                             'tipo': tipo,
                             'data_inicio': data_inicio,
                             'data_fim': data_fim
                         })

@insumo_web.route('/nova_movimentacao', methods=['GET', 'POST'])
@insumo_web.route('/movimentacoes/nova', methods=['GET', 'POST'])
def nova_movimentacao():
    """Nova movimentação"""
    form = MovimentacaoInsumoForm()
    
    # Carregar insumos ativos para o select
    insumos_ativos = InsumoController.listar_todos(ativo=True)
    form.insumo_id.choices = [(i.id_insumo, f"{i.nome} (Atual: {i.quantidade_atual} {i.unidade})") 
                              for i in insumos_ativos]
    
    if form.validate_on_submit():
        try:
            MovimentacaoInsumoController.criar_movimentacao(
                insumo_id=form.insumo_id.data,
                tipo=form.tipo.data,
                quantidade=form.quantidade.data,
                data_movimentacao=form.data_movimentacao.data,
                observacoes=form.observacoes.data,
                usuario_id=1 
            )
            
            flash('✅ Movimentação registrada com sucesso!', 'success')
            return redirect(url_for('insumo_web.listar_movimentacoes'))
            
        except Exception as e:
            flash(f'❌ Erro ao registrar movimentação: {str(e)}', 'danger')
    
    return render_template('insumo/nova_movimentacao.html', form=form)

# ===== ROTAS DE RELATÓRIOS =====
@insumo_web.route('/relatorios', methods=['GET'])
def relatorios():
    """Dashboard de relatórios"""
    return render_template('insumo/relatorios.html')

@insumo_web.route('/relatorios/abaixo-minimo', methods=['GET'])
def relatorio_abaixo_minimo():
    """Relatório de insumos abaixo do mínimo"""
    insumos = InsumoController.listar_todos(abaixo_minimo=True, ativo=True)
    
    return render_template('insumo/relatorio_abaixo_minimo.html',
                         insumos=insumos,
                         today=date.today())

@insumo_web.route('/relatorios/vencimentos', methods=['GET'])
def relatorio_vencimentos():
    """Relatório de vencimentos próximos"""
    dias = request.args.get('dias', 30, type=int)
    insumos = InsumoController.listar_todos(vencimento_dias=dias, ativo=True)
    
    return render_template('insumo/relatorio_vencimentos.html',
                         insumos=insumos,
                         dias=dias,
                         today=date.today())

@insumo_web.route('/relatorios/consumo', methods=['GET'])
def relatorio_consumo():
    """Relatório de consumo por período"""
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    categoria = request.args.get('categoria')
    
    # Valores padrão (último mês)
    if not data_fim:
        data_fim = date.today()
    else:
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
    
    if not data_inicio:
        data_inicio = data_fim - timedelta(days=30)
    else:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
    
    # Buscar movimentações de saída no período
    movimentacoes = MovimentacaoInsumoController.listar_movimentacoes(
        tipo='Saída - Uso',
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    
    # Agrupar por insumo
    consumo_por_insumo = {}
    for mov in movimentacoes:
        if categoria and mov.insumo.categoria != categoria:
            continue
            
        nome_insumo = mov.insumo.nome
        if nome_insumo not in consumo_por_insumo:
            consumo_por_insumo[nome_insumo] = {
                'insumo': mov.insumo,
                'total_consumido': 0,
                'movimentacoes': []
            }
        
        consumo_por_insumo[nome_insumo]['total_consumido'] += mov.quantidade
        consumo_por_insumo[nome_insumo]['movimentacoes'].append(mov)
    
    consumo_ordenado = sorted(
        consumo_por_insumo.items(), 
        key=lambda x: x[1]['total_consumido'], 
        reverse=True
    )
    
    top_5_consumo = consumo_ordenado[:5]
    
    total_itens_consumidos = len(consumo_por_insumo)
    total_quantidade_consumida = sum(dados['total_consumido'] for dados in consumo_por_insumo.values())
    
    return render_template('insumo/relatorio_consumo.html',
                         consumo_por_insumo=consumo_por_insumo,
                         consumo_ordenado=consumo_ordenado,
                         top_5_consumo=top_5_consumo,
                         total_itens_consumidos=total_itens_consumidos,
                         total_quantidade_consumida=total_quantidade_consumida,
                         data_inicio=data_inicio,
                         data_fim=data_fim,
                         categoria=categoria,
                         categorias=CategoriaInsumo)

# ===== ROTAS DE EXPORTAÇÃO =====
@insumo_web.route('/relatorios/consumo/export/<formato>', methods=['GET'])
def export_consumo(formato):
    """Exporta relatório de consumo"""
    try:
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        categoria = request.args.get('categoria')
        
        # Valores padrão (último mês)
        if not data_fim:
            data_fim = date.today()
        else:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=30)
        else:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        
        # Validar formato
        if formato not in ['csv', 'excel', 'pdf']:
            flash('Formato de exportação inválido', 'danger')
            return redirect(url_for('insumo_web.relatorio_consumo'))
        
        # Exportar
        return RelatoriosInsumosController.exportar(
            tipo_relatorio='consumo',
            formato=formato,
            data_inicio=data_inicio,
            data_fim=data_fim,
            categoria=categoria
        )
        
    except Exception as e:
        flash(f'Erro ao exportar relatório: {str(e)}', 'danger')
        return redirect(url_for('insumo_web.relatorio_consumo'))

@insumo_web.route('/relatorios/abaixo-minimo/export/<formato>', methods=['GET'])
def export_abaixo_minimo(formato):
    """Exporta relatório de insumos abaixo do mínimo"""
    try:
        # Validar formato
        if formato not in ['csv', 'excel', 'pdf']:
            flash('Formato de exportação inválido', 'danger')
            return redirect(url_for('insumo_web.relatorio_abaixo_minimo'))
        
        # Exportar
        return RelatoriosInsumosController.exportar(
            tipo_relatorio='abaixo_minimo',
            formato=formato
        )
        
    except Exception as e:
        flash(f'Erro ao exportar relatório: {str(e)}', 'danger')
        return redirect(url_for('insumo_web.relatorio_abaixo_minimo'))

@insumo_web.route('/relatorios/vencimentos/export/<formato>', methods=['GET'])
def export_vencimentos(formato):
    """Exporta relatório de vencimentos"""
    try:
        dias = request.args.get('dias', 30, type=int)
        
        # Validar formato
        if formato not in ['csv', 'excel', 'pdf']:
            flash('Formato de exportação inválido', 'danger')
            return redirect(url_for('insumo_web.relatorio_vencimentos'))
        
        # Exportar
        return RelatoriosInsumosController.exportar(
            tipo_relatorio='vencimentos',
            formato=formato,
            dias=dias
        )
        
    except Exception as e:
        flash(f'Erro ao exportar relatório: {str(e)}', 'danger')
        return redirect(url_for('insumo_web.relatorio_vencimentos'))

@insumo_web.route('/relatorios/cobertura/export/<formato>', methods=['GET'])
def export_cobertura(formato):
    """Exporta relatório de cobertura de estoque"""
    try:
        # Validar formato
        if formato not in ['csv', 'excel', 'pdf']:
            flash('Formato de exportação inválido', 'danger')
            return redirect(url_for('insumo_web.relatorios'))
        
        # Exportar
        return RelatoriosInsumosController.exportar(
            tipo_relatorio='cobertura',
            formato=formato
        )
        
    except Exception as e:
        flash(f'Erro ao exportar relatório: {str(e)}', 'danger')
        return redirect(url_for('insumo_web.relatorios'))

# ===== ROTA PARA RELATÓRIO DE COBERTURA =====
@insumo_web.route('/relatorios/cobertura', methods=['GET'])
def relatorio_cobertura():
    """Relatório de cobertura de estoque"""
    try:
        dados_cobertura = RelatoriosInsumosController.cobertura()
        
        # Estatísticas
        total_insumos = len(dados_cobertura)
        criticos = len([item for item in dados_cobertura if item['status'] == 'crítico'])
        atencao = len([item for item in dados_cobertura if item['status'] == 'atenção'])
        ok = len([item for item in dados_cobertura if item['status'] == 'ok'])
        
        return render_template('insumo/relatorio_cobertura.html',
                             dados_cobertura=dados_cobertura,
                             total_insumos=total_insumos,
                             criticos=criticos,
                             atencao=atencao,
                             ok=ok,
                             today=date.today())
                             
    except Exception as e:
        flash(f'Erro ao gerar relatório: {str(e)}', 'danger')
        return redirect(url_for('insumo_web.relatorios'))


# ===== API ENDPOINTS =====
@insumo_web.route('/api/estoque/<int:id_insumo>', methods=['GET'])
def api_estoque_insumo(id_insumo: int):
    """API: Consultar estoque atual de um insumo"""
    insumo = InsumoController.buscar_por_id(id_insumo)
    if not insumo:
        return jsonify({'error': 'Insumo não encontrado'}), 404
    
    return jsonify({
        'id_insumo': insumo.id_insumo,
        'nome': insumo.nome,
        'quantidade_atual': float(insumo.quantidade_atual),
        'quantidade_minima': float(insumo.quantidade_minima),
        'unidade': insumo.unidade,
        'categoria': insumo.categoria,
        'abaixo_minimo': insumo.quantidade_atual < insumo.quantidade_minima
    })