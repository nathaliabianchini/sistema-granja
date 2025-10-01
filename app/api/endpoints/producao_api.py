from flask import Blueprint, jsonify
from datetime import datetime, timedelta
from app.controllers.producao_controller import ProducaoController

producao_api = Blueprint('producao_api', __name__, url_prefix='/api/producao')

@producao_api.route('/api/producao/teste', methods=['GET'])
def teste_producao():
    producao_ctrl = ProducaoController()
    
    nova_producao = producao_ctrl.criar_producao(                   # Criar produção
        lote_id=1,
        data_producao=datetime.now(),
        quantidade_aves=1000,
        quantidade_produzida=950,
        qualidade_producao="Excelente",
        producao_nao_aproveitada=50
    )
    
    stats = producao_ctrl.calcular_estatisticas_periodo(            # Buscar estatísticas
        data_inicio=datetime.now() - timedelta(days=30),
        data_fim=datetime.now()
    )
    
    return jsonify({
        'producao_id': nova_producao.id_producao,
        'estatisticas': stats
    })