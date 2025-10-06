from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.forms.estoque_vacina_forms import EstoqueVacinaForm
from app.controllers.estoque_vacina_controller import EstoqueVacinaController
from app.exceptions import BusinessError
from datetime import date

estoque_vacina_web = Blueprint('estoque_vacina_web', __name__, url_prefix='/estoque-vacinas')

@estoque_vacina_web.route('/', methods=['GET'])
def listar():
    estoques = EstoqueVacinaController.listar_todos()
    return render_template('estoque_vacina/listar.html', 
                         estoques=estoques, 
                         today=date.today())

@estoque_vacina_web.route('/novo', methods=['GET', 'POST'])
def criar():
    form = EstoqueVacinaForm()
    
    if form.validate_on_submit():
        try:
            EstoqueVacinaController.criar_estoque_vacina(
                tipo_vacina=form.tipo_vacina.data,
                fabricante=form.fabricante.data,
                lote_vacina=form.lote_vacina.data,
                data_validade=form.data_validade.data,
                quantidade_doses=form.quantidade_doses.data,
                data_entrada=form.data_entrada.data,
                observacoes=form.observacoes.data
            )
            
            flash('✅ Estoque de vacina criado com sucesso!', 'success')
            return redirect(url_for('estoque_vacina_web.listar'))
            
        except Exception as e:
            flash(f'❌ Erro ao criar estoque: {str(e)}', 'danger')
    
    return render_template('estoque_vacina/criar.html', form=form)

@estoque_vacina_web.route('/<int:id_estoque_vacina>/editar', methods=['GET', 'POST'])
def editar(id_estoque_vacina: int):
    estoque = EstoqueVacinaController.buscar_por_id(id_estoque_vacina)
    if not estoque:
        flash('Estoque de vacina não encontrado.', 'danger')
        return redirect(url_for('estoque_vacina_web.listar'))

    form = EstoqueVacinaForm(obj=estoque)

    if form.validate_on_submit():
        try:
            EstoqueVacinaController.atualizar(
                id_estoque_vacina,
                tipo_vacina=form.tipo_vacina.data,
                fabricante=form.fabricante.data,
                lote_vacina=form.lote_vacina.data,
                data_validade=form.data_validade.data,
                quantidade_doses=form.quantidade_doses.data,
                data_entrada=form.data_entrada.data,
                observacoes=form.observacoes.data
            )
            flash('Estoque de vacina atualizado com sucesso.', 'success')
            return redirect(url_for('estoque_vacina_web.listar'))
        except Exception as e:
            flash(f'Erro ao atualizar estoque: {str(e)}', 'danger')

    return render_template('estoque_vacina/editar.html', 
                         form=form, 
                         estoque=estoque, 
                         today=date.today())

@estoque_vacina_web.route('/<int:id_estoque_vacina>/excluir', methods=['POST'])
def excluir(id_estoque_vacina: int):
    try:
        EstoqueVacinaController.excluir(id_estoque_vacina)
        flash('Estoque de vacina excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir estoque: {str(e)}', 'danger')
    
    return redirect(url_for('estoque_vacina_web.listar'))