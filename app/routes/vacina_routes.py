from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.forms.vacina_forms import VacinaForm 
from app.controllers.vacina_controller import VacinaController 
from app.exceptions import BusinessError

vacina_web = Blueprint('vacina_web', __name__, url_prefix='/vacinas')  

@vacina_web.route('/', methods=['GET'])
def listar():
    vacinas = VacinaController.listar_todos()  
    return render_template('vacina/listar.html', vacinas=vacinas)  

@vacina_web.route('/novo', methods=['GET', 'POST'])
def criar():
    form = VacinaForm()  
    
    if form.validate_on_submit():
        try:
            VacinaController.criar_vacina(  
                data_aplicacao=form.data_aplicacao.data,
                responsavel=form.responsavel.data,
                tipo_vacina=form.tipo_vacina.data,
                id_lote=form.id_lote.data,
                quantidade_aves=form.quantidade_aves.data,
                observacoes=form.observacoes.data
            )
            
            flash('✅ Vacinação registrada com sucesso!', 'success')
            return redirect(url_for('vacina_web.listar'))  
            
        except Exception as e:
            flash(f'❌ Erro ao registrar vacinação: {str(e)}', 'danger')
    
    return render_template('vacina/criar.html', form=form)  

@vacina_web.route('/<int:id_vacinacao>/editar', methods=['GET', 'POST'])
def editar(id_vacinacao: int):
    vacina = VacinaController.buscar_por_id(id_vacinacao)  
    if not vacina:
        flash('Vacinação não encontrada.', 'danger')
        return redirect(url_for('vacina_web.listar'))  

    form = VacinaForm(obj=vacina)  

    if form.validate_on_submit():
        try:
            VacinaController.atualizar(  
                id_vacinacao,
                data_aplicacao=form.data_aplicacao.data,
                responsavel=form.responsavel.data,
                tipo_vacina=form.tipo_vacina.data,
                id_lote=form.id_lote.data,
                quantidade_aves=form.quantidade_aves.data,
                observacoes=form.observacoes.data
            )
            flash('Vacinação atualizada com sucesso.', 'success')
            return redirect(url_for('vacina_web.listar'))  
        except Exception as e:
            flash(f'Erro ao atualizar vacinação: {str(e)}', 'danger')

    return render_template('vacina/editar.html', form=form, vacina=vacina)  

@vacina_web.route('/<int:id_vacinacao>/excluir', methods=['POST'])
def excluir(id_vacinacao: int):
    try:
        VacinaController.excluir(id_vacinacao)  
        flash('Vacinação excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir vacinação: {str(e)}', 'danger')
    
    return redirect(url_for('vacina_web.listar'))  