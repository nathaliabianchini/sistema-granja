from flask import Blueprint, request, jsonify
from insumo_service import InsumoService
from models import Usuarios, TipoUsuario, TipoInsumo, UnidadeMedida, TipoMovimentacao
from datetime import datetime, date, timedelta
import csv
from io import StringIO

insumo_bp = Blueprint('insumo', __name__)

def verificar_permissao(usuario_id, operacao='read'):
    """Verificar permissões do usuário"""
    usuario = Usuarios.query.get(usuario_id)
    if not usuario:
        return False, "Usuário não encontrado"
    
    if operacao in ['read'] and usuario.tipo_usuario in [TipoUsuario.OPERADOR, TipoUsuario.GERENTE, TipoUsuario.ADMIN]:
        return True, None
    elif operacao in ['create', 'update', 'movimentacao'] and usuario.tipo_usuario in [TipoUsuario.GERENTE, TipoUsuario.ADMIN]:
        return True, None
    elif operacao in ['delete'] and usuario.tipo_usuario in [TipoUsuario.ADMIN]:
        return True, None
    
    return False, "Permissão negada"

@insumo_bp.route('/cadastrar', methods=['POST'])
def cadastrar_insumo():
    """Cadastrar novo insumo"""
    try:
        data = request.get_json()
        usuario_id = request.headers.get('User-ID')
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        pode, erro = verificar_permissao(usuario_id, 'create')
        if not pode:
            return jsonify({'error': erro}), 403
        
        campos_obrigatorios = ['nome', 'tipo_insumo', 'id_granja']
        for campo in campos_obrigatorios:
            if campo not in data or not data[campo]:
                return jsonify({'error': f'{campo} é obrigatório'}), 400
        
        try:
            TipoInsumo(data['tipo_insumo'])
            if data.get('unidade_medida'):
                UnidadeMedida(data['unidade_medida'])
        except ValueError as e:
            return jsonify({'error': f'Valor inválido: {str(e)}'}), 400
        
        insumo, erro = InsumoService.criar_insumo(data, usuario_id)
        
        if erro:
            return jsonify({'error': erro}), 400
        
        return jsonify({
            'message': 'Insumo cadastrado com sucesso',
            'data': insumo.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/listar', methods=['GET'])
def listar_insumos():
    """Listar insumos com filtros"""
    try:
        usuario_id = request.headers.get('User-ID')
        id_granja = request.args.get('id_granja', type=str)
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        if not id_granja:
            return jsonify({'error': 'ID da granja é obrigatório'}), 400
        
        pode, erro = verificar_permissao(usuario_id, 'read')
        if not pode:
            return jsonify({'error': erro}), 403
        
        filtros = {
            'status': request.args.get('status'),
            'tipo_insumo': request.args.get('tipo_insumo'),
            'busca': request.args.get('busca'),
            'estoque_baixo': request.args.get('estoque_baixo'),
            'vencimento_proximo': request.args.get('vencimento_proximo'),
            'fornecedor': request.args.get('fornecedor'),
            'ordem': request.args.get('ordem')
        }
        
        filtros = {k: v for k, v in filtros.items() if v}
        
        insumos = InsumoService.listar_insumos(id_granja, filtros)
        
        return jsonify({
            'data': [i.to_dict() for i in insumos],
            'total': len(insumos),
            'filtros_aplicados': filtros
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/<id_insumo>', methods=['GET'])
def obter_insumo(id_insumo):
    """Obter insumo específico"""
    try:
        usuario_id = request.headers.get('User-ID')
        id_granja = request.args.get('id_granja', type=str)
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        if not id_granja:
            return jsonify({'error': 'ID da granja é obrigatório'}), 400
        
        pode, erro = verificar_permissao(usuario_id, 'read')
        if not pode:
            return jsonify({'error': erro}), 403
        
        insumo = InsumoService.obter_insumo(id_insumo, id_granja)
        
        if not insumo:
            return jsonify({'error': 'Insumo não encontrado'}), 404
        
        return jsonify({'data': insumo.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/<id_insumo>', methods=['PUT'])
def atualizar_insumo(id_insumo):
    """Atualizar dados do insumo"""
    try:
        data = request.get_json()
        usuario_id = request.headers.get('User-ID')
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        pode, erro = verificar_permissao(usuario_id, 'update')
        if not pode:
            return jsonify({'error': erro}), 403
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        insumo, erro = InsumoService.atualizar_insumo(id_insumo, data, usuario_id)
        
        if erro:
            return jsonify({'error': erro}), 400
        
        return jsonify({
            'message': 'Insumo atualizado com sucesso',
            'data': insumo.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/<id_insumo>/entrada', methods=['POST'])
def registrar_entrada(id_insumo):
    """Registrar entrada de insumo"""
    try:
        data = request.get_json()
        usuario_id = request.headers.get('User-ID')
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        pode, erro = verificar_permissao(usuario_id, 'movimentacao')
        if not pode:
            return jsonify({'error': erro}), 403
        
        if not data.get('quantidade') or float(data['quantidade']) <= 0:
            return jsonify({'error': 'Quantidade deve ser maior que zero'}), 400
        
        movimentacao, erro = InsumoService.registrar_entrada(id_insumo, data, usuario_id)
        
        if erro:
            return jsonify({'error': erro}), 400
        
        return jsonify({
            'message': 'Entrada registrada com sucesso',
            'data': movimentacao.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/<id_insumo>/saida', methods=['POST'])
def registrar_saida(id_insumo):
    """Registrar saída de insumo"""
    try:
        data = request.get_json()
        usuario_id = request.headers.get('User-ID')
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        pode, erro = verificar_permissao(usuario_id, 'movimentacao')
        if not pode:
            return jsonify({'error': erro}), 403
        
        if not data.get('quantidade') or float(data['quantidade']) <= 0:
            return jsonify({'error': 'Quantidade deve ser maior que zero'}), 400
        
        if not data.get('motivo'):
            return jsonify({'error': 'Motivo da saída é obrigatório'}), 400
        
        movimentacao, erro = InsumoService.registrar_saida(id_insumo, data, usuario_id)
        
        if erro:
            return jsonify({'error': erro}), 400
        
        return jsonify({
            'message': 'Saída registrada com sucesso',
            'data': movimentacao.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/movimentacoes', methods=['GET'])
def listar_movimentacoes():
    """Listar movimentações com filtros"""
    try:
        usuario_id = request.headers.get('User-ID')
        id_granja = request.args.get('id_granja', type=str)
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        if not id_granja:
            return jsonify({'error': 'ID da granja é obrigatório'}), 400
        
        pode, erro = verificar_permissao(usuario_id, 'read')
        if not pode:
            return jsonify({'error': erro}), 403
        
        filtros = {
            'tipo_movimentacao': request.args.get('tipo_movimentacao'),
            'data_inicio': request.args.get('data_inicio'),
            'data_fim': request.args.get('data_fim'),
            'fornecedor': request.args.get('fornecedor'),
            'responsavel': request.args.get('responsavel')
        }
        
        filtros = {k: v for k, v in filtros.items() if v}
        
        id_insumo = request.args.get('id_insumo')
        movimentacoes = InsumoService.obter_movimentacoes(id_insumo, id_granja, filtros)
        
        return jsonify({
            'data': [m.to_dict() for m in movimentacoes],
            'total': len(movimentacoes),
            'filtros_aplicados': filtros
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/<id_insumo>/movimentacoes', methods=['GET'])
def obter_historico_insumo(id_insumo):
    """Obter histórico de movimentações de um insumo específico"""
    try:
        usuario_id = request.headers.get('User-ID')
        id_granja = request.args.get('id_granja', type=str)
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        if not id_granja:
            return jsonify({'error': 'ID da granja é obrigatório'}), 400
        
        pode, erro = verificar_permissao(usuario_id, 'read')
        if not pode:
            return jsonify({'error': erro}), 403
        
        insumo = InsumoService.obter_insumo(id_insumo, id_granja)
        if not insumo:
            return jsonify({'error': 'Insumo não encontrado'}), 404
        
        movimentacoes = InsumoService.obter_movimentacoes(id_insumo, id_granja)
        
        return jsonify({
            'insumo': insumo.to_dict(),
            'movimentacoes': [m.to_dict() for m in movimentacoes],
            'total_movimentacoes': len(movimentacoes)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/relatorio/consumo', methods=['POST'])
def gerar_relatorio_consumo():
    """Gerar relatório de consumo de insumos"""
    try:
        data = request.get_json()
        usuario_id = request.headers.get('User-ID')
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        pode, erro = verificar_permissao(usuario_id, 'read')
        if not pode:
            return jsonify({'error': erro}), 403
        
        campos_obrigatorios = ['id_granja', 'data_inicio', 'data_fim', 'tipo_periodo']
        for campo in campos_obrigatorios:
            if campo not in data:
                return jsonify({'error': f'{campo} é obrigatório'}), 400
        
        relatorio, erro = InsumoService.gerar_relatorio_consumo(
            data['id_granja'],
            data['data_inicio'],
            data['data_fim'],
            data['tipo_periodo'],
            data.get('id_insumo'),
            data.get('tipo_insumo_filtro'),
            usuario_id
        )
        
        if erro:
            return jsonify({'error': erro}), 400
        
        return jsonify({
            'message': 'Relatório gerado com sucesso',
            'data': relatorio.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/dashboard', methods=['GET'])
def obter_dashboard():
    """Obter dados para dashboard de insumos"""
    try:
        usuario_id = request.headers.get('User-ID')
        id_granja = request.args.get('id_granja', type=str)
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        if not id_granja:
            return jsonify({'error': 'ID da granja é obrigatório'}), 400
        
        pode, erro = verificar_permissao(usuario_id, 'read')
        if not pode:
            return jsonify({'error': erro}), 403
        
        dashboard = InsumoService.obter_dashboard_insumos(id_granja)
        
        if not dashboard:
            return jsonify({'error': 'Erro ao obter dados do dashboard'}), 500
        
        return jsonify({'data': dashboard}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/alertas', methods=['GET'])
def obter_alertas():
    """Obter alertas ativos de insumos"""
    try:
        usuario_id = request.headers.get('User-ID')
        id_granja = request.args.get('id_granja', type=str)
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        if not id_granja:
            return jsonify({'error': 'ID da granja é obrigatório'}), 400
        
        pode, erro = verificar_permissao(usuario_id, 'read')
        if not pode:
            return jsonify({'error': erro}), 403
        
        alertas = InsumoService.obter_alertas_ativos(id_granja)
        
        return jsonify({
            'data': [a.to_dict() for a in alertas],
            'total': len(alertas)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/alertas/<id_alerta>/resolver', methods=['PUT'])
def resolver_alerta(id_alerta):
    """Resolver alerta"""
    try:
        usuario_id = request.headers.get('User-ID')
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        pode, erro = verificar_permissao(usuario_id, 'update')
        if not pode:
            return jsonify({'error': erro}), 403
        
        sucesso, erro = InsumoService.resolver_alerta(id_alerta, usuario_id)
        
        if erro:
            return jsonify({'error': erro}), 400
        
        return jsonify({'message': 'Alerta resolvido com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/export/csv', methods=['GET'])
def exportar_insumos_csv():
    """Exportar insumos para CSV"""
    try:
        usuario_id = request.headers.get('User-ID')
        id_granja = request.args.get('id_granja', type=str)
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        if not id_granja:
            return jsonify({'error': 'ID da granja é obrigatório'}), 400

        pode, erro = verificar_permissao(usuario_id, 'read')
        if not pode:
            return jsonify({'error': erro}), 403

        filtros = {
            'status': request.args.get('status'),
            'tipo_insumo': request.args.get('tipo_insumo'),
            'estoque_baixo': request.args.get('estoque_baixo')
        }
        filtros = {k: v for k, v in filtros.items() if v}
        
        insumos = InsumoService.listar_insumos(id_granja, filtros)
        
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Código Interno', 'Nome', 'Tipo', 'Unidade', 'Quantidade Atual',
            'Quantidade Mínima', 'Quantidade Máxima', 'Fabricante', 'Fornecedor',
            'Data Validade', 'Local Armazenamento', 'Status', 'Preço Última Compra',
            'Data Última Compra', 'Estoque Baixo', 'Dias Para Vencer'
        ])

        for insumo in insumos:
            writer.writerow([
                insumo.codigo_interno,
                insumo.nome,
                insumo.tipo_insumo.value if insumo.tipo_insumo else '',
                insumo.unidade_medida.value if insumo.unidade_medida else '',
                float(insumo.quantidade_atual) if insumo.quantidade_atual else 0,
                float(insumo.quantidade_minima) if insumo.quantidade_minima else 0,
                float(insumo.quantidade_maxima) if insumo.quantidade_maxima else '',
                insumo.fabricante or '',
                insumo.fornecedor_principal or '',
                insumo.data_validade.strftime('%d/%m/%Y') if insumo.data_validade else '',
                insumo.local_armazenamento or '',
                insumo.status.value if insumo.status else '',
                float(insumo.preco_ultima_compra) if insumo.preco_ultima_compra else '',
                insumo.data_ultima_compra.strftime('%d/%m/%Y') if insumo.data_ultima_compra else '',
                'Sim' if insumo.estoque_baixo else 'Não',
                insumo.dias_para_vencer if insumo.dias_para_vencer is not None else ''
            ])
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=insumos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/movimentacoes/export/csv', methods=['GET'])
def exportar_movimentacoes_csv():
    """Exportar movimentações para CSV"""
    try:
        usuario_id = request.headers.get('User-ID')
        id_granja = request.args.get('id_granja', type=str)
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        if not id_granja:
            return jsonify({'error': 'ID da granja é obrigatório'}), 400

        pode, erro = verificar_permissao(usuario_id, 'read')
        if not pode:
            return jsonify({'error': erro}), 403

        filtros = {
            'data_inicio': request.args.get('data_inicio'),
            'data_fim': request.args.get('data_fim'),
            'tipo_movimentacao': request.args.get('tipo_movimentacao')
        }
        filtros = {k: v for k, v in filtros.items() if v}
        
        movimentacoes = InsumoService.obter_movimentacoes(None, id_granja, filtros)
        
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Data/Hora', 'Insumo', 'Tipo Movimentação', 'Quantidade',
            'Unidade', 'Estoque Anterior', 'Estoque Posterior', 'Fornecedor',
            'Número Documento', 'Valor Unitário', 'Valor Total', 'Motivo',
            'Responsável', 'Observações'
        ])

        for mov in movimentacoes:
            writer.writerow([
                mov.data_movimentacao.strftime('%d/%m/%Y %H:%M:%S'),
                mov.insumo.nome if mov.insumo else '',
                mov.tipo_movimentacao.value if mov.tipo_movimentacao else '',
                float(mov.quantidade) if mov.quantidade else 0,
                mov.unidade_medida or '',
                float(mov.quantidade_anterior) if mov.quantidade_anterior else 0,
                float(mov.quantidade_posterior) if mov.quantidade_posterior else 0,
                mov.fornecedor or '',
                mov.numero_documento or '',
                float(mov.valor_unitario) if mov.valor_unitario else '',
                float(mov.valor_total) if mov.valor_total else '',
                mov.motivo or '',
                mov.nome_responsavel or '',
                mov.observacoes or ''
            ])
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=movimentacoes_insumos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/tipos', methods=['GET'])
def obter_tipos_insumo():
    """Obter lista de tipos de insumo disponíveis"""
    try:
        tipos = [{'value': tipo.value, 'label': tipo.value} for tipo in TipoInsumo]
        return jsonify({'data': tipos}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/unidades', methods=['GET'])
def obter_unidades_medida():
    """Obter lista de unidades de medida disponíveis"""
    try:
        unidades = [{'value': unidade.value, 'label': unidade.value} for unidade in UnidadeMedida]
        return jsonify({'data': unidades}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/tipos-movimentacao', methods=['GET'])
def obter_tipos_movimentacao():
    """Obter lista de tipos de movimentação disponíveis"""
    try:
        tipos = [{'value': tipo.value, 'label': tipo.value} for tipo in TipoMovimentacao]
        return jsonify({'data': tipos}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/<id_insumo>/ajustar-estoque', methods=['POST'])
def ajustar_estoque(id_insumo):
    """Ajustar estoque por inventário"""
    try:
        data = request.get_json()
        usuario_id = request.headers.get('User-ID')
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401

        pode, erro = verificar_permissao(usuario_id, 'update')
        if not pode:
            return jsonify({'error': erro}), 403

        if 'quantidade_real' not in data:
            return jsonify({'error': 'Quantidade real é obrigatória'}), 400
        
        if not data.get('motivo_ajuste'):
            return jsonify({'error': 'Motivo do ajuste é obrigatório'}), 400

        insumo = InsumoService.obter_insumo(id_insumo, data.get('id_granja'))
        if not insumo:
            return jsonify({'error': 'Insumo não encontrado'}), 404
        
        quantidade_atual = float(insumo.quantidade_atual)
        quantidade_real = float(data['quantidade_real'])
        diferenca = quantidade_real - quantidade_atual
        
        if diferenca == 0:
            return jsonify({'message': 'Não há diferença no estoque, ajuste não necessário'}), 200

        dados_movimentacao = {
            'quantidade': abs(diferenca),
            'tipo_movimentacao': 'AJUSTE_INVENTARIO',
            'motivo': data['motivo_ajuste'],
            'observacoes': f"Inventário: Estava {quantidade_atual}, contado {quantidade_real}"
        }
        
        if diferenca > 0:
            movimentacao, erro = InsumoService.registrar_entrada(id_insumo, dados_movimentacao, usuario_id)
        else:
            movimentacao, erro = InsumoService.registrar_saida(id_insumo, dados_movimentacao, usuario_id)
        
        if erro:
            return jsonify({'error': erro}), 400
        
        return jsonify({
            'message': 'Estoque ajustado com sucesso',
            'diferenca': diferenca,
            'data': movimentacao.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insumo_bp.route('/inventario/pendentes', methods=['GET'])
def obter_insumos_inventario():
    """Obter insumos que precisam de inventário (estoque baixo ou zerado)"""
    try:
        usuario_id = request.headers.get('User-ID')
        id_granja = request.args.get('id_granja', type=str)
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        if not id_granja:
            return jsonify({'error': 'ID da granja é obrigatório'}), 400
        
        pode, erro = verificar_permissao(usuario_id, 'read')
        if not pode:
            return jsonify({'error': erro}), 403
        
        filtros = {'estoque_baixo': 'true'}
        insumos_baixo = InsumoService.listar_insumos(id_granja, filtros)
        
        filtros_zerado = {'busca': ''} 
        todos_insumos = InsumoService.listar_insumos(id_granja, filtros_zerado)
        insumos_zerados = [i for i in todos_insumos if i.quantidade_atual <= 0]
        
        return jsonify({
            'estoque_baixo': [i.to_dict() for i in insumos_baixo],
            'estoque_zerado': [i.to_dict() for i in insumos_zerados],
            'total_pendentes': len(set([i.id_insumo for i in insumos_baixo + insumos_zerados]))
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500