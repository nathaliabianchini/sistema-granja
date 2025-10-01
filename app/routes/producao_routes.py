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
    
    # POPULAR O SELECT COM OS LOTES CADASTRADOS
    from app.models.database import Lote
    lotes = list(Lote.select())
    form.lote.choices = [(lote.id_lote, lote.numero_lote) for lote in lotes]
    
    print(f"DEBUG: Método da requisição: {request.method}")
    
    if request.method == 'POST':
        print(f"DEBUG: Dados do formulário: {dict(request.form)}")
        print(f"DEBUG: Formulário válido? {form.validate_on_submit()}")
        
        if form.errors:
            print(f"DEBUG: Erros do formulário: {form.errors}")
    
    if form.validate_on_submit():
        try:
            print("DEBUG: Tentando criar produção...")
            
            # CORRIGIR OS PARÂMETROS PARA COINCIDIR COM O CONTROLLER
            producao = ProducaoController.criar_producao(
                lote=form.lote.data,
                data_coleta=form.data_coleta.data,
                quantidade_aves=form.quantidade_aves.data,
                quantidade_ovos=form.quantidade_ovos.data,
                qualidade_producao=form.qualidade_producao.data,
                producao_nao_aproveitada=form.producao_nao_aproveitada.data,
                responsavel=form.responsavel.data,
                observacoes=form.observacoes.data
            )
            
            print(f"DEBUG: Produção criada: {producao}")
            flash('✅ Produção cadastrada com sucesso!', 'success')
            return redirect(url_for('producao_web.listar'))
            
        except Exception as e:
            print(f"DEBUG: Erro na criação: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'❌ Erro ao cadastrar produção: {str(e)}', 'danger')
    
    return render_template('producao/criar.html', form=form)


@producao_web.route('/producoes/excluir/<int:id>', methods=['POST'])
def excluir(id):
    try:
        from app.controllers.producao_controller import ProducaoController
        
        # Chamar diretamente o método de exclusão
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
    from app.models.database import Lote
    lotes = list(Lote.select())
    form.lote.choices = [(lote.id_lote, lote.numero_lote) for lote in lotes]

    if request.method == 'GET':
        # Definir o lote selecionado corretamente
        form.lote.data = producao.lote.id_lote
        
        # Corrigir a data
        if hasattr(producao.data_coleta, 'date'):
            form.data_coleta.data = producao.data_coleta.date()
        else:
            form.data_coleta.data = producao.data_coleta

    if form.validate_on_submit():
        try:
            print(f"DEBUG: Responsável do form: {form.responsavel.data}")  # ← DEBUG
            
            atualizado = ProducaoController.atualizar(
                producao_id,
                lote_id=form.lote.data,  # ← MUDANÇA AQUI: lote_id em vez de lote
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
        except Exception as e:  # ← Mudança: capturar Exception geral
            print(f"DEBUG: Erro na atualização: {str(e)}")  # ← DEBUG
            flash(f'Erro ao atualizar produção: {str(e)}', 'danger')

    return render_template('producao/editar.html', form=form, producao=producao)