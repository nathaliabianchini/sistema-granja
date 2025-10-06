from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.forms.producao_forms import ProducaoForm
from app.controllers.producao_controller import ProducaoController
from app.exceptions import BusinessError

producao_web = Blueprint('producao_web', __name__, url_prefix='/producoes')

@producao_web.route('/', methods=['GET'])
def listar():
    producoes = ProducaoController.listar_todos()
    producoes = sorted(producoes, key=lambda x: x.id_producao)
    return render_template('producao/listar.html', producoes=producoes)

@producao_web.route('/novo', methods=['GET', 'POST'])
def criar():
    form = ProducaoForm()
    
    if form.validate_on_submit():
        try:
            producao = ProducaoController.criar_producao(
                lote_id=form.id_lote.data,
                data_coleta=form.data_coleta.data,
                quantidade_aves=form.quantidade_aves.data,
                quantidade_ovos=form.quantidade_ovos.data,
                qualidade_producao=form.qualidade_producao.data,
                producao_nao_aproveitada=form.producao_nao_aproveitada.data,
                responsavel=form.responsavel.data,
                observacoes=form.observacoes.data
            )
            
            flash('✅ Produção cadastrada com sucesso!', 'success')
            return redirect(url_for('producao_web.listar'))
            
        except Exception as e:
            flash(f'❌ Erro ao cadastrar produção: {str(e)}', 'danger')
    
    return render_template('producao/criar.html', form=form)

@producao_web.route('/producoes/excluir/<int:id>', methods=['POST'])
def excluir(id):
    try:
        from app.controllers.producao_controller import ProducaoController
        
        ProducaoController.excluir_producao(id)
        flash('Produção excluída com sucesso!', 'success')
        
    except ValueError as e:
        flash('Produção não encontrada.', 'danger')
    except Exception as e:
        flash(f'Erro ao excluir produção: {str(e)}', 'danger')
    
    return redirect(url_for('producao_web.listar'))

@producao_web.route('/<int:producao_id>/editar', methods=['GET', 'POST'])
def editar(producao_id: int):
    producao = ProducaoController.buscar_por_id(producao_id)
    if not producao:
        flash('Produção não encontrada.', 'danger')
        return redirect(url_for('producao_web.listar'))

    form = ProducaoForm(obj=producao)

    if request.method == 'GET':
        form.id_lote.data = producao.id_lote  
        
        if hasattr(producao.data_coleta, 'date'):
            form.data_coleta.data = producao.data_coleta.date()
        else:
            form.data_coleta.data = producao.data_coleta

    if form.validate_on_submit():
        try:
            atualizado = ProducaoController.atualizar(
                producao_id,
                id_lote=form.id_lote.data,  
                data_coleta=datetime.combine(form.data_coleta.data, datetime.min.time()),
                quantidade_aves=form.quantidade_aves.data,
                quantidade_ovos=form.quantidade_ovos.data,
                qualidade_producao=form.qualidade_producao.data,
                producao_nao_aproveitada=form.producao_nao_aproveitada.data,
                responsavel=form.responsavel.data,
                observacoes=form.observacoes.data,
            )
            if atualizado:
                flash('Produção atualizada com sucesso.', 'success')
            return redirect(url_for('producao_web.listar'))
        except Exception as e:
            flash(f'Erro ao atualizar produção: {str(e)}', 'danger')

    return render_template('producao/editar.html', form=form, producao=producao)