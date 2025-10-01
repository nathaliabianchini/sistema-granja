from datetime import datetime, timedelta
from app.controllers.producao_controller import ProducaoController

def test_criar_producao():
    producao_ctrl = ProducaoController()
    
    nova_producao = producao_ctrl.criar_producao(
        lote_id=1,
        data_producao=datetime.now(),
        quantidade_aves=1000,
        quantidade_produzida=950,
        qualidade_producao="Excelente",
        producao_nao_aproveitada=50
    )
    
    assert nova_producao is not None
    assert nova_producao.quantidade_aves == 1000