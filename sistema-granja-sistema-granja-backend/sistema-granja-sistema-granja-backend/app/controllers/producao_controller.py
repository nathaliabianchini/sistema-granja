from flask import Blueprint, request, jsonify
from app.producao_service import ProducaoService
from app.models import Usuarios, TipoUsuario
from datetime import datetime, date, timedelta
import csv
from io import StringIO

producao_bp = Blueprint('producao', __name__)

def verificar_permissao(usuario_id, operacao='read'):
    """Verificar permissões do usuário"""
    usuario = Usuarios.query.get(usuario_id)
    if not usuario:
        return False, "Usuário não encontrado"
    
    if operacao in ['read', 'create'] and usuario.tipo_usuario in [TipoUsuario.OPERADOR, TipoUsuario.GERENTE, TipoUsuario.ADMIN]:
        return True, None
    elif operacao in ['update', 'delete'] and usuario.tipo_usuario in [TipoUsuario.GERENTE, TipoUsuario.ADMIN]:
        return True, None
    elif operacao == 'history' and usuario.tipo_usuario in [TipoUsuario.GERENTE, TipoUsuario.ADMIN]:
        return True, None
    
    return False, "Permissão negada"

def obter_ip_cliente():
    """Obter IP do cliente"""
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)


@producao_bp.route('/registrar', methods=['POST'])
def registrar_producao():
    """Registrar nova produção diária"""
    try:
        data = request.get_json()
        usuario_id = request.headers.get('User-ID')  
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        
        pode, erro = verificar_permissao(usuario_id, 'create')
        if not pode:
            return jsonify({'error': erro}), 403
        
        
        campos_obrigatorios = ['id_setor', 'quantidade_ovos_produzidos', 'numero_aves_ativas', 'id_granja']
        for campo in campos_obrigatorios:
            if campo not in data or data[campo] is None:
                return jsonify({'error': f'{campo} é obrigatório'}), 400
        
        
        if data['quantidade_ovos_produzidos'] < 0:
            return jsonify({'error': 'Quantidade de ovos não pode ser negativa'}), 400
        
        if data['numero_aves_ativas'] <= 0:
            return jsonify({'error': 'Número de aves ativas deve ser maior que zero'}), 400
        
        if data.get('ovos_quebrados_danificados', 0) > data['quantidade_ovos_produzidos']:
            return jsonify({'error': 'Ovos quebrados não pode ser maior que a produção total'}), 400
        
        producao, erro = ProducaoService.criar_producao(data, usuario_id, obter_ip_cliente())
        
        if erro:
            return jsonify({'error': erro}), 400
        
        return jsonify({
            'message': 'Produção registrada com sucesso',
            'data': producao.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@producao_bp.route('/listar', methods=['GET'])
def listar_producoes():
    """Listar produções com filtros"""
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
            'id_setor': request.args.get('id_setor'),
            'id_lote': request.args.get('id_lote'),
            'operador_responsavel': request.args.get('operador_responsavel'),
            'qualidade_ovos': request.args.get('qualidade_ovos')
        }
        
        
        filtros = {k: v for k, v in filtros.items() if v}
        
        producoes = ProducaoService.listar_producoes(id_granja, filtros)
        
        return jsonify({
            'data': [p.to_dict() for p in producoes],
            'total': len(producoes),
            'filtros_aplicados': filtros
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@producao_bp.route('/<id_producao>', methods=['GET'])
def obter_producao(id_producao):
    """Obter produção específica"""
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
        
        producao = ProducaoService.obter_producao(id_producao, id_granja)
        
        if not producao:
            return jsonify({'error': 'Produção não encontrada'}), 404
        
        return jsonify({'data': producao.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@producao_bp.route('/<id_producao>', methods=['PUT'])
def atualizar_producao(id_producao):
    """Atualizar registro de produção"""
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
        
        motivo = data.pop('motivo_alteracao', None)
        if not motivo:
            return jsonify({'error': 'Motivo da alteração é obrigatório'}), 400
        
        producao, erro = ProducaoService.atualizar_producao(
            id_producao, data, usuario_id, obter_ip_cliente(), motivo
        )
        
        if erro:
            return jsonify({'error': erro}), 400
        
        return jsonify({
            'message': 'Produção atualizada com sucesso',
            'data': producao.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@producao_bp.route('/<id_producao>/cancelar', methods=['PUT'])
def cancelar_producao(id_producao):
    """Cancelar registro de produção"""
    try:
        data = request.get_json()
        usuario_id = request.headers.get('User-ID')
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        
        pode, erro = verificar_permissao(usuario_id, 'delete')
        if not pode:
            return jsonify({'error': erro}), 403
        
        motivo = data.get('motivo') if data else None
        if not motivo:
            return jsonify({'error': 'Motivo do cancelamento é obrigatório'}), 400
        
        sucesso, erro = ProducaoService.cancelar_producao(
            id_producao, usuario_id, motivo, obter_ip_cliente()
        )
        
        if erro:
            return jsonify({'error': erro}), 400
        
        return jsonify({'message': 'Produção cancelada com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@producao_bp.route('/<id_producao>/historico', methods=['GET'])
def obter_historico(id_producao):
    """Obter histórico de alterações"""
    try:
        usuario_id = request.headers.get('User-ID')
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        

        pode, erro = verificar_permissao(usuario_id, 'history')
        if not pode:
            return jsonify({'error': erro}), 403
        
        historico = ProducaoService.obter_historico(id_producao)
        
        return jsonify({
            'data': [h.to_dict() for h in historico],
            'total': len(historico)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@producao_bp.route('/relatorio/periodo', methods=['POST'])
def gerar_relatorio_periodo():
    """Gerar relatório de período"""
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
        
        relatorio, erro = ProducaoService.gerar_relatorio_periodo(
            data['id_granja'],
            data['data_inicio'],
            data['data_fim'],
            data['tipo_periodo'],
            data.get('id_setor'),
            data.get('id_lote'),
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

@producao_bp.route('/dashboard', methods=['GET'])
def obter_dashboard():
    """Obter dados para dashboard"""
    try:
        usuario_id = request.headers.get('User-ID')
        id_granja = request.args.get('id_granja', type=str)
        dias = request.args.get('dias', 30, type=int)
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        if not id_granja:
            return jsonify({'error': 'ID da granja é obrigatório'}), 400
        

        pode, erro = verificar_permissao(usuario_id, 'read')
        if not pode:
            return jsonify({'error': erro}), 403
        
        estatisticas = ProducaoService.obter_estatisticas_dashboard(id_granja, dias)
        
        if not estatisticas:
            return jsonify({'error': 'Erro ao obter estatísticas'}), 500
        
        return jsonify({
            'data': estatisticas,
            'periodo_analisado': f'Últimos {dias} dias'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@producao_bp.route('/graficos/dados', methods=['GET'])
def obter_dados_graficos():
    """Obter dados para gráficos"""
    try:
        usuario_id = request.headers.get('User-ID')
        id_granja = request.args.get('id_granja', type=str)
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        tipo_agrupamento = request.args.get('tipo_agrupamento', 'diario')
        
        if not usuario_id:
            return jsonify({'error': 'ID do usuário é obrigatório'}), 401
        
        if not all([id_granja, data_inicio, data_fim]):
            return jsonify({'error': 'ID da granja, data início e data fim são obrigatórios'}), 400
        

        pode, erro = verificar_permissao(usuario_id, 'read')
        if not pode:
            return jsonify({'error': erro}), 403
        
        dados = ProducaoService.obter_dados_graficos(
            id_granja, data_inicio, data_fim, tipo_agrupamento
        )
        
        return jsonify({
            'data': dados,
            'periodo': {
                'inicio': data_inicio,
                'fim': data_fim,
                'agrupamento': tipo_agrupamento
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@producao_bp.route('/export/csv', methods=['GET'])
def exportar_csv():
    """Exportar dados para CSV"""
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
            'id_setor': request.args.get('id_setor'),
            'id_lote': request.args.get('id_lote')
        }
        filtros = {k: v for k, v in filtros.items() if v}
        
        producoes = ProducaoService.listar_producoes(id_granja, filtros)
        
        output = StringIO()
        writer = csv.writer(output)
        

        writer.writerow([
            'Data Produção', 'Setor', 'Lote', 'Ovos Produzidos', 'Aves Ativas',
            'Taxa Produção (%)', 'Ovos Quebrados', 'Ovos Aproveitáveis',
            'Qualidade', 'Operador', 'Observações', 'Status'
        ])
        

        for producao in producoes:
            writer.writerow([
                producao.data_producao,
                producao.setor.descricao_setor if producao.setor else '',
                producao.id_lote or '',
                producao.quantidade_ovos_produzidos,
                producao.numero_aves_ativas,
                producao.taxa_producao,
                producao.ovos_quebrados_danificados,
                producao.ovos_aproveitaveis,
                producao.qualidade_ovos.value if producao.qualidade_ovos else '',
                producao.operador.nome if producao.operador else '',
                producao.observacoes or '',
                producao.status.value
            ])
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=producao_ovos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500