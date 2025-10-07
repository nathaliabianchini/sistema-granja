from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.forms.producao_forms import ProducaoForm
from app.controllers.producao_controller import ProducaoController

producao_bp = Blueprint('producao', __name__)

@producao_bp.route('/producao/registrar', methods=['GET', 'POST'])
def registrar_producao():
    form = ProducaoForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            ProducaoController.criar_producao(
                lote_id=form.id_lote.data,
                data_coleta=form.data_coleta.data,
                quantidade_aves=form.quantidade_aves.data,
                quantidade_ovos=form.quantidade_ovos.data,
                qualidade_producao=form.qualidade_producao.data,
                producao_nao_aproveitada=form.producao_nao_aproveitada.data,
                responsavel=form.responsavel.data,
                observacoes=form.observacoes.data
            )
            flash('Registro de produção realizado com sucesso!', 'success')
            return redirect(url_for('producao.registrar_producao'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('producao/registrar.html', form=form)
